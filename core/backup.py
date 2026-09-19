from pathlib import Path
from datetime import datetime
import json

from core.logging import get_logger

logger = get_logger("backup")

try:
    import winreg
except ImportError:  # pragma: no cover - Windows runtime only
    winreg = None


BASE = Path.home() / "WindowsOptimizerBackups"

if winreg is not None:
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
else:
    CHECKS = ()
    ROOTS = {}


def _require_windows():
    if winreg is None:
        raise RuntimeError("Registry backup is only available on Windows.")


def _serialise(value):
    if isinstance(value, bytes):
        return {"kind": "bytes", "value": value.hex()}
    return {"kind": "value", "value": value}


def _deserialise(data):
    if data.get("kind") == "bytes":
        return bytes.fromhex(data.get("value", ""))
    return data.get("value")


def _selector(entry):
    return (
        entry.get("root"),
        entry.get("key"),
        entry.get("value_name"),
    )


class BackupManager:
    def __init__(self, base=None):
        self.base = Path(base or BASE)

    def create(self):
        logger.info("Registry backup requested")
        _require_windows()
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
                    legacy[f"{root_name}:{key}:{value_name}"] = value
            except FileNotFoundError:
                legacy[f"{root_name}:{key}:{value_name}"] = None
            manifest.append(entry)

        (path / "registry_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (path / "registry_snapshot.json").write_text(
            json.dumps(legacy, indent=2, default=str),
            encoding="utf-8",
        )
        (path / "backup.json").write_text(
            json.dumps(
                {
                    "format_version": 2,
                    "kind": "WindowsOptimizer registry backup",
                    "created_utc": datetime.now().astimezone().isoformat(),
                    "entry_count": len(manifest),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        logger.info("Registry backup created | path=%s | entries=%s", path, len(manifest))
        return path

    def _load_manifest(self, path):
        manifest_path = Path(path) / "registry_manifest.json"
        if not manifest_path.exists():
            raise ValueError("This backup does not contain a restorable registry manifest.")
        entries = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(entries, list):
            raise ValueError("Registry manifest is invalid.")
        return entries

    def restore_entries(self, path, selectors):
        """Restore only the captured registry entries named by selectors.

        This is the operation-level recovery primitive. It intentionally does
        not restore the entire manifest, so a single rollback cannot silently
        overwrite unrelated settings.
        """
        _require_windows()
        wanted = {
            _selector(item) if isinstance(item, dict) else tuple(item)
            for item in selectors
        }
        entries = [
            entry for entry in self._load_manifest(path)
            if _selector(entry) in wanted
        ]
        if len(entries) != len(wanted):
            raise ValueError("The backup does not contain every requested rollback entry.")

        logger.info("Targeted registry restore requested | backup=%s | entries=%s", path, len(entries))
        restored = 0
        for entry in entries:
            root = ROOTS.get(entry.get("root"))
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
        logger.info("Targeted registry restore completed | backup=%s | restored=%s", path, restored)
        return restored

    def restore(self, path):
        return self.restore_entries(path, [
            _selector(entry) for entry in self._load_manifest(path)
        ])
