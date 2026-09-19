import json

from core.operation_receipts import load


def test_receipt_without_new_rollback_metadata_still_loads(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text(
        json.dumps(
            {
                "receipt_version": 1,
                "receipt_id": "legacy",
                "created_utc": "2026-09-19T00:00:00+00:00",
                "source": "profile",
                "profile_id": "demo",
                "profile_version": 1,
                "backup_path": None,
                "status": "VERIFIED",
                "items": [
                    {
                        "kind": "tweak",
                        "identifier": "demo",
                        "action": "enable",
                        "status": "VERIFIED",
                        "message": "changed",
                        "verification": "verified",
                        "rollback_supported": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    receipt = load(path)

    assert receipt.items[0].rollback_supported is True
    assert receipt.items[0].rollback_keys == ()
