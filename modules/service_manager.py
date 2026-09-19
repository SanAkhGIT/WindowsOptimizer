"""Conservative service inspection and reversible startup controls."""

import base64
import json
from datetime import datetime
from pathlib import Path

from core.process import run_executable

BACKUP_FILE = Path.home() / "WindowsOptimizerBackups" / "services.json"


def _ps(script, timeout=90):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable(
        "powershell.exe",
        ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded),
        timeout,
    )


def _valid(name):
    return bool(name) and not any(c in name for c in "\r\n;&|")


def inventory():
    script = r"""Get-CimInstance Win32_Service |
Select-Object Name,DisplayName,Description,State,StartMode,StartName,PathName,ProcessId,AcceptStop,AcceptPause,Started |
Sort-Object DisplayName |
ConvertTo-Json -Depth 4 -Compress"""
    result = _ps(script)
    if result.returncode:
        raise RuntimeError(result.stderr or "Service inventory failed.")
    return result.stdout or "[]"


def details(name):
    if not _valid(name):
        raise ValueError("Invalid service name.")
    safe = name.replace("'", "''")
    script = f"""$svc=Get-CimInstance Win32_Service -Filter "Name='{safe}'" -ErrorAction Stop
$deps=Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
[pscustomobject]@{{
Name=$svc.Name
DisplayName=$svc.DisplayName
Description=$svc.Description
State=$svc.State
StartMode=$svc.StartMode
StartName=$svc.StartName
PathName=$svc.PathName
ProcessId=$svc.ProcessId
Dependencies=@($deps.ServicesDependedOn.Name)
DependentServices=@($deps.DependentServices.Name)
}} | ConvertTo-Json -Depth 6 -Compress"""
    result = _ps(script)
    if result.returncode:
        raise RuntimeError(result.stderr or "Service detail query failed.")
    return result.stdout or "{}"


def _load_backup():
    if not BACKUP_FILE.exists():
        return {}
    try:
        return json.loads(BACKUP_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_backup(data):
    BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _set_start_mode(name, mode):
    safe = name.replace("'", "''")
    filter_expr = f"Name='{safe}'"
    script = (
        f"Set-Service -Name '{safe}' -StartupType {mode}; "
        f"Get-CimInstance Win32_Service -Filter \"{filter_expr}\" | "
        "Select-Object Name,StartMode,State | ConvertTo-Json -Compress"
    )
    return _ps(script)


def set_start_mode(name, mode):
    if mode not in {"Automatic", "Manual", "Disabled"} or not _valid(name):
        raise ValueError("Invalid service name or startup mode.")
    current = json.loads(details(name))
    data = _load_backup()
    data.setdefault(
        name,
        {
            "name": name,
            "original_start_mode": current.get("StartMode"),
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        },
    )
    _save_backup(data)

    result = _set_start_mode(name, mode)
    if result.returncode:
        raise RuntimeError(result.stderr or "Service startup mode change failed.")
    return result.stdout or f"Service '{name}' set to {mode}."


def restore_start_mode(name):
    data = _load_backup()
    item = data.get(name)
    if not item or not item.get("original_start_mode"):
        raise RuntimeError(f"No saved startup mode exists for {name}.")
    mode = {
        "Auto": "Automatic",
        "Manual": "Manual",
        "Disabled": "Disabled",
    }.get(item["original_start_mode"], item["original_start_mode"])

    result = _set_start_mode(name, mode)
    if result.returncode:
        raise RuntimeError(result.stderr or "Service restore failed.")
    data.pop(name, None)
    _save_backup(data)
    return result.stdout or f"Restored {name} to {mode}."


def start(name):
    return _action(name, "Start-Service")


def stop(name):
    if not _valid(name):
        raise ValueError("Invalid service name.")
    detail = json.loads(details(name))
    if detail.get("DependentServices"):
        raise RuntimeError(
            "Service has dependent services; review dependencies before stopping it."
        )
    return _action(name, "Stop-Service")


def _action(name, verb):
    if not _valid(name):
        raise ValueError("Invalid service name.")
    safe = name.replace("'", "''")
    script = (
        f"{verb} -Name '{safe}' -ErrorAction Stop; "
        f"Get-Service -Name '{safe}' | "
        "Select-Object Name,Status,StartType | ConvertTo-Json -Compress"
    )
    result = _ps(script)
    if result.returncode:
        raise RuntimeError(result.stderr or f"{verb} failed.")
    return result.stdout or f"{verb} completed."


def saved_changes():
    return list(_load_backup().values())
