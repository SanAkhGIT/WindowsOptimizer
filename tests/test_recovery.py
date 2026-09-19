from types import SimpleNamespace

import core.recovery as recovery


def test_rollback_tweak_uses_declared_inverse(monkeypatch, tmp_path):
    calls = []

    tweak = SimpleNamespace(
        id="demo",
        rollback=lambda: calls.append("rollback") or "restored",
    )
    receipt = recovery.complete(
        recovery.new_receipt("profile"),
        [recovery.ReceiptItem(
            "tweak", "demo", "enable", "VERIFIED",
            "changed", "verified", True,
        )],
    )
    path = recovery.save(receipt, tmp_path)
    monkeypatch.setattr(recovery, "all_tweaks", lambda: [tweak])

    result = recovery.rollback_receipt_item(path, 0, receipt_root=tmp_path)

    assert calls == ["rollback"]
    assert result.item.status == "ROLLED_BACK"


def test_rollback_rejects_unsupported_operation(tmp_path):
    receipt = recovery.complete(
        recovery.new_receipt("profile"),
        [recovery.ReceiptItem(
            "app", "demo", "install", "VERIFIED",
            "installed", "verified", False,
        )],
    )
    path = recovery.save(receipt, tmp_path)
    try:
        recovery.rollback_receipt_item(path, 0, receipt_root=tmp_path)
    except ValueError as exc:
        assert "safe operation-level rollback" in str(exc)
    else:
        raise AssertionError("Expected unsupported rollback to be rejected.")
