"""Startup inventory and conservative reversible controls."""

import base64
import json
from core.process import run_executable

def _ps(script, timeout=90):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable("powershell.exe", ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded), timeout)

def inventory():
    script = r"""
$startup = @(Get-CimInstance Win32_StartupCommand -ErrorAction SilentlyContinue |
  Select-Object Name,Command,Location,User,UserSID)
$tasks = @(Get-ScheduledTask -ErrorAction SilentlyContinue |
  Where-Object { $_.TaskPath -notlike 'Microsoft*' } |
  Select-Object TaskName,TaskPath,State)
[pscustomobject]@{ Startup = $startup; ScheduledTasks = $tasks } |
  ConvertTo-Json -Depth 6 -Compress
"""
    r = _ps(script)
    if r.returncode:
        raise RuntimeError(r.stderr or "Startup inventory failed.")
    return r.stdout or "{}"

def records():
    value = json.loads(inventory())
    startup = value.get("Startup", []) if isinstance(value, dict) else []
    tasks = value.get("ScheduledTasks", []) if isinstance(value, dict) else []
    if isinstance(startup, dict): startup = [startup]
    if isinstance(tasks, dict): tasks = [tasks]
    return {
        "startup": [classify(item) for item in startup],
        "scheduled_tasks": tasks,
    }

def classify(entry):
    location = str(entry.get("Location") or "")
    command = str(entry.get("Command") or "")
    user = str(entry.get("User") or "")
    location_upper = location.upper()
    if "STARTUP" in location_upper:
        source = "Startup folder"
    elif "\RUNONCE" in location_upper:
        source = "Registry RunOnce"
    elif "\RUN" in location_upper:
        source = "Registry Run"
    else:
        source = "Other"
    scope = "User" if "HKCU" in location_upper or "CURRENT_USER" in location_upper or user else "System"
    return {
        **entry,
        "scope": scope,
        "source": source,
        "manageable": scope == "User" and source in {"Registry Run", "Registry RunOnce"},
        "impact": "User startup" if scope == "User" else "System startup",
        "command": command,
    }

def disable_user_run(name, run_once=False):
    from modules.startup_controls import disable_user_run as disable
    return disable(name, run_once)

def restore_user_run(name, run_once=False):
    from modules.startup_controls import restore_user_run as restore
    return restore(name, run_once)
