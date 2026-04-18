import subprocess


class cmd:
    def __init__(self, cmd, cwd=None):
        self.cmd = cmd.split(" ")
        self.cwd = cwd
        self.out = None
        self.err = None
        self.ret = None

        self.run()

    def run(self):
        process = subprocess.run(
            self.cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            cwd=self.cwd
        )
        self.out, self.err = process.stdout.strip(), process.stderr.strip()
        self.ret = process.returncode
