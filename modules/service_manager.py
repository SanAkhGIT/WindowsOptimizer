import base64
from core.process import run_executable

def _ps(script, timeout=90):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable("powershell.exe", ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded), timeout)

def inventory():
    r = _ps("Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,StartName,PathName | Sort-Object DisplayName | ConvertTo-Json -Compress")
    if r.returncode: raise RuntimeError(r.stderr or "Service inventory failed.")
    return r.stdout or "[]"

def _valid(name):
    return bool(name) and not any(c in name for c in "\r\n;&|")

def set_start_mode(name, mode):
    if mode not in {"Automatic", "Manual", "Disabled"} or not _valid(name):
        raise ValueError("Invalid service name or startup mode.")
    safe = name.replace("'", "''")
    r = _ps(f"Set-Service -Name '{safe}' -StartupType {mode}; Get-Service -Name '{safe}' | Select-Object Name,Status,StartType | ConvertTo-Json -Compress")
    if r.returncode: raise RuntimeError(r.stderr or "Service startup mode change failed.")
    return r.stdout or f"Service '{name}' set to {mode}."

def start(name):
    return _action(name, "Start-Service")

def stop(name):
    return _action(name, "Stop-Service")

def _action(name, verb):
    if not _valid(name): raise ValueError("Invalid service name.")
    safe = name.replace("'", "''")
    r = _ps(f"{verb} -Name '{safe}' -ErrorAction Stop; Get-Service -Name '{safe}' | Select-Object Name,Status,StartType | ConvertTo-Json -Compress")
    if r.returncode: raise RuntimeError(r.stderr or f"{verb} failed.")
    return r.stdout or f"{verb} completed."
