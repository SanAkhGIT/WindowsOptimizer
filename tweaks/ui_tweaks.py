import winreg

from core.models import Tweak
from core.registry import read_value, write_dword

ADV = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
PERSONALIZE = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"


def left_state():
    value = read_value(winreg.HKEY_CURRENT_USER, ADV, "TaskbarAl")
    return value is not None and value[0] == 0


def trans_state():
    value = read_value(winreg.HKEY_CURRENT_USER, PERSONALIZE, "EnableTransparency")
    return value is not None and value[0] == 0


def left():
    write_dword(winreg.HKEY_CURRENT_USER, ADV, "TaskbarAl", 0)
    return "Taskbar alignment set to left."


def trans():
    write_dword(winreg.HKEY_CURRENT_USER, PERSONALIZE, "EnableTransparency", 0)
    return "Transparency disabled."


def scan_ui_tweaks():
    return [
        Tweak(
            "taskbar_left",
            "Left-align taskbar",
            "UI",
            "Use the Windows 11 taskbar alignment setting.",
            "SAFE",
            not left_state(),
            True,
            False,
            "Explorer restart may be required.",
            left_state,
            left,
            metadata={
                "rollback_keys": (
                    {"root": "HKCU", "key": ADV, "value_name": "TaskbarAl"},
                )
            },
        ),
        Tweak(
            "transparency_off",
            "Disable transparency",
            "Performance",
            "Reduce transparency effects for a simpler desktop composition.",
            "SAFE",
            not trans_state(),
            True,
            False,
            "None",
            trans_state,
            trans,
            metadata={
                "rollback_keys": (
                    {"root": "HKCU", "key": PERSONALIZE, "value_name": "EnableTransparency"},
                )
            },
        ),
    ]
