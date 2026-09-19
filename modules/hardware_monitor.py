import json

from core.process import run_executable


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
    """Single PowerShell round-trip for high-frequency dashboard telemetry."""
    script = r"""
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1 Name,LoadPercentage,CurrentClockSpeed,MaxClockSpeed
$gpu = Get-CimInstance Win32_VideoController | Select-Object -First 1 Name,DriverVersion,AdapterRAM
$memory = Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize,FreePhysicalMemory
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$env:SystemDrive'" | Select-Object Size,FreeSpace
[pscustomobject]@{
    cpu = $cpu
    gpu = $gpu
    memory = $memory
    disk = $disk
} | ConvertTo-Json -Compress -Depth 4
"""
    value = json.loads(_powershell(script, 20))
    return value if isinstance(value, dict) else {}


def cpu():
    return _powershell(
        r"Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed,LoadPercentage,Manufacturer | ConvertTo-Json -Compress"
    )


def gpu():
    return _powershell(
        r"Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,DriverDate,CurrentHorizontalResolution,CurrentVerticalResolution | ConvertTo-Json -Compress"
    )


def memory():
    return _powershell(
        r"Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json -Compress"
    )


def drives():
    return _powershell(
        r"Get-PhysicalDisk | Select-Object FriendlyName,MediaType,Size,HealthStatus,OperationalStatus | ConvertTo-Json -Compress"
    )


def temperatures():
    return _powershell(
        r"Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object InstanceName,CurrentTemperature | ConvertTo-Json -Compress"
    )


def fans():
    return _powershell(
        r"Get-CimInstance Win32_Fan -ErrorAction SilentlyContinue | Select-Object Name,Status,DesiredSpeed,ActiveCooling | ConvertTo-Json -Compress"
    )


def drivers():
    return _powershell(
        r"Get-CimInstance Win32_PnPSignedDriver | Select-Object DeviceName,DriverVersion,DriverDate,Manufacturer,InfName,IsSigned | ConvertTo-Json -Compress",
        60,
    )


def summary():
    return {
        "cpu": cpu(),
        "gpu": gpu(),
        "memory": memory(),
        "drives": drives(),
        "temperatures": temperatures(),
        "fans": fans(),
        "drivers": drivers(),
    }
