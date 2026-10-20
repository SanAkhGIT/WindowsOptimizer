import subprocess

from core.process import hidden_console_kwargs


def run_command(command, timeout=120):
    p = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        **hidden_console_kwargs(),
    )
    return p.returncode, p.stdout.strip(), p.stderr.strip()
