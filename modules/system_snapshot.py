import json
import platform
import socket
from core.process import run_executable
from core.system_info import get_system_info
from modules.network_center import adapters, configuration

def _json_query(script, timeout=30):
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-Command",script],timeout)
    if r.returncode: return []
    try:
        value=json.loads(r.stdout or "[]")
        return value if isinstance(value,list) else [value]
    except json.JSONDecodeError:
        return []

def snapshot():
    info=get_system_info()
    return {
        "system":info,
        "hostname":socket.gethostname(),
        "platform":platform.platform(),
        "network_adapters":_json_query(adapters()),
        "network_configuration":_json_query(configuration()),
        "os_hotfixes":_json_query(r"Get-HotFix | Select-Object HotFixID,Description,InstalledOn | ConvertTo-Json -Compress"),
        "bios":_json_query(r"Get-CimInstance Win32_BIOS | Select-Object Manufacturer,SMBIOSBIOSVersion,ReleaseDate,SerialNumber | ConvertTo-Json -Compress"),
        "motherboard":_json_query(r"Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer,Product,Version | ConvertTo-Json -Compress"),
    }
