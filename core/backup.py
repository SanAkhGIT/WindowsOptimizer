from pathlib import Path
from datetime import datetime
import json
import winreg


BASE = Path.home() / "WindowsOptimizerBackups"


CHECKS = (
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Control Panel\Desktop", "WallPaper"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\GameBar", "AutoGameModeEnabled"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"System\GameConfigStore", "GameDVR_Enabled"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo", "Enabled"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled"),
    (winreg.HKEY_CURRENT_USER, "HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\TaskbarDeveloperSettings", "TaskbarEndTask"),
    (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"SOFTWARE\Policies\Microsoft\Windows\CloudContent", "DisableWindowsConsumerFeatures"),
    (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "PublishUserActivities"),
    (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"SOFTWARE\Policies\Microsoft\Windows\System", "UploadUserActivities"),
    (winreg.HKEY_LOCAL_MACHINE, "HKLM", r"SYSTEM\CurrentControlSet\Control\Session Manager", "DisableWpbtExecution"),
)

ROOTS = {
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
}


def _serialise(value):
    if isinstance(value, bytes):
        return {"kind": "bytes", "value": value.hex()}
    return {"kind": "value", "value": value}


def _deserialise(data):
    if data.get("kind") == "bytes":
        return bytes.fromhex(data.get("value", ""))
    return data.get("value")


class BackupManager:
    def __init__(self, base=None):
        self.base = Path(base or BASE)

    def create(self):
        path = self.base / datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        path.mkdir(parents=True, exist_ok=False)

        legacy = {}
        manifest = []
        for root, root_name, key, value_name in CHECKS:
            entry = {
                "root": root_name,
                "key": key,
                "value_name": value_name,
                "present": False,
            }
            try:
                with winreg.OpenKey(root, key, 0, winreg.KEY_READ) as handle:
                    value, value_type = winreg.QueryValueEx(handle, value_name)
                    entry.update({
                        "present": True,
                        "value": _serialise(value),
                        "value_type": value_type,
                    })
                    legacy[f"{root}:{key}:{value_name}"] = value
            except FileNotFoundError:
                legacy[f"{root}:{key}:{value_name}"] = None
            manifest.append(entry)

        (path / "registry_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (path / "registry_snapshot.json").write_text(
            json.dumps(legacy, indent=2, default=str),
            encoding="utf-8",
        )
        return path

    def restore(self, path):
        path = Path(path)
        manifest_path = path / "registry_manifest.json"
        if not manifest_path.exists():
            raise ValueError("This backup does not contain a restorable registry manifest.")

        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
        restored = 0
        for entry in entries:
            root_name = entry.get("root")
            root = ROOTS.get(root_name)
            key = entry.get("key")
            value_name = entry.get("value_name")
            if root is None or not key or not value_name:
                raise ValueError("Backup contains an invalid registry entry.")

            if entry.get("present"):
                with winreg.CreateKeyEx(root, key, 0, winreg.KEY_SET_VALUE) as handle:
                    winreg.SetValueEx(
                        handle,
                        value_name,
                        0,
                        int(entry.get("value_type", winreg.REG_SZ)),
                        _deserialise(entry.get("value", {})),
                    )
            else:
                try:
                    with winreg.OpenKey(root, key, 0, winreg.KEY_SET_VALUE) as handle:
                        winreg.DeleteValue(handle, value_name)
                except FileNotFoundError:
                    pass
            restored += 1
        return restored
