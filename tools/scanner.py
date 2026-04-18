import re
from tools.logger import message
from tools.strings import domain as get_domain

class Scanner:
    def __init__(self, mode="all"):
        self.mode = mode.lower()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def passive(self, target_domain: str) -> list[str]:
        """Discovery via crt.sh (SSL Certificates)"""
        from tools.files import Internet
        message.info(f"Passive scanning for: {target_domain} (this may take a minute...)")
        subdomains = set()
        try:
            url = f"https://crt.sh/?q=%.{target_domain}&output=json"
            # Use the global session with retries and a larger timeout
            response = Internet.get_session().get(url, headers=self.headers, timeout=60)
            if response.status_code == 200:
                data = response.json()
                for entry in data:
                    name = entry['name_value'].lower()
                    # Clean up multi-name entries and wildcards
                    names = name.split('\n')
                    for n in names:
                        if "*" not in n and n.endswith(target_domain):
                            subdomains.add(n)
            message.success(f"Found {len(subdomains)} subdomains via crt.sh")
        except Exception as e:
            message.error(f"Error in passive scan: {str(e)}")
        
        return list(subdomains)

    @staticmethod
    def scan_local(root_path: str) -> list[tuple[str, str]]:
        """Find local .git folders and extract their remote URLs"""
        import os
        import configparser
        from tools.logger import message

        found_repos = []
        message.info(f"Scanning for local repositories in: {root_path}")
        
        # Normalize and check if root_path itself is a .git directory or project directory
        root_path = os.path.abspath(root_path)

        def check_repo(d_path):
            # Check if this directory is a .git folder or contains one
            g_dir = d_path if d_path.endswith(".git") else os.path.join(d_path, ".git")
            c_path = os.path.join(g_dir, "config")
            
            if os.path.exists(c_path):
                url = None
                try:
                    config = configparser.ConfigParser()
                    config.read(c_path)
                    for section in config.sections():
                        if section.startswith('remote') and 'url' in config[section]:
                            temp_url = config[section]['url']
                            # If it's a known upstream host, ignore it to force inference from folder
                            if any(x in temp_url.lower() for x in ["github.com", "gitlab.com", "bitbucket.org"]):
                                url = None
                            else:
                                url = temp_url
                            break
                except: pass

                if not url:
                    # Infer domain from parent folder name
                    p_name = os.path.basename(os.path.dirname(g_dir))
                    if "." in p_name: url = f"https://{p_name}/.git/"
                
                if url:
                    # Normalize URL
                    if not url.startswith("http"): url = f"https://{url}"
                    if not url.endswith(".git/"): 
                        url = url.rstrip("/") + "/.git/"
                    return (url, os.path.dirname(g_dir))
            return None

        # 1. Check root_path first
        direct_hit = check_repo(root_path)
        if direct_hit:
            found_repos.append(direct_hit)
        else:
            # 2. Walk if not a direct hit
            for dirpath, dirnames, _ in os.walk(root_path):
                if ".git" in dirnames:
                    res = check_repo(os.path.join(dirpath, ".git"))
                    if res: found_repos.append(res)
                    dirnames.remove(".git")
        
        return found_repos

    def search(self, target_domain: str) -> list[str]:
        """Discovery via Search Engines (Basic Dorks simulated)"""
        message.info(f"Search engine discovery for: {target_domain}")
        # For simplicity without external heavy dependencies, we use a simulation of common dork patterns
        # or we could use many scrapers. For now, let's use a common pattern for public discovery.
        # Ideally, we'd use a search API here.
        targets = set()
        
        # Simulated dork results or if we had googlesearch-python:
        # url = f"https://www.google.com/search?q=site:*.{target_domain}+inurl:.git"
        
        # For the MVP, we will treat 'search' as discovery of specific .git paths on the target
        # In a real scenario, this would call a Search API.
        message.warn("Search mode currently relies on common path discovery for the domain")
        
        # We'll just return the base domain to ensure it's checked if no subdomains found
        targets.add(target_domain)
        return list(targets)

    def scan(self, target: str) -> list[str]:
        all_targets = set()
        
        if self.mode in ["passive", "all"]:
            subs = self.passive(target)
            all_targets.update(subs)
            
        if self.mode in ["search", "all"]:
            # If search logic is added later, it populates here
            # For now, ensure the main target is included
            all_targets.add(target)
            
        # Convert to full .git URLs
        final_urls = []
        for t in all_targets:
            url = t if t.startswith("http") else f"https://{t}"
            if not url.endswith("/"): url += "/"
            if not url.endswith(".git/"): url += ".git/"
            final_urls.append(url)
            
        return final_urls
