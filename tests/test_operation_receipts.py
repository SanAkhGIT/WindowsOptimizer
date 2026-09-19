from core.operation_receipts import (
    ReceiptItem, complete, load, new_receipt, save,
)


def test_receipt_round_trip(tmp_path):
    receipt = new_receipt("profile", "gaming", 2, tmp_path / "backup")
    finished = complete(receipt, [
        ReceiptItem("tweak", "game_mode", "enable", "VERIFIED", "ok", "APPLIED"),
    ])
    path = save(finished, tmp_path)
    loaded = load(path)
    assert loaded.receipt_id == receipt.receipt_id
    assert loaded.status == "VERIFIED"
    assert loaded.items[0].identifier == "game_mode"


def test_receipt_warning_state():
    receipt = new_receipt("profile")
    finished = complete(receipt, [
        ReceiptItem("app", "x", "install", "UNVERIFIED"),
    ])
    assert finished.status == "COMPLETED_WITH_WARNINGS"


def test_receipt_failure_state():
    receipt = new_receipt("profile")
    finished = complete(receipt, [
        ReceiptItem("feature", "x", "enable", "FAILED"),
    ])
    assert finished.status == "FAILED"



def test_manual_executor_receipt_records_backup_and_rollback(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from core.executor import Executor
    from core.operation_receipts import recent

    tweak = SimpleNamespace(
        id="demo",
        name="Demo",
        apply=lambda: "changed",
        check=lambda: True,
        rollback=None,
        metadata={
            "rollback_keys": (
                {"root": "HKCU", "key": r"Software\Demo", "value_name": "Enabled"},
            )
        },
    )
    monkeypatch.setattr("core.executor.verify_tweak", lambda item: (True, "verified"))

    log_dir = tmp_path / "logs"
    backup_path = tmp_path / "backup"
    backup_path.mkdir()
    results = Executor(log_dir=log_dir).apply([tweak], backup_path=backup_path)

    assert results[0].status == "VERIFIED"
    entries = recent(tmp_path, limit=5)
    assert entries
    _, receipt = entries[0]
    assert receipt.backup_path == str(backup_path)
    assert receipt.items[0].rollback_supported is True
    assert receipt.items[0].rollback_keys[0]["value_name"] == "Enabled"
