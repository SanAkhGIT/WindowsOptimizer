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


def _normalise_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _extract_address(value):
    """Return a readable IP/DNS value from strings or PowerShell objects."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        preferred = (
            "IPAddress",
            "IPv4Address",
            "IPv6Address",
            "ServerAddresses",
            "Address",
            "Value",
            "NetIPAddress",
        )
        keys = list(preferred) + [key for key in value if key not in preferred]
        for key in keys:
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.strip():
                return candidate.strip()
            if isinstance(candidate, list):
                nested = []
                for item in candidate:
                    extracted = _extract_address(item)
                    if extracted:
                        nested.append(extracted)
                if nested:
                    return ", ".join(nested)
            if isinstance(candidate, dict):
                extracted = _extract_address(candidate)
                if extracted:
                    return extracted
    return ""


def _addresses(value):
    result = []
    for item in _normalise_list(value):
        address = _extract_address(item)
        if address:
            for candidate in address.split(","):
                candidate = candidate.strip()
                if candidate and candidate not in result:
                    result.append(candidate)
    return result


def _network_records(items):
    records = []
    for item in _normalise_list(items):
        if not isinstance(item, dict):
            continue
        interface = str(item.get("InterfaceAlias") or "Network adapter").strip()
        description = str(item.get("InterfaceDescription") or "").strip()
        ipv4 = _addresses(item.get("IPv4Address"))
        ipv6 = _addresses(item.get("IPv6Address"))
        dns = _addresses(item.get("DNSServer"))
        status = str(item.get("Status") or "").strip()
        records.append(
            {
                "InterfaceAlias": interface,
                "InterfaceDescription": description,
                "Status": status,
                "IPv4Address": ipv4,
                "IPv6Address": ipv6,
                "DNSServer": dns,
            }
        )
    return records


def snapshot():
    """Collect slower-changing system inventory in one PowerShell process."""
    script = r"""
$adapters = @(
    Get-NetIPConfiguration -ErrorAction SilentlyContinue |
    ForEach-Object {
        [pscustomobject]@{
            InterfaceAlias = $_.InterfaceAlias
            InterfaceDescription = $_.InterfaceDescription
            Status = $(
                try {
                    (Get-NetAdapter -InterfaceIndex $_.InterfaceIndex -ErrorAction Stop).Status
                } catch {
                    "Unknown"
                }
            )
            IPv4Address = @($_.IPv4Address | ForEach-Object {
                if ($_.IPAddress) { $_.IPAddress } elseif ($_.IPv4Address) { $_.IPv4Address } else { "$_" }
            })
            IPv6Address = @($_.IPv6Address | ForEach-Object {
                if ($_.IPAddress) { $_.IPAddress } elseif ($_.IPv6Address) { $_.IPv6Address } else { "$_" }
            })
            DNSServer = @($_.DNSServer.ServerAddresses)
        }
    }
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
} | ConvertTo-Json -Compress -Depth 8
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
        "network": _network_records(payload.get("network", [])),
        "os_hotfixes": payload.get("hotfixes", []),
        "bios": payload.get("bios", []),
        "motherboard": payload.get("motherboard", []),
        "drivers": payload.get("drivers", []),
    }
