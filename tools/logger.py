from datetime import datetime
import os

DEBUG = os.getenv("debug", "false").lower() == "true"


class color:
    class foreground:
        black = "\033[30m"
        red = "\033[31m"
        green = "\033[32m"
        orange = "\033[33m"
        blue = "\033[34m"
        purple = "\033[35m"
        cyan = "\033[36m"
        lightgrey = "\033[37m"
        darkgrey = "\033[90m"
        lightred = "\033[91m"
        lightgreen = "\033[92m"
        yellow = "\033[93m"
        lightblue = "\033[94m"
        pink = "\033[95m"
        lightcyan = "\033[96m"
        reset = "\033[0m"

    def red(message):
        return f"{color.foreground.red}{message}{color.foreground.reset}"

    def black(message):
        return f"{color.foreground.black}{message}{color.foreground.reset}"

    def green(message):
        return f"{color.foreground.green}{message}{color.foreground.reset}"

    def orange(message):
        return f"{color.foreground.orange}{message}{color.foreground.reset}"

    def blue(message):
        return f"{color.foreground.blue}{message}{color.foreground.reset}"

    def purple(message):
        return f"{color.foreground.purple}{message}{color.foreground.reset}"

    def cyan(message):
        return f"{color.foreground.cyan}{message}{color.foreground.reset}"

    def lightgrey(message):
        return f"{color.foreground.lightgrey}{message}{color.foreground.reset}"

    def darkgrey(message):
        return f"{color.foreground.darkgrey}{message}{color.foreground.reset}"

    def lightred(message):
        return f"{color.foreground.lightred}{message}{color.foreground.reset}"

    def lightgreen(message):
        return f"{color.foreground.lightgreen}{message}{color.foreground.reset}"

    def yellow(message):
        return f"{color.foreground.yellow}{message}{color.foreground.reset}"

    def lightblue(message):
        return f"{color.foreground.lightblue}{message}{color.foreground.reset}"

    def pink(message):
        return f"{color.foreground.pink}{message}{color.foreground.reset}"

    def lightcyan(message):
        return f"{color.foreground.lightcyan}{message}{color.foreground.reset}"


class date:
    def print(message) -> None:
        print(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] {message}')


class message:
    def __checker(variable):
        type_mapping = {list: "<list>", dict: "<dict>", tuple: "<tuple>"}
        return f"{type_mapping.get(type(variable), '')} {variable}"

    def __stringMaker(vars):
        return " ".join(map(lambda arg: message.__checker(arg), vars))

    def log(*args) -> None:
        date.print(f"[LOG]{message.__stringMaker(args)}")

    def error(*args) -> None:
        date.print(f"[{color.red('ERROR')}]{message.__stringMaker(args)}")

    def warn(*args) -> None:
        date.print(f"[{color.yellow('WARN')}]{message.__stringMaker(args)}")

    def info(*args) -> None:
        date.print(f"[{color.cyan('INFO')}]{message.__stringMaker(args)}")

    def debug(*args) -> None:
        (
            date.print(f"[{color.purple('DEBUG')}]{message.__stringMaker(args)}")
            if DEBUG
            else None
        )

    def success(*args) -> None:
        date.print(f"[{color.lightgreen('SUCCESS')}]{message.__stringMaker(args)}")

    def custom(prefix: str, *args) -> None:
        date.print(
            f"[{color.lightcyan(prefix.capitalize())}]{message.__stringMaker(args)}"
        )
