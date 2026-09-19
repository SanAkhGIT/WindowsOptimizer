from pathlib import Path
import ctypes
import os
import winreg

from PIL import Image
from core.models import Tweak
from core.registry import read_value

ASSET_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "WindowsOptimizer" / "Assets"
WALLPAPER_KEY = r"Control Panel\Desktop"


def black():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSET_DIR / "black-desktop.png"
    if not path.exists():
        Image.new("RGB", (3840, 2160), (0, 0, 0)).save(path, "PNG")
    return path


def state():
    value = read_value(winreg.HKEY_CURRENT_USER, WALLPAPER_KEY, "WallPaper")
    return value is not None and Path(str(value[0])).resolve() == black().resolve()


def apply():
    path = black()
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, WALLPAPER_KEY) as key:
        winreg.SetValueEx(key, "WallPaper", 0, winreg.REG_SZ, str(path))
    ctypes.windll.user32.SystemParametersInfoW(20, 0, str(path), 3)
    return "Desktop wallpaper set to pure black."


def scan_personalization():
    return [
        Tweak(
            "black_wallpaper",
            "Pure black desktop wallpaper",
            "UI",
            "Use an application-generated #000000 wallpaper.",
            "SAFE",
            False,
            True,
            False,
            "None",
            state,
            apply,
            metadata={
                "path": str(black()),
                "rollback_keys": (
                    {"root": "HKCU", "key": WALLPAPER_KEY, "value_name": "WallPaper"},
                ),
            },
        )
    ]
