import ctypes
import platform
import psutil
import subprocess

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False

def _powershell(cmd):
    p = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", cmd],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20
    )
    return p.stdout.strip()

def get_system_info():
    windows = platform.platform()
    build = platform.version()
    cpu = platform.processor() or "Unknown"
    ram = round(psutil.virtual_memory().total / (1024**3), 1)
    try:
        name = _powershell("(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty Name)")
        if name:
            cpu = name
    except Exception:
        pass
    return {"windows": windows, "build": build, "cpu": cpu, "ram_gb": ram}
