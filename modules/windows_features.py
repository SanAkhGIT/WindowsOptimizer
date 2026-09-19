import base64
import json
from dataclasses import dataclass

from core.process import run_executable


@dataclass(frozen=True)
class WindowsFeature:
    name: str
    display_name: str
    state: str
    restart_required: bool = False


def _powershell(script, timeout=180):
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return run_executable(
        "powershell.exe",
        ("-NoProfile", "-NonInteractive", "-EncodedCommand", encoded),
        timeout=timeout,
    )


def inventory():
    script = """
$ErrorActionPreference = 'Stop'
Get-WindowsOptionalFeature -Online |
  Select-Object FeatureName, DisplayName, State, RestartNeeded |
  Sort-Object FeatureName |
  ConvertTo-Json -Depth 3 -Compress
"""
    result = _powershell(script)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or "Windows feature inventory failed.")
    if not result.stdout:
        return []
    rows = json.loads(result.stdout)
    if not isinstance(rows, list):
        rows = [rows]
    return [
        WindowsFeature(
            name=str(row.get("FeatureName") or ""),
            display_name=str(row.get("DisplayName") or row.get("FeatureName") or ""),
            state=str(row.get("State") or ""),
            restart_required=bool(row.get("RestartNeeded")),
        )
        for row in rows
        if row.get("FeatureName")
    ]


def _validate_name(name):
    if not name or any(ch in name for ch in "*?;$|&"):
        raise ValueError("Feature names must be exact names returned by Windows inventory.")


def set_feature(name, enable):
    _validate_name(name)
    verb = "Enable" if enable else "Disable"
    all_switch = " -All" if enable else ""
    escaped = name.replace("'", "''")
    script = (
        "$ErrorActionPreference = 'Stop'; "
        f"{verb}-WindowsOptionalFeature -Online -FeatureName '{escaped}'"
        f"{all_switch} -NoRestart -ErrorAction Stop | "
        "Select-Object FeatureName, State, RestartNeeded | ConvertTo-Json -Compress"
    )
    result = _powershell(script, timeout=600)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or f"Unable to {verb.lower()} feature.")
    return result.stdout or f"{verb} operation completed."
