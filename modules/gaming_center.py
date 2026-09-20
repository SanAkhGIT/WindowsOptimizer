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
  GameMode = (Get-ItemPropertyValue -Path 'HKCU:\\Software\\Microsoft\\GameBar' -Name AutoGameModeEnabled -ErrorAction SilentlyContinue)
  GameDVR = (Get-ItemPropertyValue -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR' -Name AppCaptureEnabled -ErrorAction SilentlyContinue)
  HAGSRaw = (Get-ItemPropertyValue -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers' -Name HwSchMode -ErrorAction SilentlyContinue)
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


def _open_settings(uri, label):
    import os
    if not hasattr(os, "startfile"):
        raise RuntimeError("Windows Settings shortcuts are only available on Windows.")
    try:
        os.startfile(uri)
    except OSError as exc:
        raise RuntimeError(f"Unable to open {label}: {exc}") from exc
    return f"Opened {label}."

def open_graphics_settings():
    return _open_settings("ms-settings:display-advancedgraphics", "Windows Graphics settings")

def open_game_mode_settings():
    return _open_settings("ms-settings:gaming-gamemode", "Windows Game Mode settings")

def open_game_bar_settings():
    return _open_settings("ms-settings:gaming-gamebar", "Windows Game Bar settings")

def xbox_services():
    script = r"""
$names = @("XblAuthManager","XboxNetApiSvc","XboxGipSvc","XboxLiveAuthManager")
Get-CimInstance Win32_Service -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -in $names } |
  Select-Object Name,State,StartMode |
  Sort-Object Name -Unique |
  ConvertTo-Json -Compress
"""
    result = _ps(script)
    if result.returncode:
        raise RuntimeError(result.stderr or "Xbox service inventory failed.")
    return result.stdout or "[]"
