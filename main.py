from tools.git import Web as GitWeb
from tools.strings import *
from tools.logger import message
import argparse
import os


class Repository:
    def __init__(self, url: str, output: str = None):
        if not url:
            return
        self.url = url
        self.domain = domain(url)
        message.debug(self.domain, url, fixed_url(url))
        self.gitweb = GitWeb()
        self.gitweb.setDomain(url)
        self.output = output

    def init(self, position: int = 0, force_dir: str = None) -> None:
        self.check_if_git_folder()
        self.process_remote_repo(position=position, force_dir=force_dir)

    def check_if_git_folder(self) -> None:
        message.info(f"Probing {self.url} for infrastructure...")
        if self.gitweb.probe():
            message.success(f"{self.domain} has a valid {self.gitweb.REPO_TYPE} exposure")
        else:
            message.error(f"{self.domain} does not have any supported repository exposure")
            raise Exception(f"{self.domain} no exposure found")

    def process_remote_repo(self, position: int = 0, force_dir: str = None) -> None:
        message.log(f"Getting repository info for {self.url}")

        self.gitweb.files.config
        self.gitweb.files.start_download(self.output, position=position, force_dir=force_dir)


def banner():
    art = """
 ____  __ _____   __ _____ _  _
(( ___ ||  ||    ((  ||_// \\\\//
 \\\\_|| ||  ||   \\_)) ||     // 
    """
    print(art)

def main():
    banner()
    parser = argparse.ArgumentParser(
        description="GitSpy - The Ultimate Multi-Protocol Reconnaissance Engine\n" + 
        " ____  __ _____   __ _____ _  _ \n" +
        "(( ___ ||  ||    ((  ||_// \\\\// \n" +
        " \\\\_|| ||  ||   \\_)) ||     // ",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Target URL (e.g., https://example.com/.git)")
    group.add_argument("--list", help="Path to a text file containing target URLs (one per line)")
    group.add_argument("--scan", help="Target domain to scan for subdomains (e.g., example.com)")
    group.add_argument("--repair-path", help="Local path to scan for .git folders and attempt to finish extraction")

    parser.add_argument("--repair", help="Enable repair mode: resume downloads if local folder exists", action="store_true")
    parser.add_argument("--output", help="Output directory where the repository will be saved", default=None)
    parser.add_argument("--mode", help="Scanning mode: passive, extensive, search, all", default="all", choices=["passive", "extensive", "search", "all"])
    parser.add_argument("--speed", help="Processing speed: patient (one by one) or impatient (parallel)", default="patient", choices=["patient", "impatient"])
    parser.add_argument("--timeout", help="Request timeout in seconds", type=int, default=15)
    parser.add_argument("--concurrency", "--parallel", help="Number of repositories to process in parallel (impatient mode)", type=int, default=5)
    parser.add_argument("-v", "--verbose", help="Increase verbosity level (-v, -vv, -vvv, -vvvv)", action="count", default=0)
    
    args = parser.parse_args()
    message.set_level(args.verbose)
    
    initial_dir = os.getcwd()

    urls = []
    if args.repair_path:
        from tools.scanner import Scanner
        urls = Scanner.scan_local(args.repair_path)
        if not urls:
            message.warn(f"No local repositories with valid config found in: {args.repair_path}")
            return
        message.success(f"Found {len(urls)} repositories to repair.")
    elif args.url:
        urls.append(args.url)
    elif args.list:
        if not os.path.exists(args.list):
            message.error(f"File not found: {args.list}")
            return
        with open(args.list, "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    elif args.scan:
        from tools.scanner import Scanner
        scanner = Scanner(mode=args.mode)
        urls = scanner.scan(args.scan)
        if not urls:
            message.warn(f"No targets found for {args.scan}")
            return
        message.info(f"Adding {len(urls)} potential targets to queue")

    def process_url(data):
        target, pos = data
        url = target[0] if isinstance(target, tuple) else target
        force_dir = target[1] if isinstance(target, tuple) else None
        
        # Auto-detect local folder if --repair is enabled and no force_dir provided
        if args.repair and not force_dir:
            from tools.strings import domain as get_domain
            domain_name = get_domain(url)
            local_base = args.output if args.output else os.getcwd()
            # Try to find the local repo path
            potential_path = os.path.join(local_base, "repos", domain_name)
            if os.path.exists(potential_path):
                force_dir = os.path.join(potential_path, ".git") if not potential_path.endswith(".git") else potential_path
                message.info(f"Local repo found for {domain_name}, enabling repair mode.")

        try:
            repo = Repository(url, args.output)
            repo.gitweb.set_timeout(args.timeout)
            repo.init(position=pos, force_dir=force_dir)
            # message.success is already handled inside finish extraction or Repository methods
        except Exception as e:
            message.error(f"Error processing {url}: {str(e)}")

    if args.speed == "impatient":
        import concurrent.futures
        max_parallel_repos = args.concurrency
        url_queue = [(url, i % max_parallel_repos) for i, url in enumerate(urls)]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel_repos) as executor:
            executor.map(process_url, url_queue)
    else:
        for url in urls:
            process_url((url, 0))


if __name__ == "__main__":
    main()
