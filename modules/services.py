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
    text = " ".join(
        str(service.get(key, "") or "")
        for key in ("Name", "DisplayName", "PathName", "StartName")
    ).lower()
    windows_markers = ("microsoft", "\\windows\\", "windows\\")
    if any(marker in text for marker in windows_markers):
        return "Windows"
    if any(marker in text for marker in ("intel", "amd", "nvidia", "realtek", "oem")):
        return "Hardware/OEM"
    return "Third-party/Unknown"


def recommendation(service):
    if str(service.get("StartMode", "")).lower() == "disabled":
        return "Leave unchanged; already disabled."
    if classify(service) == "Windows":
        return "Leave unchanged unless a specific Windows issue is being diagnosed."
    if classify(service) == "Hardware/OEM":
        return "Review only if the associated hardware/software is unused."
    return "Review publisher, path and dependency before changing startup mode."
