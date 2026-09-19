from core.process import run_executable


def create_restore_point(description="WindowsOptimizer"):
    safe = description.replace("'", "''")
    script = (
        "$ErrorActionPreference='Stop'; "
        f"Checkpoint-Computer -Description '{safe}' -RestorePointType 'MODIFY_SETTINGS'"
    )
    result = run_executable(
        "powershell.exe",
        (
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ),
        timeout=90,
    )
    if result.returncode:
        raise RuntimeError(
            result.stderr or result.stdout or "Restore point creation failed."
        )
    return "System Restore point created."
