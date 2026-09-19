from core.process import run_executable

def inventory():
    ps = (
        r"Get-CimInstance Win32_Service | "
        r"Select-Object Name,DisplayName,State,StartMode,StartName,PathName | "
        r"ConvertTo-Json -Compress"
    )
    r = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps],
        120,
    )
    if r.returncode:
        raise RuntimeError(r.stderr or "Service inventory failed.")
    return r.stdout or "[]"

def classify(service):
    text = " ".join(
        str(service.get(key, "") or "")
        for key in ("Name", "DisplayName", "PathName", "StartName")
    ).lower()
    if any(token in text for token in ("microsoft", r"\windows\", "windows\")):
        return "Windows"
    if any(token in text for token in ("intel", "amd", "nvidia", "realtek", "oem")):
        return "Hardware/OEM"
    return "Third-party/Unknown"
