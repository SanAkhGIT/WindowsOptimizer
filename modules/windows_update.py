import base64
from core.process import run_executable


def _powershell(script, timeout=300):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable(
        "powershell.exe",
        ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded),
        timeout=timeout,
    )


def status():
    script = """
$ErrorActionPreference = 'Stop'
$services = Get-Service -Name wuauserv,bits,cryptsvc -ErrorAction SilentlyContinue |
  Select-Object Name, Status, StartType
$pending = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'
[pscustomobject]@{
  Services = $services
  RebootPending = $pending
} | ConvertTo-Json -Depth 4 -Compress
"""
    result = _powershell(script)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Windows Update status failed.")
    return result.stdout or "No Windows Update status returned."


def reset_components():
    script = r"""
$ErrorActionPreference = 'Stop'
$services = 'bits','wuauserv','cryptsvc'
foreach ($name in $services) {
  Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$sd = Join-Path $env:SystemRoot 'SoftwareDistribution'
$cat = Join-Path $env:SystemRoot 'System32catroot2'
if (Test-Path $sd) { Rename-Item -LiteralPath $sd -NewName ("SoftwareDistribution.WindowsOptimizer." + $stamp) -ErrorAction Stop }
if (Test-Path $cat) { Rename-Item -LiteralPath $cat -NewName ("catroot2.WindowsOptimizer." + $stamp) -ErrorAction Stop }
Start-Service -Name cryptsvc -ErrorAction SilentlyContinue
Start-Service -Name bits -ErrorAction SilentlyContinue
Start-Service -Name wuauserv -ErrorAction SilentlyContinue
'Windows Update components were reset by renaming caches; original folders remain available for recovery.'
"""
    result = _powershell(script, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Windows Update component reset failed.")
    return result.stdout or "Windows Update components reset."
