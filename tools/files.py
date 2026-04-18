from tools.logger import message

from tqdm import tqdm
from os import path
import threading

import requests, urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Internet:
    _session = None
    _lock = threading.Lock()
    timeout = 5

    @staticmethod
    def is_valid_git_content(content: bytes, path_hint: str = "") -> bool:
        if not content or len(content) == 0:
            return False
            
        # Detect HTML - This is the most common "False 200" indicator
        sample = content[:1024].lower()
        if b"<!doctype html" in sample or b"<html" in sample or b"<body" in sample or b"<head" in sample:
            # Special case: it might be a directory listing
            if b"index of /" in sample:
                return "DIRECTORY_LISTING"
            return False

        # Specific format validations (Inspired by DotGit)
        p_hint = path_hint.lower()
        
        if "config" in p_hint:
            # Git config usually has [core], SVN has [auth], etc.
            return any(marker in content.lower() for marker in [b"[core]", b"[repository]", b"[auth]", b"[svn"])

        if "index" in p_hint and not any(ext in p_hint for ext in [".ia.cali.gov.co", ".index"]):
            # Git index always starts with "DIRC"
            return content.startswith(b"DIRC") if len(content) >= 4 else False
                
        if "objects/" in p_hint or ".svn/" in p_hint or ".hg/" in p_hint:
            # Common markers for binary repo files (e.g. zlib 0x78)
            if len(content) > 0 and content[0] == 0x78: return True
            # For SVN/Hg just allow if not HTML
            return True

        if ".env" in p_hint or ".ds_store" in p_hint:
            return True
                
        return True # Default allow for anything else not caught as HTML
                
        if "objects/" in p_hint:
            # Git objects are zlib compressed. First byte is 0x78
            return content[0] == 0x78 if len(content) > 0 else False

        if "wc.db" in p_hint:
            # SVN always starts with SQLite
            return content.startswith(b"SQLite format 3")
            
        if "00manifest.i" in p_hint:
            # Mercurial (Hg) manifest headers
            hg_headers = [b"\x00\x00\x00\x01", b"\x00\x01\x00\x01", b"\x00\x02\x00\x01", b"\x00\x03\x00\x01"]
            return any(content.startswith(h) for h in hg_headers)

        if ".ds_store" in p_hint:
            # DS_Store starts with Bud1
            return b"Bud1" in content[:20]
                
        return True

    @staticmethod
    def scrape_index(content: bytes) -> list:
        import re
        html = content.decode("utf-8", errors="ignore")
        # Regular expression to find links: <a href="XXXX">
        # Avoid parent directory, query strings, and absolute links
        links = re.findall(r'href=["\']([^"\'>?\s]+)["\']', html)
        # Filter: remove parent dir and absolute links
        filtered = []
        for l in links:
            if l.startswith("/") or "://" in l or l.startswith("?"): continue
            if l.endswith("../"): continue
            filtered.append(l)
        return filtered

    @classmethod
    def get_session(cls):
        if cls._session is None:
            cls._session = requests.Session()
            # Standard Chrome headers
            cls._session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            })
            retry_strategy = Retry(
                total=3,
                backoff_factor=0.5,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(
                pool_connections=1000, 
                pool_maxsize=1000, 
                max_retries=retry_strategy
            )
            cls._session.mount("http://", adapter)
            cls._session.mount("https://", adapter)
            cls._session.verify = False
        return cls._session

    @staticmethod
    def status_code(url: str) -> int:
        try:
            return Internet.get_session().head(url, timeout=Internet.timeout).status_code
        except requests.exceptions.RequestException:
            return None

    @staticmethod
    def get(url: str) -> bytes:
        try:
            session = Internet.get_session()
            
            # Use the directory containing .git as Referer (very effective for some server protections)
            current_headers = {}
            if "/.git/" in url:
                referer = url.split("/.git/")[0] + "/"
                current_headers['Referer'] = referer
            
            with session.get(url, timeout=Internet.timeout, stream=False, headers=current_headers) as r:
                status = r.status_code
                content = r.content if status == 200 else b""
                size = len(content) if content else 0
                
                if status == 200:
                    is_valid = Internet.is_valid_git_content(content, url)
                    message.debug(f"GET {url} - Status: {status}, Size: {size}b, Valid: {is_valid}")
                    if is_valid: return content
                else:
                    message.debug(f"GET {url} - Status: {status}")
                return b""
        except Exception as e:
            message.debug(f"GET {url} - Error: {str(e)}")
            return b""

    @staticmethod
    def filesize(url: str) -> int:
        try:
            headers = Internet.get_session().head(url, timeout=Internet.timeout).headers
            return int(headers.get("Content-Length", 0)) or None
        except:
            return None

    @staticmethod
    def download(url: str, filename: str) -> bool:
        try:
            # We use a longer timeout for the actual download
            with Internet.get_session().get(url, timeout=Internet.timeout * 2) as r:
                if r.status_code != 200:
                    return False
                
                content = r.content
                if not Internet.is_valid_git_content(content, url):
                    return False
                    
                with open(filename, "wb") as f:
                    f.write(content)
                return True
        except Exception:
            return False
