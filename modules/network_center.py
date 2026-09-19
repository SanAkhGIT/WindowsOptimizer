from core.process import run_executable

def adapters():
    ps=r"Get-NetAdapter | Select-Object Name,InterfaceDescription,Status,LinkSpeed,MacAddress,ifIndex | ConvertTo-Json -Depth 4 -Compress"
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-Command",ps],60)
    if r.returncode:
        raise RuntimeError(r.stderr or "Network adapter inventory failed.")
    try:
        import json
        value=json.loads(r.stdout or "[]")
        return value if isinstance(value,list) else [value]
    except json.JSONDecodeError as exc:
        raise RuntimeError("Windows returned invalid adapter data.") from exc

def configuration():
    ps=r"Get-NetIPConfiguration | Select-Object InterfaceAlias,InterfaceIndex,IPv4Address,IPv6Address,DNSServer,NetProfile,IPv4DefaultGateway | ConvertTo-Json -Depth 5 -Compress"
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-Command",ps],60)
    if r.returncode:
        raise RuntimeError(r.stderr or "Network configuration inventory failed.")
    try:
        import json
        value=json.loads(r.stdout or "[]")
        return value if isinstance(value,list) else [value]
    except json.JSONDecodeError as exc:
        raise RuntimeError("Windows returned invalid network configuration data.") from exc

def latency(host="1.1.1.1"):
    r=run_executable("ping.exe",["-n","4",host],30)
    if r.returncode not in (0,1): raise RuntimeError(r.stderr or "Ping failed.")
    return r.stdout or "No ping output."
