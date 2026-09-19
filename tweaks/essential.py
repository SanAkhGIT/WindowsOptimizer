import winreg

from core.models import Tweak
from core.registry import delete_value, read_value, write_dword


SYSTEM_POLICY = r"SOFTWARE\Policies\Microsoft\Windows"
CLOUD_CONTENT = SYSTEM_POLICY + r"\CloudContent"
SYSTEM_OS = SYSTEM_POLICY + r"\System"
PRIVACY = r"Software\Microsoft\Windows\CurrentVersion\Privacy"
ADVANCED = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"


def _state(root, path, name, desired):
    value = read_value(root, path, name)
    if value is None:
        return "NOT APPLIED"
    return "APPLIED" if value[0] == desired else "CONFLICT"


def _policy_apply(root, path, name, desired, label):
    current = read_value(root, path, name)
    if current is not None and current[0] != desired:
        return f"Existing {label} policy differs ({current[0]}); no change was made."
    write_dword(root, path, name, desired)
    return f"{label} enabled."


def _policy_rollback(root, path, name, desired, label):
    current = read_value(root, path, name)
    if current is None:
        return f"{label} policy was already not configured."
    if current[0] != desired:
        return f"{label} policy was not changed by this operation."
    delete_value(root, path, name)
    return f"{label} policy reset to Windows default (not configured)."


def _consumer_state():
    return _state(
        winreg.HKEY_LOCAL_MACHINE,
        CLOUD_CONTENT,
        "DisableWindowsConsumerFeatures",
        1,
    )


def _consumer_apply():
    return _policy_apply(
        winreg.HKEY_LOCAL_MACHINE,
        CLOUD_CONTENT,
        "DisableWindowsConsumerFeatures",
        1,
        "Microsoft consumer experiences",
    )


def _consumer_rollback():
    return _policy_rollback(
        winreg.HKEY_LOCAL_MACHINE,
        CLOUD_CONTENT,
        "DisableWindowsConsumerFeatures",
        1,
        "Microsoft consumer experiences",
    )


def _activity_state():
    publish = _state(winreg.HKEY_LOCAL_MACHINE, SYSTEM_OS, "PublishUserActivities", 0)
    upload = _state(winreg.HKEY_LOCAL_MACHINE, SYSTEM_OS, "UploadUserActivities", 0)
    if publish == "CONFLICT" or upload == "CONFLICT":
        return "CONFLICT"
    if publish == "APPLIED" and upload == "APPLIED":
        return "APPLIED"
    return "NOT APPLIED"


def _activity_apply():
    names = ("PublishUserActivities", "UploadUserActivities")
    conflicts = [
        name
        for name in names
        if _state(winreg.HKEY_LOCAL_MACHINE, SYSTEM_OS, name, 0) == "CONFLICT"
    ]
    if conflicts:
        return "Existing activity-history policies differ (" + ", ".join(conflicts) + "); no changes were made."
    for name in names:
        _policy_apply(
            winreg.HKEY_LOCAL_MACHINE,
            SYSTEM_OS,
            name,
            0,
            name,
        )
    return "Activity history publishing and upload disabled."


def _activity_rollback():
    messages = []
    for name in ("PublishUserActivities", "UploadUserActivities"):
        messages.append(
            _policy_rollback(
                winreg.HKEY_LOCAL_MACHINE,
                SYSTEM_OS,
                name,
                0,
                name,
            )
        )
    return " ".join(messages)


def _tailored_state():
    return _state(
        winreg.HKEY_CURRENT_USER,
        PRIVACY,
        "TailoredExperiencesWithDiagnosticDataEnabled",
        0,
    )


def _tailored_apply():
    return _policy_apply(
        winreg.HKEY_CURRENT_USER,
        PRIVACY,
        "TailoredExperiencesWithDiagnosticDataEnabled",
        0,
        "Tailored experiences",
    )


def _tailored_rollback():
    delete_value(
        winreg.HKEY_CURRENT_USER,
        PRIVACY,
        "TailoredExperiencesWithDiagnosticDataEnabled",
    )
    return "Tailored experiences policy reset to Windows default."


def _end_task_state():
    return _state(
        winreg.HKEY_CURRENT_USER,
        ADVANCED + r"\TaskbarDeveloperSettings",
        "TaskbarEndTask",
        1,
    )


def _end_task_apply():
    return _policy_apply(
        winreg.HKEY_CURRENT_USER,
        ADVANCED + r"\TaskbarDeveloperSettings",
        "TaskbarEndTask",
        1,
        "Taskbar End Task",
    )


def _end_task_rollback():
    delete_value(
        winreg.HKEY_CURRENT_USER,
        ADVANCED + r"\TaskbarDeveloperSettings",
        "TaskbarEndTask",
    )
    return "Taskbar End Task reset to Windows default."


def _wpbt_state():
    return _state(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\Session Manager",
        "DisableWpbtExecution",
        1,
    )


def _wpbt_apply():
    return _policy_apply(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\Session Manager",
        "DisableWpbtExecution",
        1,
        "WPBT execution policy",
    ) + " A reboot may be required."


def _wpbt_rollback():
    delete_value(
        winreg.HKEY_LOCAL_MACHINE,
        r"SYSTEM\CurrentControlSet\Control\Session Manager",
        "DisableWpbtExecution",
    )
    return "WPBT policy reset to Windows default. A reboot may be required."


def scan():
    return [
        Tweak(
            "consumer_features_off",
            "Disable Microsoft consumer experiences",
            "Essential Tweaks",
            "Stops policy-controlled consumer suggestions and promoted app experiences.",
            "SAFE",
            True,
            True,
            True,
            "None",
            lambda: _consumer_state() == "APPLIED",
            _consumer_apply,
            _consumer_rollback,
            metadata={"state": _consumer_state},
        ),
        Tweak(
            "activity_history_off",
            "Disable Windows activity history publishing",
            "Privacy",
            "Stops Windows from publishing and uploading User Activities through the documented policy controls.",
            "SAFE",
            True,
            True,
            True,
            "None",
            lambda: _activity_state() == "APPLIED",
            _activity_apply,
            _activity_rollback,
            metadata={"state": _activity_state},
        ),
        Tweak(
            "tailored_experiences_off",
            "Disable tailored experiences",
            "Privacy",
            "Stops Windows from using diagnostic data to personalize experiences for the current user.",
            "SAFE",
            True,
            True,
            False,
            "None",
            lambda: _tailored_state() == "APPLIED",
            _tailored_apply,
            _tailored_rollback,
            metadata={"state": _tailored_state},
        ),
        Tweak(
            "taskbar_end_task",
            "Enable End Task on the taskbar",
            "UI",
            "Adds End Task to the taskbar context menu for supported Windows 11 builds.",
            "SAFE",
            False,
            True,
            False,
            "Explorer restart may be required.",
            lambda: _end_task_state() == "APPLIED",
            _end_task_apply,
            _end_task_rollback,
            metadata={"state": _end_task_state},
        ),
        Tweak(
            "wpbt_off",
            "Disable Windows Platform Binary Table (WPBT)",
            "Advanced",
            "Prevents OEM-provided WPBT programs from executing at boot. This is an advanced system-policy change and may affect OEM security or management software.",
            "CAUTION",
            False,
            True,
            True,
            "Reboot required.",
            lambda: _wpbt_state() == "APPLIED",
            _wpbt_apply,
            _wpbt_rollback,
            metadata={"state": _wpbt_state},
        ),
    ]
