import json
import time

import psutil

from core.process import run_executable

_NETWORK_PREVIOUS = {}
_NETWORK_LOCK = __import__("threading").Lock()


def _powershell(script, timeout=30):
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
        timeout,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Hardware query failed.")
    return result.stdout or "[]"


def live():
    """Collect Task Manager-style performance telemetry without blocking the UI."""
    script = r"""
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name,LoadPercentage,CurrentClockSpeed,MaxClockSpeed
$gpus = @(Get-CimInstance Win32_VideoController |
    Select-Object Name,DriverVersion,DriverDate,AdapterRAM,VideoProcessor)
$gpuUsage = @{}
try {
    Get-CimInstance Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine -ErrorAction Stop |
      Where-Object { $_.Name -match "_phys_(\d+)_.*engtype_3D" } |
      ForEach-Object {
        if ($_.Name -match "_phys_(\d+)_") {
          $index = [int]$matches[1]
          if (-not $gpuUsage.ContainsKey($index)) { $gpuUsage[$index] = 0.0 }
          $gpuUsage[$index] += [double]$_.UtilizationPercentage
        }
      }
} catch {}
$diskPerf = @{}
try {
    Get-CimInstance Win32_PerfFormattedData_PerfDisk_LogicalDisk -ErrorAction Stop |
      Where-Object { $_.Name -ne "_Total" } |
      ForEach-Object { $diskPerf[$_.Name] = [double]$_.PercentDiskTime }
} catch {}
[pscustomobject]@{
    cpu = $cpu
    gpus = $gpus
    gpuUsage = $gpuUsage
    diskPerf = $diskPerf
} | ConvertTo-Json -Compress -Depth 5
"""
    value = json.loads(_powershell(script, 20))
    if not isinstance(value, dict):
        value = {}

    memory = psutil.virtual_memory()
    disks = []
    for partition in psutil.disk_partitions(all=False):
        device = partition.device
        if not device or ":" not in device:
            continue
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (OSError, PermissionError):
            continue
        disks.append({
            "name": device.rstrip("\\"),
            "mountpoint": partition.mountpoint,
            "fstype": partition.fstype,
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "percent": usage.percent,
            "active_percent": float(value.get("diskPerf", {}).get(device.rstrip("\\").upper(), 0) or 0),
        })

    now = time.monotonic()
    network = []
    counters = psutil.net_io_counters(pernic=True)
    with _NETWORK_LOCK:
        for name, counter in counters.items():
            previous = _NETWORK_PREVIOUS.get(name)
            sent_rate = recv_rate = 0.0
            if previous:
                previous_time, previous_sent, previous_recv = previous
                elapsed = max(now - previous_time, 0.1)
                sent_rate = max(0, counter.bytes_sent - previous_sent) / elapsed
                recv_rate = max(0, counter.bytes_recv - previous_recv) / elapsed
            _NETWORK_PREVIOUS[name] = (now, counter.bytes_sent, counter.bytes_recv)
            if counter.bytes_sent or counter.bytes_recv:
                network.append({
                    "name": name,
                    "sent_bps": sent_rate,
                    "recv_bps": recv_rate,
                    "sent_total": counter.bytes_sent,
                    "recv_total": counter.bytes_recv,
                })

    return {
        "cpu": value.get("cpu") or {},
        "gpus": value.get("gpus") if isinstance(value.get("gpus"), list) else [value.get("gpus")] if value.get("gpus") else [],
        "memory": {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent,
        },
        "disks": disks,
        "network": network,
    }



def sensors():
    """Return Windows-exposed thermal-zone and fan sensor records."""
    script = r"""
$temps = @()
$fans = @()
try { $temps = @(Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction Stop | Select-Object Name,CurrentTemperature) } catch {}
try { $fans = @(Get-CimInstance Win32_Fan -ErrorAction Stop | Select-Object Name,DesiredSpeed,Status) } catch {}
[pscustomobject]@{ temperatures = $temps; fans = $fans } | ConvertTo-Json -Compress -Depth 4
"""
    try:
        value = json.loads(_powershell(script, 15))
    except (TypeError, ValueError, RuntimeError):
        value = {}
    if not isinstance(value, dict):
        value = {}
    temperatures = value.get("temperatures") or []
    fans = value.get("fans") or []
    if isinstance(temperatures, dict):
        temperatures = [temperatures]
    if isinstance(fans, dict):
        fans = [fans]
    return {"temperatures": temperatures, "fans": fans}
