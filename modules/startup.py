from core.process import run_executable

def inventory():
    ps = r"Get-CimInstance Win32_StartupCommand | Select-Object Name,Command,Location,User | ConvertTo-Json -Compress"
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",ps],60)
    if r.returncode: raise RuntimeError(r.stderr or "Startup inventory failed.")
    return r.stdout or "[]"
