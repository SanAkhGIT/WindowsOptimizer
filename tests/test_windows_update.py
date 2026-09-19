import modules.windows_update as windows_update


def test_update_controls_are_callable():
    for name in (
        "status",
        "pause_quality",
        "pause_feature",
        "resume_quality",
        "resume_feature",
        "set_driver_exclusion",
        "set_target_version",
        "clear_target_version",
        "reset_components",
    ):
        assert callable(getattr(windows_update, name))


def test_target_version_validation(monkeypatch):
    calls = []

    monkeypatch.setattr(windows_update, "_ensure_admin", lambda: None)
    monkeypatch.setattr(
        windows_update,
        "write_dword",
        lambda *args: calls.append(("dword", args)),
    )
    monkeypatch.setattr(
        windows_update,
        "write_string",
        lambda *args: calls.append(("string", args)),
    )

    windows_update.set_target_version("25H2")

    assert any(item[0] == "dword" for item in calls)
    assert any(item[0] == "string" and item[1][-1] == "25H2" for item in calls)


def test_target_version_rejects_invalid_labels():
    try:
        windows_update.set_target_version("11.0")
    except ValueError as exc:
        assert "release label" in str(exc)
    else:
        raise AssertionError("Expected invalid target version to be rejected.")


def test_reset_script_targets_catroot2(monkeypatch):
    class Result:
        returncode = 0
        stderr = ""
        stdout = "ok"

    captured = []
    monkeypatch.setattr(
        windows_update,
        "_powershell",
        lambda script, timeout=300: captured.append(script) or Result(),
    )

    assert windows_update.reset_components() == "ok"
    assert r"System32\catroot2" in captured[0]


def test_pause_quality_writes_timestamp_string(monkeypatch):
    calls = []
    monkeypatch.setattr(windows_update, "_ensure_admin", lambda: None)
    monkeypatch.setattr(windows_update, "write_string", lambda *args: calls.append(args))
    monkeypatch.setattr(windows_update, "write_dword", lambda *args: calls.append(("wrong", args)))
    result = windows_update.pause_quality()
    assert "maximum 35-day" in result
    assert calls and calls[0][-2] == "PauseQualityUpdatesStartTime"
    assert isinstance(calls[0][-1], str)
    assert calls[0][-1] != "1"


def test_pause_feature_writes_timestamp_string(monkeypatch):
    calls = []
    monkeypatch.setattr(windows_update, "_ensure_admin", lambda: None)
    monkeypatch.setattr(windows_update, "write_string", lambda *args: calls.append(args))
    windows_update.pause_feature()
    assert calls and calls[0][-2] == "PauseFeatureUpdatesStartTime"
    assert isinstance(calls[0][-1], str)
