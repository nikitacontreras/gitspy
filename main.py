from tools.git import Web as GitWeb
from tools.strings import *
from tools.logger import message


class Repository:
    def __init__(self, url: str):
        self.domain = domain(url)
        message.debug(self.domain, url, fixed_url(url))
        self.gitweb = GitWeb()
        self.gitweb.setDomain(fixed_url(url))

    def init(self) -> None:
        self.check_if_git_folder()
        self.process_remote_repo()

    def check_if_git_folder(self) -> None:
        if self.gitweb.hasGitFolder():
            message.success(f"{self.domain} has a valid git folder")
            message.info(
                f"{self.domain} has {'directory listing' if self.gitweb.isExplorable() else 'no directory listing'}"
            )
        else:
            message.error(f"{self.domain} does not have a valid git folder")
            exit()

    def process_remote_repo(self) -> None:
        message.log(f"Getting repository info")

        self.gitweb.files.config
        self.gitweb.files.start_download()


def main():
    for url in [
        "https://example.com/.git/",
    ]:
        repo = Repository(url)
        repo.init()
        message.success(f"Finished processing {url}")


if __name__ == "__main__":
    main()
