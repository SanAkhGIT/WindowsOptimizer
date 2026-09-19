from types import SimpleNamespace

import core.profile_execution as execution


def test_execute_approved_plan_runs_only_selected(monkeypatch, tmp_path):
    calls = []

    class Backup:
        def create(self):
            calls.append("backup")
            return tmp_path / "backup"

    tweak = SimpleNamespace(
        id="demo_tweak",
        apply=lambda: calls.append("tweak") or "changed",
        check=lambda: True,
    )
    profile = SimpleNamespace(id="gaming", version=3)

    monkeypatch.setattr(execution, "_tweak_map", lambda: {"demo_tweak": tweak})
    monkeypatch.setattr(execution, "CATALOG", [])
    monkeypatch.setattr(execution, "verify_tweak", lambda item: (True, "verified"))

    item = SimpleNamespace(
        kind="tweak",
        action="enable",
        identifier="demo_tweak",
        reason="test",
    )
    result = execution.execute_approved_plan(
        profile,
        [item],
        backup_manager=Backup(),
        receipt_root=tmp_path,
    )

    assert calls == ["backup", "tweak"]
    assert result.status == "VERIFIED"
    assert result.items[0].identifier == "demo_tweak"
    assert result.backup_path.endswith("backup")
    assert (tmp_path / "receipts").exists()


def test_execute_approved_plan_rejects_empty_selection():
    profile = SimpleNamespace(id="p", version=1)
    try:
        execution.execute_approved_plan(profile, [])
    except ValueError as exc:
        assert "No approved operations" in str(exc)
    else:
        raise AssertionError("Expected empty approval to be rejected.")


def test_execute_approved_plan_persists_rollback_keys(monkeypatch, tmp_path):
    class Backup:
        def create(self):
            return tmp_path / "backup"

    tweak = SimpleNamespace(
        id="demo_tweak",
        apply=lambda: "changed",
        check=lambda: True,
        rollback=None,
        metadata={
            "rollback_keys": (
                {"root": "HKCU", "key": r"Software\Demo", "value_name": "Enabled"},
            )
        },
    )
    profile = SimpleNamespace(id="demo", version=1)
    monkeypatch.setattr(execution, "_tweak_map", lambda: {"demo_tweak": tweak})
    monkeypatch.setattr(execution, "verify_tweak", lambda item: (True, "verified"))

    item = SimpleNamespace(kind="tweak", action="enable", identifier="demo_tweak", reason="test")
    result = execution.execute_approved_plan(
        profile, [item], backup_manager=Backup(), receipt_root=tmp_path
    )

    assert result.items[0].rollback_supported is True
    assert result.items[0].rollback_keys == (
        {"root": "HKCU", "key": r"Software\Demo", "value_name": "Enabled"},
    )



def test_failed_tweak_still_writes_receipt(monkeypatch, tmp_path):
    class Backup:
        def create(self):
            return tmp_path / "backup"

    tweak = SimpleNamespace(
        id="broken_tweak",
        apply=lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        check=lambda: False,
        rollback=None,
        metadata={"rollback_keys": ({"root": "HKCU", "key": r"Software\Demo", "value_name": "Enabled"},)},
    )
    profile = SimpleNamespace(id="demo", version=1)
    monkeypatch.setattr(execution, "_tweak_map", lambda: {"broken_tweak": tweak})

    item = SimpleNamespace(kind="tweak", action="enable", identifier="broken_tweak", reason="test")
    result = execution.execute_approved_plan(
        profile, [item], backup_manager=Backup(), receipt_root=tmp_path
    )

    assert result.status == "FAILED"
    assert result.items[0].status == "FAILED"
    assert result.items[0].rollback_keys == ()
    assert (tmp_path / "receipts").exists()
