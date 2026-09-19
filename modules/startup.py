import json
import os
import re

from core.process import run_executable


_RUN_KEY_RE = re.compile(
    r"(HKCU|HKEY_CURRENT_USER|HKLM|HKEY_LOCAL_MACHINE).*?\\Run(?:Once)?",
    re.I,
)


def inventory():
    ps = (
        r"Get-CimInstance Win32_StartupCommand | "
        r"Select-Object Name,Command,Location,User | ConvertTo-Json -Compress"
    )
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps],
        60,
    )
    if result.returncode:
        raise RuntimeError(result.stderr or "Startup inventory failed.")
    return result.stdout or "[]"


def records():
    raw = inventory()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Startup inventory returned invalid JSON: {exc}") from exc
    if isinstance(value, dict):
        value = [value]
    return [classify(v) for v in value]


def _command_path(command):
    command = str(command or "").strip()
    quoted = re.match(r'^"([^"]+\.(?:exe|com|bat|cmd|vbs|ps1))"', command, re.I)
    if quoted:
        return quoted.group(1)
    unquoted = re.match(r"^([^\s]+\.(?:exe|com|bat|cmd|vbs|ps1))", command, re.I)
    if unquoted:
        return unquoted.group(1)
    return command.split(None, 1)[0] if command else ""


def classify(entry):
    location = str(entry.get("Location", "") or "")
    command = str(entry.get("Command", "") or "")
    user = str(entry.get("User", "") or "")
    location_upper = location.upper()

    scope = (
        "User"
        if "HKCU" in location_upper
        or "CURRENT_USER" in location_upper
        or user
        else "System"
    )

    if "STARTUP" in location_upper:
        source = "Startup folder"
    elif _RUN_KEY_RE.search(location):
        source = "Registry Run"
    else:
        source = "Other"

    path = _command_path(command)
    exists = bool(path and os.path.exists(os.path.expandvars(path)))
    return {
        **entry,
        "scope": scope,
        "source": source,
        "executable": path,
        "executable_exists": exists,
    }


def impact(record):
    source = record.get("source", "Other")
    scope = record.get("scope", "System")
    path = record.get("executable", "")
    if not record.get("executable_exists", False):
        return "Stale/Unknown"
    windir = os.environ.get("WINDIR", r"C:\Windows").lower()
    programfiles = os.environ.get("PROGRAMFILES", r"C:\Program Files").lower()
    if path.lower().startswith((windir, programfiles)):
        return "System-managed"
    if scope == "User" and source in ("Registry Run", "Startup folder"):
        return "User startup"
    return "Third-party/User-managed"
