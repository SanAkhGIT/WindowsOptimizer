from core.process import run_executable

def adapters():
    ps=r"Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed,MacAddress | ConvertTo-Json -Compress"
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-Command",ps],60)
    if r.returncode: raise RuntimeError(r.stderr or "Network adapter inventory failed.")
    return r.stdout or "[]"

def configuration():
    ps=r"Get-NetIPConfiguration | Select-Object InterfaceAlias,IPv4Address,IPv6Address,DNSServer,NetProfile | ConvertTo-Json -Compress"
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-Command",ps],60)
    if r.returncode: raise RuntimeError(r.stderr or "Network configuration inventory failed.")
    return r.stdout or "[]"

def latency(host="1.1.1.1"):
    r=run_executable("ping.exe",["-n","4",host],30)
    if r.returncode not in (0,1): raise RuntimeError(r.stderr or "Ping failed.")
    return r.stdout or "No ping output."
