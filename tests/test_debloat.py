import winreg

import tweaks.debloat as debloat


def test_widgets_state_defaults_to_not_applied(monkeypatch):
    monkeypatch.setattr(debloat, "read_value", lambda *args: None)
    assert debloat.widgets_state() == "NOT APPLIED"


def test_widgets_apply_writes_taskbar_setting(monkeypatch):
    calls = []
    monkeypatch.setattr(debloat, "read_value", lambda *args: None)
    monkeypatch.setattr(debloat, "write_dword", lambda *args: calls.append(args))
    message = debloat.widgets_apply()
    assert calls == [(winreg.HKEY_CURRENT_USER, debloat.TASKBAR_ADVANCED, "TaskbarDa", 0)]
    assert "Widgets" in message
    debloat._CHANGED.clear()


def test_widgets_rollback_only_removes_our_setting(monkeypatch):
    calls = []
    debloat._CHANGED.add(
        (winreg.HKEY_CURRENT_USER, debloat.TASKBAR_ADVANCED, "TaskbarDa")
    )
    monkeypatch.setattr(debloat, "read_value", lambda *args: (0, winreg.REG_DWORD))
    monkeypatch.setattr(debloat, "delete_value", lambda *args: calls.append(args))
    message = debloat.widgets_rollback()
    assert calls == [(winreg.HKEY_CURRENT_USER, debloat.TASKBAR_ADVANCED, "TaskbarDa")]
    assert "reset" in message


def test_widgets_rollback_does_not_delete_preexisting_setting(monkeypatch):
    debloat._CHANGED.clear()
    monkeypatch.setattr(debloat, "read_value", lambda *args: (0, winreg.REG_DWORD))
    calls = []
    monkeypatch.setattr(debloat, "delete_value", lambda *args: calls.append(args))
    message = debloat.widgets_rollback()
    assert calls == []
    assert "not changed" in message


def test_device_companion_tweak_is_admin_only():
    tweak = next(item for item in debloat.scan() if item.id == "device_companion_apps_off")
    assert tweak.requires_admin is True
    assert tweak.reversible is True
