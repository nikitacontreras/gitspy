from urllib.parse import urlparse
from typing import Optional


def git_url(url: str) -> dict[str, str]:
    # Clean trailing slash and .git for splitting logic
    clean_url = url.rstrip("/")
    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]
    
    splitted = clean_url.split("/")
    
    if "@" in url:
        return {
            "host": url.split("@")[1].split(":")[0],
            "user": splitted[-2].split(":")[1] if ":" in splitted[-2] else splitted[-2],
            "name": splitted[-1],
            "url": url,
        }
    
    # Heuristic for non-ssh URLs
    user = splitted[-2] if len(splitted) > 2 else base_domain(url)
    name = splitted[-1] if len(splitted) > 1 else "root"
    
    return {
        "host": domain(url),
        "user": user,
        "name": name,
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
    url_path = parsed_url.path
    
    # Remove /.git or /.git/ from the end of the path
    if url_path.endswith("/.git"):
        url_path = url_path[:-5]
    elif url_path.endswith("/.git/"):
        url_path = url_path[:-6]
    
    # Ensure we don't end with a slash since /.git/ is added later
    if url_path.endswith("/"):
        url_path = url_path[:-1]
        
    return f"{parsed_url.scheme}://{parsed_url.netloc}{url_path}"
