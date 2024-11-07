from urllib.parse import urlparse
from typing import Optional


def git_url(url: str) -> dict[str, str]:
    splitted = url.split("/")
    if "@" in url:
        return {
            "host": url.split("@")[1].split(":")[0],
            "user": splitted[-2].split(":")[1],
            "name": splitted[-1].split(".")[0],
            "url": url,
        }
    return {
        "host": domain(url),
        "user": splitted[-2],
        "name": splitted[-1].split(".")[0],
        "url": url,
    }


def url_git(url: str) -> dict[str, Optional[str]]:
    splitted = url.split("/")
    return {"host": None, "user": base_domain(url), "name": "", url: url}


def subdomain(url: str):
    domain_parts = urlparse(url).netloc.split(".")
    return ".".join(domain_parts[:-2]) if len(domain_parts) > 2 else None


def domain(url: str):
    return urlparse(url).netloc


def base_domain(url: str):
    domain_parts = urlparse(url).netloc.split(".")
    return (
        domain_parts[-3]
        if len(domain_parts) > 2
        else domain_parts[-2] if len(domain_parts) > 1 else domain_parts[0]
    )


def protocol(url: str):
    return urlparse(url).scheme


def fixed_url(url: str):
    parsed_url = urlparse(url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return domain
