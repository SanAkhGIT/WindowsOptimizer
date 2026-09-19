"""Reversible current-user Run/RunOnce startup controls."""

import json
from pathlib import Path
import winreg

BACKUP_ROOT = Path.home() / "WindowsOptimizerBackups" / "startup"
RUN_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUNONCE_PATH = r"Software\Microsoft\Windows\CurrentVersion\RunOnce"

def _key_path(run_once=False):
    return RUNONCE_PATH if run_once else RUN_PATH

def _backup_file():
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    return BACKUP_ROOT / "startup_disabled.json"

def _load():
    path = _backup_file()
    if not path.exists(): return {}
    try: return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError): return {}

def _save(data):
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)
    _backup_file().write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def disable_user_run(name, run_once=False):
    if not name or any(c in name for c in "\r\n"):
        raise ValueError("Invalid startup value name.")
    path = _key_path(run_once)
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
        value, value_type = winreg.QueryValueEx(key, name)
        data = _load()
        backup_id = ("RunOnce:" if run_once else "Run:") + name
        data[backup_id] = {"name": name, "path": path, "value": value, "type": value_type}
        _save(data)
        winreg.DeleteValue(key, name)
    return f"Disabled current-user startup entry: {name}"

def restore_user_run(name, run_once=False):
    if not name or any(c in name for c in "\r\n"):
        raise ValueError("Invalid startup value name.")
    path = _key_path(run_once)
    backup_id = ("RunOnce:" if run_once else "Run:") + name
    data = _load()
    item = data.get(backup_id)
    if not item: raise RuntimeError(f"No saved startup backup exists for {name}.")
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_WRITE) as key:
        winreg.SetValueEx(key, name, 0, int(item["type"]), item["value"])
    del data[backup_id]
    _save(data)
    return f"Restored current-user startup entry: {name}"

def disabled_entries():
    return list(_load().values())
