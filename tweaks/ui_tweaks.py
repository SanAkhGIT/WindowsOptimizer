import winreg
from core.registry import read_value, write_dword

ADV = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
PERSONALIZE = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"

def scan_ui_tweaks():
    taskbar = read_value(winreg.HKEY_CURRENT_USER, ADV, "TaskbarAl")
    transparency = read_value(winreg.HKEY_CURRENT_USER, PERSONALIZE, "EnableTransparency")
    return [
        {"id":"taskbar_left","name":"Left-align taskbar","description":"Use the supported Windows 11 taskbar alignment value.","risk":"SAFE","recommended":taskbar is None or taskbar[0] != 0},
        {"id":"transparency_off","name":"Disable transparency","description":"Reduces transparency effects and visual overhead.","risk":"SAFE","recommended":transparency is None or transparency[0] != 0},
    ]

def apply_tweak(tweak):
    if tweak["id"] == "taskbar_left":
        write_dword(winreg.HKEY_CURRENT_USER, ADV, "TaskbarAl", 0)
        return "Applied. Explorer restart may be required."
    if tweak["id"] == "transparency_off":
        write_dword(winreg.HKEY_CURRENT_USER, PERSONALIZE, "EnableTransparency", 0)
        return "Applied."
    raise ValueError("Unsupported tweak")
