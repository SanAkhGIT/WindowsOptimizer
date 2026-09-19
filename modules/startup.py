import json
from core.process import run_executable

def inventory():
    ps = r"Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location,User | ConvertTo-Json -Compress"
    r = run_executable("powershell.exe", ["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",ps], 60)
    if r.returncode:
        raise RuntimeError(r.stderr or "Startup inventory failed.")
    return r.stdout or "[]"

def records():
    raw = inventory()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Startup inventory returned invalid JSON: {exc}") from exc
    if isinstance(value, dict):
        value = [value]
    return value

def classify(entry):
    location = str(entry.get("Location", "") or "").lower()
    command = str(entry.get("Command", "") or "").lower()
    user = str(entry.get("User", "") or "")
    scope = "User" if "hkcu" in location or user else "System"
    if "startup" in location:
        source = "Startup folder"
    elif "run" in location:
        source = "Registry Run"
    else:
        source = "Other"
    return {"scope": scope, "source": source, "command": command}
