from pathlib import Path
from datetime import datetime
import json
import winreg


BASE = Path.home() / "WindowsOptimizerBackups"


class BackupManager:
    def create(self):
        path = BASE / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        path.mkdir(parents=True, exist_ok=True)
        reg = {}
        checks = [
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
                "TaskbarAl",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Control Panel\Desktop",
                "WallPaper",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                "EnableTransparency",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\GameBar",
                "AutoGameModeEnabled",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\GameDVR",
                "AppCaptureEnabled",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"System\GameConfigStore",
                "GameDVR_Enabled",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo",
                "Enabled",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Privacy",
                "TailoredExperiencesWithDiagnosticDataEnabled",
            ),
            (
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced\TaskbarDeveloperSettings",
                "TaskbarEndTask",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Policies\Microsoft\Windows\CloudContent",
                "DisableWindowsConsumerFeatures",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Policies\Microsoft\Windows\System",
                "PublishUserActivities",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Policies\Microsoft\Windows\System",
                "UploadUserActivities",
            ),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager",
                "DisableWpbtExecution",
            ),
        ]
        for root, key, val in checks:
            try:
                with winreg.OpenKey(root, key, 0, winreg.KEY_READ) as handle:
                    reg[f"{root}:{key}:{val}"] = winreg.QueryValueEx(handle, val)[0]
            except FileNotFoundError:
                reg[f"{root}:{key}:{val}"] = None
        (path / "registry_snapshot.json").write_text(
            json.dumps(reg, indent=2, default=str),
            encoding="utf-8",
        )
        return path
