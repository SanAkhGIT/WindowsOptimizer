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
