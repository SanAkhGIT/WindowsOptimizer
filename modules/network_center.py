from core.process import run_executable


def adapters():
    ps = r"""
Get-NetAdapter -ErrorAction SilentlyContinue |
  Select-Object Name,InterfaceDescription,Status,LinkSpeed,MacAddress |
  ConvertTo-Json -Depth 4 -Compress
"""
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-Command", ps],
        60,
    )
    if result.returncode:
        raise RuntimeError(result.stderr or "Network adapter inventory failed.")
    return result.stdout or "[]"


def configuration():
    ps = r"""
Get-NetIPConfiguration -ErrorAction SilentlyContinue |
  ForEach-Object {
    [pscustomobject]@{
      InterfaceAlias = $_.InterfaceAlias
      InterfaceDescription = $_.InterfaceDescription
      IPv4Address = @($_.IPv4Address | ForEach-Object { $_.IPAddress })
      IPv6Address = @($_.IPv6Address | ForEach-Object { $_.IPAddress })
      DNSServer = @($_.DNSServer.ServerAddresses)
      ProfileName = if ($_.NetProfile) { $_.NetProfile.Name } else { $null }
      NetworkCategory = if ($_.NetProfile) { [string]$_.NetProfile.NetworkCategory } else { $null }
    }
  } | ConvertTo-Json -Depth 5 -Compress
"""
    result = run_executable(
        "powershell.exe",
        ["-NoProfile", "-NonInteractive", "-Command", ps],
        60,
    )
    if result.returncode:
        raise RuntimeError(result.stderr or "Network configuration inventory failed.")
    return result.stdout or "[]"


def latency(host="1.1.1.1"):
    result = run_executable("ping.exe", ["-n", "4", host], 30)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr or "Ping failed.")
    return result.stdout or "No ping output."
