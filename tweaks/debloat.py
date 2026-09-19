"""Windows debloat-oriented, reversible policy tweaks.

These are deliberately conservative: they change documented policy/settings
surfaces rather than deleting system components. AppX removal remains a
separate, exact-package operation in modules.appx.
"""
import winreg

from core.models import Tweak
from core.registry import delete_value, read_value, write_dword

TASKBAR_ADVANCED = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
DEVICE_METADATA = r"SOFTWARE\Policies\Microsoft\Windows\Device Metadata"


def _state(root, path, name, desired):
    value = read_value(root, path, name)
    if value is None:
        return "NOT APPLIED"
    return "APPLIED" if value[0] == desired else "CONFLICT"


def _apply(root, path, name, desired, label):
    current = read_value(root, path, name)
    if current is not None and current[0] != desired:
        return f"Existing {label} setting differs ({current[0]}); no change was made."
    if current is not None:
        return f"{label} was already configured."
    write_dword(root, path, name, desired)
    return f"{label} enabled."


def _rollback(root, path, name, desired, label):
    current = read_value(root, path, name)
    if current is None:
        return f"{label} is already at the Windows default."
    if current[0] != desired:
        return f"{label} was changed after this operation; it was not overwritten."
    delete_value(root, path, name)
    return f"{label} reset to Windows default."


def widgets_state():
    return _state(winreg.HKEY_CURRENT_USER, TASKBAR_ADVANCED, "TaskbarDa", 0)


def widgets_apply():
    return _apply(
        winreg.HKEY_CURRENT_USER,
        TASKBAR_ADVANCED,
        "TaskbarDa",
        0,
        "Widgets taskbar button",
    ) + " Explorer restart may be required."


def widgets_rollback():
    return _rollback(
        winreg.HKEY_CURRENT_USER,
        TASKBAR_ADVANCED,
        "TaskbarDa",
        0,
        "Widgets taskbar button",
    ) + " Explorer restart may be required."


def device_metadata_state():
    return _state(
        winreg.HKEY_LOCAL_MACHINE,
        DEVICE_METADATA,
        "PreventDeviceMetadataFromNetwork",
        1,
    )


def device_metadata_apply():
    return _apply(
        winreg.HKEY_LOCAL_MACHINE,
        DEVICE_METADATA,
        "PreventDeviceMetadataFromNetwork",
        1,
        "Device companion app installation",
    )


def device_metadata_rollback():
    return _rollback(
        winreg.HKEY_LOCAL_MACHINE,
        DEVICE_METADATA,
        "PreventDeviceMetadataFromNetwork",
        1,
        "Device companion app installation",
    )


def scan():
    return [
        Tweak(
            "widgets_off",
            "Disable Widgets taskbar button",
            "Debloat",
            "Hides the Widgets entry point without uninstalling the underlying Windows components.",
            "SAFE",
            True,
            True,
            False,
            "Explorer restart may be required.",
            lambda: widgets_state() == "APPLIED",
            widgets_apply,
            widgets_rollback,
            metadata={"state": widgets_state},
        ),
        Tweak(
            "device_companion_apps_off",
            "Prevent device companion app suggestions",
            "Debloat",
            "Prevents Windows from automatically obtaining device companion software from the network. Hardware drivers are not removed.",
            "SAFE",
            False,
            True,
            True,
            "None",
            lambda: device_metadata_state() == "APPLIED",
            device_metadata_apply,
            device_metadata_rollback,
            metadata={"state": device_metadata_state},
        ),
    ]
