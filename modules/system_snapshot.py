import json
import platform
import socket

import psutil

from core.process import run_executable
from core.system_info import is_admin


def _json_query(script, timeout=30):
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-Command", script],
        timeout,
    )
    if result.returncode:
        return []
    try:
        value = json.loads(result.stdout or "[]")
        return value if isinstance(value, list) else [value]
    except json.JSONDecodeError:
        return []


def snapshot():
    """Collect slower-changing system inventory in one PowerShell process."""
    script = r"""
$adapters = @(
    Get-NetIPConfiguration -ErrorAction SilentlyContinue |
    Select-Object InterfaceAlias,InterfaceDescription,IPv4Address,IPv6Address,DNSServer
)
$hotfixes = @(Get-HotFix -ErrorAction SilentlyContinue | Select-Object HotFixID,Description,InstalledOn)
$bios = @(Get-CimInstance Win32_BIOS -ErrorAction SilentlyContinue | Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate,SerialNumber)
$board = @(Get-CimInstance Win32_BaseBoard -ErrorAction SilentlyContinue | Select-Object Manufacturer,Product,Version)
$drivers = @(
    Get-CimInstance Win32_PnPSignedDriver -ErrorAction SilentlyContinue |
    Select-Object DeviceName,DriverVersion,DriverDate,Manufacturer,IsSigned
)
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1 Name
$disk = Get-PhysicalDisk | Select-Object -First 1 MediaType
$chassis = @(Get-CimInstance Win32_SystemEnclosure | Select-Object -Expand ChassisTypes)
[pscustomobject]@{
    network = $adapters
    hotfixes = $hotfixes
    bios = $bios
    motherboard = $board
    drivers = $drivers
    cpu = $cpu.Name
    gpu = $gpu.Name
    disk = $disk.MediaType
    chassis = $chassis
} | ConvertTo-Json -Compress -Depth 6
"""
    data = _json_query(script, 60)
    payload = data[0] if data else {}
    if not isinstance(payload, dict):
        payload = {}

    chassis = payload.get("chassis", [])
    if isinstance(chassis, str):
        chassis = [chassis]
    laptop_chassis = {"8", "9", "10", "11", "12", "14", "18", "21", "30", "31", "32"}
    system = {
        "windows": platform.platform(),
        "build": platform.version(),
        "cpu": payload.get("cpu") or "Unknown",
        "gpu": payload.get("gpu") or "Unknown",
        "disk": payload.get("disk") or "Unknown",
        "ram_gb": round(psutil.virtual_memory().total / 1073741824, 1),
        "device_type": "Laptop" if any(str(x) in laptop_chassis for x in chassis) else "Desktop",
        "admin": is_admin(),
        "battery": bool(psutil.sensors_battery()),
    }
    return {
        "system": system,
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "network": payload.get("network", []),
        "os_hotfixes": payload.get("hotfixes", []),
        "bios": payload.get("bios", []),
        "motherboard": payload.get("motherboard", []),
        "drivers": payload.get("drivers", []),
    }
