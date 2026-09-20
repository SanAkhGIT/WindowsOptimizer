import json
from core.process import run_executable


def inventory():
    ps = (
        r"Get-CimInstance Win32_Service | "
        r"Select-Object Name,DisplayName,State,StartMode,StartName,PathName | "
        r"ConvertTo-Json -Compress"
    )
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps],
        120,
    )
    if result.returncode:
        raise RuntimeError(result.stderr or "Service inventory failed.")
    return result.stdout or "[]"


def records():
    try:
        value = json.loads(inventory())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Service inventory returned invalid JSON: {exc}") from exc
    if isinstance(value, dict):
        value = [value]
    return [
        {
            **item,
            "classification": classify(item),
            "recommendation": recommendation(item),
        }
        for item in value
    ]


def classify(service):
    import os
    name = str(service.get("Name", "") or "").lower()
    display = str(service.get("DisplayName", "") or "").lower()
    path = str(service.get("PathName", "") or "").lower()
    windir = str(os.environ.get("WINDIR", r"C:\Windows")).lower().rstrip("\\")
    if path.startswith(windir + "\\") or ("\\windows\\" in path and path.startswith(r"\\?\\")):
        return "Windows"
    combined = " ".join((name, display, path))
    if any(marker in combined for marker in ("amd", "intel", "nvidia", "realtek", "msi", "asus", "lenovo", "dell", "oem")):
        return "Hardware/OEM"
    if "microsoft defender" in display or display.startswith("windows ") or name.startswith("wuauserv"):
        return "Windows/Security"
    if path.startswith(r"c:\program files") or path.startswith(r"c:\programdata"):
        return "Third-party/Unknown"
    return "Third-party/Unknown"


def recommendation(service):
    mode = str(service.get("StartMode", "") or "").lower()
    state = str(service.get("State", "") or "").lower()
    description = str(service.get("Description", "") or "").lower()
    classification = classify(service)
    if mode == "disabled":
        if "strongly recommended" in description or "system instability" in description:
            return "Attention: disabled service has an explicit Windows warning."
        return "Leave unchanged; already disabled."
    if classification.startswith("Windows"):
        return "Leave unchanged unless diagnosing a specific Windows issue."
    if classification == "Hardware/OEM":
        return "Review only if the associated hardware/software is unused."
    if mode in {"auto", "automatic"} and state == "running":
        return "Review: third-party service starts automatically."
    return "Review publisher, path and dependency before changing startup mode."

def attention(service):
    mode = str(service.get("StartMode", "") or "").lower()
    state = str(service.get("State", "") or "").lower()
    description = str(service.get("Description", "") or "")
    classification = classify(service)
    if not description or "failed to read description" in description.lower():
        return "Inspect"
    if mode == "disabled" and ("strongly recommended" in description.lower() or "system instability" in description.lower()):
        return "Attention"
    if classification.startswith("Third-party") and mode in {"auto", "automatic"} and state == "running":
        return "Review"
    return "Normal"
