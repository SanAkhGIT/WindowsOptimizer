import ctypes
import json
import platform

import psutil

from core.process import run_executable


_LAPTOP_CHASSIS = {"8", "9", "10", "11", "12", "14", "18", "21", "30", "31", "32"}


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _query():
    script = r"""
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1 Name
$disk = Get-PhysicalDisk | Select-Object -First 1 MediaType
$chassis = @(Get-CimInstance Win32_SystemEnclosure | Select-Object -Expand ChassisTypes)
[pscustomobject]@{
    cpu = $cpu.Name
    gpu = $gpu.Name
    disk = $disk.MediaType
    chassis = $chassis
} | ConvertTo-Json -Compress
"""
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-Command", script],
        timeout=20,
    )
    if result.returncode:
        return {}
    try:
        value = json.loads(result.stdout or "{}")
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_system_info():
    queried = _query()
    chassis = queried.get("chassis") or []
    if isinstance(chassis, str):
        chassis = [chassis]
    return {
        "windows": platform.platform(),
        "build": platform.version(),
        "cpu": queried.get("cpu") or platform.processor() or "Unknown",
        "gpu": queried.get("gpu") or "Unknown",
        "disk": queried.get("disk") or "Unknown",
        "ram_gb": round(psutil.virtual_memory().total / 1073741824, 1),
        "device_type": "Laptop" if any(str(x) in _LAPTOP_CHASSIS for x in chassis) else "Desktop",
        "admin": is_admin(),
        "battery": bool(psutil.sensors_battery()),
    }
