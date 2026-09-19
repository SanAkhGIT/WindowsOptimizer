import winreg

from core.models import Tweak
from core.registry import read_value, write_dword

GAME_BAR = r"Software\Microsoft\GameBar"
GAME_DVR = r"Software\Microsoft\Windows\CurrentVersion\GameDVR"
GAME_CONFIG = r"System\GameConfigStore"


def game_on():
    value = read_value(winreg.HKEY_CURRENT_USER, GAME_BAR, "AutoGameModeEnabled")
    return value is not None and value[0] == 1


def dvr_off():
    capture = read_value(winreg.HKEY_CURRENT_USER, GAME_DVR, "AppCaptureEnabled")
    enabled = read_value(winreg.HKEY_CURRENT_USER, GAME_CONFIG, "GameDVR_Enabled")
    return (
        capture is not None and capture[0] == 0
        and enabled is not None and enabled[0] == 0
    )


def game_apply():
    write_dword(winreg.HKEY_CURRENT_USER, GAME_BAR, "AutoGameModeEnabled", 1)
    return "Windows Game Mode preference enabled."


def dvr_apply():
    write_dword(winreg.HKEY_CURRENT_USER, GAME_DVR, "AppCaptureEnabled", 0)
    write_dword(winreg.HKEY_CURRENT_USER, GAME_CONFIG, "GameDVR_Enabled", 0)
    return "Game DVR capture disabled for the current user."


def scan():
    return [
        Tweak(
            "game_mode",
            "Enable Windows Game Mode",
            "Gaming",
            "Enables Microsoft's built-in Game Mode preference.",
            "SAFE",
            not game_on(),
            True,
            False,
            "None",
            game_on,
            game_apply,
            metadata={
                "rollback_keys": (
                    {"root": "HKCU", "key": GAME_BAR, "value_name": "AutoGameModeEnabled"},
                )
            },
        ),
        Tweak(
            "game_dvr_off",
            "Disable Game DVR capture",
            "Gaming",
            "Stops background Game DVR capture if you do not record gameplay.",
            "CAUTION",
            False,
            True,
            False,
            "None",
            dvr_off,
            dvr_apply,
            metadata={
                "rollback_keys": (
                    {"root": "HKCU", "key": GAME_DVR, "value_name": "AppCaptureEnabled"},
                    {"root": "HKCU", "key": GAME_CONFIG, "value_name": "GameDVR_Enabled"},
                )
            },
        ),
    ]
