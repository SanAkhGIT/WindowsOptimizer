from pathlib import Path
import os
import shutil
from dataclasses import dataclass

@dataclass(frozen=True)
class StorageItem:
    name: str
    path: str
    size_bytes: int

def _size(path):
    total = 0
    try:
        for root, dirs, files in os.walk(path, topdown=True, followlinks=False):
            dirs[:] = [d for d in dirs if not (Path(root) / d).is_symlink()]
            for name in files:
                try: total += (Path(root) / name).stat().st_size
                except (OSError, PermissionError): pass
    except (OSError, PermissionError): pass
    return total

def categories():
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    local = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    candidates = [
        ("Windows Temp", windows / "Temp"),
        ("User Temp", local / "Temp"),
        ("Crash Dumps", local / "CrashDumps"),
        ("Downloads", Path.home() / "Downloads"),
        ("Windows Update Download Cache", windows / "SoftwareDistribution" / "Download"),
    ]
    result, seen = [], set()
    for name, path in candidates:
        key = str(path).lower()
        if key in seen or not path.exists(): continue
        seen.add(key)
        result.append(StorageItem(name, str(path), _size(path)))
    return result

def system_drive():
    root = Path(os.environ.get("SystemDrive", "C:")) / os.sep
    usage = shutil.disk_usage(root)
    return {"total": usage.total, "used": usage.used, "free": usage.free}
