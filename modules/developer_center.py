"""Developer and remote-access diagnostics using supported Windows interfaces."""

import base64
import json
import os
from core.process import run_executable

def _command(exe, args=(), timeout=60):
    return run_executable(exe, args, timeout)

def inventory():
    script = r"""
$features = @(Get-WindowsOptionalFeature -Online -ErrorAction SilentlyContinue |
  Where-Object FeatureName -in @('Microsoft-Windows-Subsystem-Linux','VirtualMachinePlatform') |
  Select-Object FeatureName,State)
$ssh = @(Get-Service -Name sshd,ssh-agent -ErrorAction SilentlyContinue |
  Select-Object Name,Status,StartType)
$wsl = (& wsl.exe --status 2>&1 | Out-String).Trim()
$distros = (& wsl.exe --list --verbose 2>&1 | Out-String).Trim()
$pwsh = Get-Command pwsh.exe -ErrorAction SilentlyContinue
$dotnet = (& dotnet --info 2>&1 | Out-String).Trim()
$git = Get-Command git.exe -ErrorAction SilentlyContinue
$devMode = Get-ItemPropertyValue -Path 'HKLM:SOFTWAREMicrosoftWindowsCurrentVersionAppModelUnlock' -Name AllowDevelopmentWithoutDevLicense -ErrorAction SilentlyContinue
[pscustomobject]@{
  Features=$features
  SSH=$ssh
  WSLStatus=$wsl
  WSLDistros=$distros
  PowerShell7=if($pwsh){$pwsh.Source}else{$null}
  DotNetInfo=$dotnet
  Git=if($git){$git.Source}else{$null}
  DeveloperMode=$devMode
  ProgramData=$env:ProgramData
  UserProfile=$env:USERPROFILE
} | ConvertTo-Json -Depth 8 -Compress
"""
    encoded=base64.b64encode(script.encode("utf-16le")).decode("ascii")
    r=_command("powershell.exe",("-NoProfile","-NonInteractive","-EncodedCommand",encoded),90)
    if r.returncode: raise RuntimeError(r.stderr or "Developer inventory failed.")
    return r.stdout or "{}"

def parsed_inventory():
    value=json.loads(inventory())
    return value if isinstance(value,dict) else {}

def open_developer_settings():
    r=_command("explorer.exe",("ms-settings:developers"),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to open developer settings.")
    return "Opened Windows developer settings."

def open_optional_features():
    r=_command("explorer.exe",("ms-settings:optionalfeatures"),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to open Optional Features.")
    return "Opened Windows Optional Features."

def wsl_status():
    r=_command("wsl.exe",("--status",),60)
    if r.returncode and "not installed" not in (r.stdout+r.stderr).lower():
        raise RuntimeError(r.stderr or r.stdout or "WSL status failed.")
    return r.stdout or r.stderr or "WSL is not installed."

def wsl_distros():
    r=_command("wsl.exe",("--list","--verbose"),60)
    return r.stdout or r.stderr or "No WSL distributions found."

def install_wsl():
    return _command("wsl.exe",("--install","--no-launch"),300).stdout or "WSL installation command completed."

def ssh_status():
    r=_command("powershell.exe",("-NoProfile","-NonInteractive","-Command","Get-Service sshd,ssh-agent -ErrorAction SilentlyContinue | Select Name,Status,StartType | ConvertTo-Json -Compress"),60)
    if r.returncode: raise RuntimeError(r.stderr or "OpenSSH status failed.")
    return r.stdout or "OpenSSH services are not installed."

def start_sshd():
    r=_command("powershell.exe",("-NoProfile","-NonInteractive","-Command","Start-Service sshd -ErrorAction Stop"),60)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to start OpenSSH Server.")
    return "OpenSSH Server started."

def stop_sshd():
    r=_command("powershell.exe",("-NoProfile","-NonInteractive","-Command","Stop-Service sshd -ErrorAction Stop"),60)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to stop OpenSSH Server.")
    return "OpenSSH Server stopped."

def open_environment_settings():
    r=_command("rundll32.exe",("sysdm.cpl,EditEnvironmentVariables"),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to open environment variables.")
    return "Opened environment variables."

def open_terminal():
    for exe,args in (("wt.exe",()),("cmd.exe",())):
        r=_command(exe,args,30)
        if r.returncode == 0: return "Opened terminal."
    raise RuntimeError("Unable to open Windows Terminal or Command Prompt.")

def set_developer_mode(enabled):
    value="1" if enabled else "0"
    script=f'''Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" -Name AllowDevelopmentWithoutDevLicense -Type DWord -Value {value} -Force'''
    r=_command("powershell.exe",("-NoProfile","-NonInteractive","-Command",script),60)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to change Developer Mode.")
    return f"Developer Mode {'enabled' if enabled else 'disabled'}."
