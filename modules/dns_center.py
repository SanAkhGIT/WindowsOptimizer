import base64
from core.process import run_executable

PRESETS = {
    "Automatic (DHCP)": None,
    "Cloudflare": ["1.1.1.1", "1.0.0.1"],
    "Google": ["8.8.8.8", "8.8.4.4"],
    "Quad9": ["9.9.9.9", "149.112.112.112"],
}

def _ps(script, timeout=90):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable("powershell.exe", ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded), timeout)

def inventory():
    r = _ps("Get-NetIPConfiguration -All | Select-Object InterfaceIndex,InterfaceAlias,IPv4Address,DNSServer | ConvertTo-Json -Depth 4 -Compress")
    if r.returncode: raise RuntimeError(r.stderr or "DNS inventory failed.")
    return r.stdout or "[]"

def set_preset(index, preset):
    if preset not in PRESETS: raise ValueError("Unknown DNS preset.")
    index = int(index)
    if not 1 <= index <= 65535: raise ValueError("Invalid interface index.")
    if PRESETS[preset] is None:
        script = f"Set-DnsClientServerAddress -InterfaceIndex {index} -ResetServerAddresses -PassThru | ConvertTo-Json -Compress"
    else:
        addresses = ",".join("'" + x + "'" for x in PRESETS[preset])
        script = f"Set-DnsClientServerAddress -InterfaceIndex {index} -ServerAddresses ({addresses}) -PassThru | ConvertTo-Json -Compress"
    r = _ps(script)
    if r.returncode: raise RuntimeError(r.stderr or "DNS change failed.")
    return r.stdout or f"DNS preset '{preset}' applied."

def flush():
    r = run_executable("ipconfig.exe", ("/flushdns",), 30)
    if r.returncode: raise RuntimeError(r.stderr or "DNS cache flush failed.")
    return r.stdout or "DNS cache flushed."
