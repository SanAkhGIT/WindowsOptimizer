"""Windows Update inventory, repair, and conservative policy controls.

Policy controls use the Windows Update client policy registry locations
documented by Microsoft. They are explicit operations; no automatic update
blocking is performed.
"""
from __future__ import annotations

import re
import base64
import winreg
from datetime import date

from core.process import run_executable
from core.registry import read_value, write_dword, write_string, delete_value

POLICY = r"SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
PAUSE_SETTINGS = r"SOFTWARE\Microsoft\WindowsUpdate\UpdatePolicy\Settings"


def _powershell(script, timeout=300):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable(
        "powershell.exe",
        ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded),
        timeout=timeout,
    )


def status():
    script = r"""
$ErrorActionPreference = 'Stop'
$names = 'wuauserv','bits','cryptsvc'
$services = Get-Service -Name $names -ErrorAction SilentlyContinue |
  Select-Object Name, Status, StartType
$pending = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending'
$updatePending = Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired'
$policy = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate' -ErrorAction SilentlyContinue
$settings = Get-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UpdatePolicy\Settings' -ErrorAction SilentlyContinue
[pscustomobject]@{
  Services = $services
  RebootPending = ($pending -or $updatePending)
  PauseFeatureStart = $policy.PauseFeatureUpdatesStartTime
  PauseQualityStart = $policy.PauseQualityUpdatesStartTime
  PauseFeatureStatus = $settings.PausedFeatureStatus
  PauseQualityStatus = $settings.PausedQualityStatus
  TargetReleaseVersion = $policy.TargetReleaseVersion
  TargetReleaseVersionInfo = $policy.TargetReleaseVersionInfo
  ProductVersion = $policy.ProductVersion
  ExcludeWUDriversInQualityUpdate = $policy.ExcludeWUDriversInQualityUpdate
} | ConvertTo-Json -Depth 5 -Compress
"""
    result = _powershell(script)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Windows Update status failed.")
    return result.stdout or "No Windows Update status returned."


def _ensure_admin():
    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            raise PermissionError("Administrator access is required.")
    except AttributeError as exc:
        raise RuntimeError("Windows Update policy controls require Windows.") from exc


def _write_policy_string(name, value):
    _ensure_admin()
    write_string(winreg.HKEY_LOCAL_MACHINE, POLICY, name, value)


def _delete_policy_value(name):
    _ensure_admin()
    delete_value(winreg.HKEY_LOCAL_MACHINE, POLICY, name)


def pause_quality():
    _ensure_admin()
    start = date.today().isoformat()
    write_string(
        winreg.HKEY_LOCAL_MACHINE,
        POLICY,
        "PauseQualityUpdatesStartTime",
        start,
    )
    return (
        f"Quality updates paused from {start}; Windows documents a maximum "
        "35-day pause window."
    )


def pause_feature():
    _ensure_admin()
    start = date.today().isoformat()
    write_string(
        winreg.HKEY_LOCAL_MACHINE,
        POLICY,
        "PauseFeatureUpdatesStartTime",
        start,
    )
    return (
        f"Feature updates paused from {start}; Windows documents a maximum "
        "35-day pause window."
    )


def resume_quality():
    _delete_policy_value("PauseQualityUpdatesStartTime")
    return "Quality update pause policy cleared."


def resume_feature():
    _delete_policy_value("PauseFeatureUpdatesStartTime")
    return "Feature update pause policy cleared."


def set_driver_exclusion(enabled=True):
    _ensure_admin()
    if enabled:
        write_dword(winreg.HKEY_LOCAL_MACHINE, POLICY, "ExcludeWUDriversInQualityUpdate", 1)
        return "Driver packages are excluded from normal Windows Update quality-update delivery where the policy applies."
    delete_value(winreg.HKEY_LOCAL_MACHINE, POLICY, "ExcludeWUDriversInQualityUpdate")
    return "Windows Update driver-exclusion policy cleared."


def set_target_version(version, product="Windows 11"):
    version = str(version).strip()
    if not re.fullmatch(r"\d{2}H[12]", version.upper()):
        raise ValueError("Target version must use a Windows release label such as 25H2.")
    _ensure_admin()
    write_dword(winreg.HKEY_LOCAL_MACHINE, POLICY, "TargetReleaseVersion", 1)
    write_string(winreg.HKEY_LOCAL_MACHINE, POLICY, "TargetReleaseVersionInfo", version)
    write_string(winreg.HKEY_LOCAL_MACHINE, POLICY, "ProductVersion", product)
    return f"Target feature update policy set to {product} {version}."


def clear_target_version():
    _ensure_admin()
    for name in ("TargetReleaseVersion", "TargetReleaseVersionInfo", "ProductVersion"):
        delete_value(winreg.HKEY_LOCAL_MACHINE, POLICY, name)
    return "Target feature update policy cleared."


def reset_components():
    script = r"""
$ErrorActionPreference = 'Stop'
$services = 'bits','wuauserv','cryptsvc'
$renamed = @()
try {
  foreach ($name in $services) {
    Stop-Service -Name $name -Force -ErrorAction SilentlyContinue
  }
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  $sd = Join-Path $env:SystemRoot 'SoftwareDistribution'
  $cat = Join-Path $env:SystemRoot 'System32\catroot2'
  if (Test-Path $sd) {
    $newSd = "SoftwareDistribution.WindowsOptimizer." + $stamp
    Rename-Item -LiteralPath $sd -NewName $newSd -ErrorAction Stop
    $renamed += (Join-Path $env:SystemRoot $newSd)
  }
  if (Test-Path $cat) {
    $newCat = "catroot2.WindowsOptimizer." + $stamp
    Rename-Item -LiteralPath $cat -NewName $newCat -ErrorAction Stop
    $renamed += (Join-Path $env:SystemRoot 'System32' $newCat)
  }
}
finally {
  Start-Service -Name cryptsvc -ErrorAction SilentlyContinue
  Start-Service -Name bits -ErrorAction SilentlyContinue
  Start-Service -Name wuauserv -ErrorAction SilentlyContinue
}
[pscustomobject]@{
  Message = 'Windows Update caches were renamed; original folders were retained.'
  RetainedPaths = $renamed
} | ConvertTo-Json -Depth 3 -Compress
"""
    result = _powershell(script, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Windows Update component reset failed.")
    return result.stdout or "Windows Update components reset."
