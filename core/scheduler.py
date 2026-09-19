"""Windows Task Scheduler integration for WindowsOptimizer maintenance."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

TASK_NAME = "WindowsOptimizer - Daily Maintenance"
DEFAULT_TIME = "03:00"


def _run_powershell(script: str) -> str:
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "PowerShell failed.")
    return result.stdout.strip()


def _task_action() -> tuple[str, str]:
    if getattr(sys, "frozen", False):
        return sys.executable, "--maintenance daily"

    root = Path(__file__).resolve().parent.parent
    main = root / "main.py"
    return sys.executable, f'"{main}" --maintenance daily'


def install_daily_schedule(start_time: str = DEFAULT_TIME) -> str:
    """Create one daily SYSTEM task with missed-run recovery."""
    executable, arguments = _task_action()
    if ":" not in start_time:
        raise ValueError("start_time must use HH:MM.")

    escaped_exe = executable.replace("'", "''")
    escaped_args = arguments.replace("'", "''")
    escaped_task = TASK_NAME.replace("'", "''")

    script = f"""
$action = New-ScheduledTaskAction -Execute '{escaped_exe}' -Argument '{escaped_args}'
$trigger = New-ScheduledTaskTrigger -Daily -At '{start_time}'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName '{escaped_task}' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
"""
    try:
        output = _run_powershell(script)
    except Exception as exc:
        raise RuntimeError(
            "Creating the daily maintenance task requires an elevated Windows Optimizer session."
        ) from exc
    return output or f"Daily maintenance scheduled at {start_time}."


def remove_daily_schedule() -> str:
    escaped_task = TASK_NAME.replace("'", "''")
    script = (
        f"Unregister-ScheduledTask -TaskName '{escaped_task}' "
        "-Confirm:$false -ErrorAction SilentlyContinue"
    )
    _run_powershell(script)
    return "Daily maintenance schedule removed."


def run_daily_schedule_now() -> str:
    escaped_task = TASK_NAME.replace("'", "''")
    _run_powershell(f"Start-ScheduledTask -TaskName '{escaped_task}'")
    return "Daily maintenance task started."


def schedule_status() -> dict:
    escaped_task = TASK_NAME.replace("'", "''")
    script = f"""
$task = Get-ScheduledTask -TaskName '{escaped_task}' -ErrorAction SilentlyContinue
if (-not $task) {{ Write-Output 'NOT_FOUND'; exit 0 }}
$info = Get-ScheduledTaskInfo -TaskName '{escaped_task}'
[pscustomobject]@{{
    state = [string]$task.State
    enabled = [bool]$task.Settings.Enabled
    next_run = [string]$info.NextRunTime
    last_run = [string]$info.LastRunTime
    last_result = [int]$info.LastTaskResult
}} | ConvertTo-Json -Compress
"""
    try:
        output = _run_powershell(script)
    except Exception as exc:
        return {"installed": False, "error": str(exc)}

    if output == "NOT_FOUND":
        return {"installed": False}
    try:
        import json
        data = json.loads(output)
        data["installed"] = True
        return data
    except Exception:
        return {"installed": False, "error": output}
