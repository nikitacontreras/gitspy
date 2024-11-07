from tools.logger import message

from tqdm import tqdm
from os import path

import requests, urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Internet:
    def status_code(url: str) -> int:
        try:
            return requests.head(url, verify=False).status_code
        except requests.exceptions.ConnectionError as e:
            message.error(f"Connection aborted while fetching headers for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            message.error(f"Failed to fetch headers for {url}: {e}")
            return None
        except:
            return None

    def get(url: str) -> bytes:
        with requests.get(url, verify=False) as r:
            if r.status_code == 200:
                return r.content
            else:
                return b""

    def filesize(url: str) -> int:
        try:
            return (
                int(requests.head(url, verify=False).headers.get("Content-Length", 0))
                or None
            )
        except requests.exceptions.ConnectionError as e:
            message.error(f"Connection aborted while fetching headers for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            message.error(f"Failed to fetch headers for {url}: {e}")
            return None
        except:
            return None

    def download(url: str, filename: str) -> bool:
        try:
            with requests.get(url, stream=True, verify=False) as r:
                r.raise_for_status()
                total_size = int(r.headers.get("content-length", 0))
                block_size = 1024
                t = tqdm(total=total_size, unit="iB", unit_scale=True)
                with open(path.join(filename), "wb") as f:
                    for data in r.iter_content(block_size):
                        t.update(len(data))
                        f.write(data)
                t.close()
                if total_size != 0 and t.n != total_size:
                    message.error("Download failed")
                    return False
                else:
                    message.success("Download completed")
                    return True
        except requests.exceptions.RequestException as e:
            message.error(f"Failed to download {url}: {e}")
