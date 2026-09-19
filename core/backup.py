from pathlib import Path
from datetime import datetime
import json
import winreg

BASE = Path.home() / "WindowsOptimizerBackups"

class BackupManager:
    def create(self):
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path = BASE / stamp
        path.mkdir(parents=True, exist_ok=True)

        reg = {}
        checks = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl"),
            (winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "UserPreferencesMask"),
            (winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", "WallPaper"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize", "EnableTransparency"),
        ]
        for root, key, value in checks:
            try:
                with winreg.OpenKey(root, key, 0, winreg.KEY_READ) as k:
                    reg[f"{root}:{key}:{value}"] = winreg.QueryValueEx(k, value)[0]
            except FileNotFoundError:
                reg[f"{root}:{key}:{value}"] = None

        (path / "registry_snapshot.json").write_text(json.dumps(reg, indent=2, default=str), encoding="utf-8")
        return path
