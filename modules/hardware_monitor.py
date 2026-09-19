import json
from core.process import run_executable

def _powershell(script, timeout=30):
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",script],timeout)
    if r.returncode: raise RuntimeError(r.stderr or "Hardware query failed.")
    return r.stdout or "[]"

def cpu():
    ps=r"Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed,CurrentClockSpeed,LoadPercentage,Manufacturer | ConvertTo-Json -Compress"
    return _powershell(ps)

def gpu():
    ps=r"Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM,DriverVersion,DriverDate,CurrentHorizontalResolution,CurrentVerticalResolution | ConvertTo-Json -Compress"
    return _powershell(ps)

def memory():
    ps=r"Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json -Compress"
    return _powershell(ps)

def drives():
    ps=r"Get-PhysicalDisk | Select-Object FriendlyName,MediaType,Size,HealthStatus,OperationalStatus | ConvertTo-Json -Compress"
    return _powershell(ps)

def temperatures():
    ps=r"Get-CimInstance MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object InstanceName,CurrentTemperature | ConvertTo-Json -Compress"
    return _powershell(ps)

def fans():
    ps=r"Get-CimInstance Win32_Fan -ErrorAction SilentlyContinue | Select-Object Name,Status,DesiredSpeed,ActiveCooling | ConvertTo-Json -Compress"
    return _powershell(ps)

def drivers():
    ps=r"Get-CimInstance Win32_PnPSignedDriver | Select-Object DeviceName,DriverVersion,DriverDate,Manufacturer,InfName,IsSigned | ConvertTo-Json -Compress"
    return _powershell(ps,60)

def summary():
    return {"cpu":cpu(),"gpu":gpu(),"memory":memory(),"drives":drives(),"temperatures":temperatures(),"fans":fans(),"drivers":drivers()}
