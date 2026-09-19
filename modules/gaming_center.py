"""Gaming diagnostics and conservative controls.

The module favors supported Windows settings and diagnostics over undocumented
performance tweaks. Changes that can alter graphics presentation are exposed
as diagnostics/settings shortcuts rather than forced registry edits.
"""

import base64
import json
from core.process import run_executable


def _ps(script, timeout=90):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable(
        "powershell.exe",
        ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded),
        timeout,
    )


def inventory():
    script = r"""
$gpu = @(Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
  Select-Object Name,DriverVersion,DriverDate,VideoProcessor,AdapterRAM,Status)
$game = [pscustomobject]@{
  GameMode = (Get-ItemPropertyValue -Path 'HKCU:\Software\Microsoft\GameBar' -Name AutoGameModeEnabled -ErrorAction SilentlyContinue)
  GameDVR = (Get-ItemPropertyValue -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR' -Name AppCaptureEnabled -ErrorAction SilentlyContinue)
  HAGSRaw = (Get-ItemPropertyValue -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers' -Name HwSchMode -ErrorAction SilentlyContinue)
}
$os = Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber
$plans = (powercfg /GETACTIVESCHEME) 2>$null
[pscustomobject]@{GPU=$gpu; Gaming=$game; OS=$os; ActivePowerPlan=$plans} |
  ConvertTo-Json -Depth 6 -Compress
"""
    result = _ps(script)
    if result.returncode:
        raise RuntimeError(result.stderr or "Gaming inventory failed.")
    return result.stdout or "{}"


def parsed_inventory():
    value = json.loads(inventory())
    return value if isinstance(value, dict) else {}


def open_graphics_settings():
    result = run_executable("explorer.exe", ("ms-settings:display-advancedgraphics"), 30)
    if result.returncode:
        raise RuntimeError(result.stderr or "Unable to open Windows Graphics settings.")
    return "Opened Windows Graphics settings."


def open_game_mode_settings():
    result = run_executable("explorer.exe", ("ms-settings:gaming-gamemode"), 30)
    if result.returncode:
        raise RuntimeError(result.stderr or "Unable to open Game Mode settings.")
    return "Opened Windows Game Mode settings."


def open_game_bar_settings():
    result = run_executable("explorer.exe", ("ms-settings:gaming-gamebar"), 30)
    if result.returncode:
        raise RuntimeError(result.stderr or "Unable to open Game Bar settings.")
    return "Opened Windows Game Bar settings."


def xbox_services():
    script = r"""
Get-Service -Name XblAuthManager,XboxNetApiSvc,XboxGipSvc,XboxLiveAuthManager,XboxGipSvc -ErrorAction SilentlyContinue |
  Select-Object Name,Status,StartType |
  Sort-Object Name -Unique |
  ConvertTo-Json -Compress
"""
    result = _ps(script)
    if result.returncode:
        raise RuntimeError(result.stderr or "Xbox service inventory failed.")
    return result.stdout or "[]"
