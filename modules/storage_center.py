"""Storage analysis and conservative cleanup operations."""

from dataclasses import dataclass
from pathlib import Path
import os
import shutil
import time
from core.process import run_executable

@dataclass(frozen=True)
class CleanupCandidate:
    id: str
    name: str
    path: str
    size_bytes: int
    description: str
    risk: str = "SAFE"

def _size(path, older_than_days=None):
    root = Path(path)
    if not root.exists(): return 0
    cutoff = time.time() - older_than_days * 86400 if older_than_days is not None else None
    total = 0
    try:
        for base, dirs, files in os.walk(root, topdown=True, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(base) / d).is_symlink()]
            for name in files:
                p = Path(base) / name
                try:
                    stat = p.stat()
                    if cutoff is None or stat.st_mtime < cutoff: total += stat.st_size
                except (OSError, PermissionError): pass
    except (OSError, PermissionError): pass
    return total

def system_drive():
    root = Path(os.environ.get("SystemDrive", "C:")) / os.sep
    usage = shutil.disk_usage(root)
    return {"total": usage.total, "used": usage.used, "free": usage.free}

def candidates():
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    temp = Path(os.environ.get("TEMP", local / "Temp"))
    items = [
        ("user_temp", "User temporary files", temp, "Files older than 48 hours; in-use files are skipped.", "SAFE"),
        ("crash_dumps", "Crash dumps", local / "CrashDumps", "Crash dumps older than 14 days.", "SAFE"),
        ("windows_update_downloads", "Windows Update download cache", windows / "SoftwareDistribution" / "Download", "Review before removing; Windows can recreate update cache files.", "CAUTION"),
    ]
    return [CleanupCandidate(i,n,str(p),_size(p,2 if i=="user_temp" else 14 if i=="crash_dumps" else None),d,r) for i,n,p,d,r in items]

def recycle_bin_status():
    script = r"""$items=@(Get-ChildItem -LiteralPath 'C:\$Recycle.Bin' -Force -Recurse -ErrorAction SilentlyContinue); [pscustomobject]@{Exists=Test-Path 'C:\$Recycle.Bin';Items=$items.Count;SizeBytes=[int64](($items|Measure-Object Length -Sum).Sum)}|ConvertTo-Json -Compress"""
    r=run_executable("powershell.exe",("-NoProfile","-NonInteractive","-Command",script),90)
    if r.returncode: raise RuntimeError(r.stderr or "Recycle Bin analysis failed.")
    return r.stdout or "{}"

def cleanup_temp():
    return _remove_older(Path(os.environ.get("TEMP",Path.home()/"AppData"/"Local"/"Temp")),48*3600)

def cleanup_crash_dumps():
    local=Path(os.environ.get("LOCALAPPDATA",Path.home()/"AppData"/"Local"))
    return _remove_older(local/"CrashDumps",14*86400)

def cleanup_update_downloads():
    windows=Path(os.environ.get("SystemRoot",r"C:\Windows"))
    return _remove_older(windows/"SoftwareDistribution"/"Download",0)

def empty_recycle_bin():
    r=run_executable("powershell.exe",("-NoProfile","-NonInteractive","-Command","Clear-RecycleBin -Force -ErrorAction Stop"),120)
    if r.returncode: raise RuntimeError(r.stderr or "Recycle Bin cleanup failed.")
    return r.stdout or "Recycle Bin emptied."

def open_storage_settings():
    r=run_executable("explorer.exe",("ms-settings:storagesense"),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to open Storage settings.")
    return "Opened Windows Storage settings."

def open_cleanup_recommendations():
    r=run_executable("explorer.exe",("ms-settings:storagerecommendations"),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to open Cleanup recommendations.")
    return "Opened Windows Cleanup recommendations."

def run_disk_cleanup():
    r=run_executable("cleanmgr.exe",("/LOWDISK",),120)
    if r.returncode: raise RuntimeError(r.stderr or "Disk Cleanup failed to start.")
    return "Started Windows Disk Cleanup."

def _remove_older(root, age_seconds):
    if not root.exists(): return f"Nothing to clean: {root}"
    cutoff=time.time()-age_seconds
    removed=reclaimed=errors=0
    try:
        for base,dirs,files in os.walk(root,topdown=True,followlinks=False):
            dirs[:]=[d for d in dirs if not (Path(base)/d).is_symlink()]
            for name in files:
                path=Path(base)/name
                try:
                    stat=path.stat()
                    if stat.st_mtime<=cutoff:
                        path.unlink(); removed+=1; reclaimed+=stat.st_size
                except (OSError,PermissionError): errors+=1
    except (OSError,PermissionError): errors+=1
    return f"Removed {removed} files; reclaimed {reclaimed/1024**2:.1f} MB; skipped {errors}."