from core.process import run_executable


def run_command(command, timeout=120):
    result = run_executable(
        "powershell.exe",
        (
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ),
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr
