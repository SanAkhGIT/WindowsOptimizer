"""Recovery helpers for completed WindowsOptimizer operations.

Recovery is deliberately capability-based. An operation is rollbackable only
when its underlying Windows change has a reliable inverse and the execution
receipt recorded that capability. Registry snapshots remain a separate
recovery aid and are not silently replayed as a generic undo mechanism.
"""
from __future__ import annotations

from dataclasses import dataclass

from core.operation_receipts import ReceiptItem, load, complete, save
from core.backup import BackupManager
from modules.catalog import all_tweaks
from modules.windows_features import set_feature


@dataclass(frozen=True)
class RecoveryResult:
    receipt_path: str
    status: str
    item: ReceiptItem


def rollback_receipt_item(receipt_path, item_index, *, receipt_root=None):
    receipt = load(receipt_path)
    if item_index < 0 or item_index >= len(receipt.items):
        raise IndexError("Receipt item index is out of range.")

    item = receipt.items[item_index]
    if not item.rollback_supported:
        raise ValueError(
            f"{item.identifier} does not have a safe operation-level rollback."
        )
    if item.status not in {"VERIFIED", "APPLIED", "UNVERIFIED"}:
        raise ValueError("Only attempted operations can be rolled back.")

    try:
        if item.kind == "tweak" and item.action == "enable":
            tweak = {t.id: t for t in all_tweaks()}.get(item.identifier)
            if tweak is None:
                raise ValueError(f"Unknown tweak: {item.identifier}.")
            if item.rollback_keys and receipt.backup_path and tweak.check:
                if not tweak.check():
                    raise ValueError(
                        "Current state no longer matches the verified post-change state; "
                        "rollback was not applied to avoid overwriting a later change."
                    )
                count = BackupManager().restore_entries(receipt.backup_path, item.rollback_keys)
                message = f"Restored {count} captured registry value(s) from the operation backup."
            elif tweak.rollback:
                message = tweak.rollback()
            else:
                raise ValueError(f"No rollback implementation for {item.identifier}.")
        elif item.kind == "windows_feature" and item.action == "enable":
            message = set_feature(item.identifier, False)
        else:
            raise ValueError(
                f"Rollback implementation unavailable for {item.kind}/{item.action}."
            )
        rollback_item = ReceiptItem(
            item.kind,
            item.identifier,
            "rollback",
            "ROLLED_BACK",
            message,
            "Rollback action completed.",
            False,
        )
    except Exception as exc:
        rollback_item = ReceiptItem(
            item.kind,
            item.identifier,
            "rollback",
            "ROLLBACK_FAILED",
            str(exc),
            "Rollback action failed; inspect the original backup and receipt.",
            True,
        )

    updated_items = list(receipt.items)
    updated_items[item_index] = rollback_item
    finished = complete(receipt, updated_items)
    path = save(finished, receipt_root)
    return RecoveryResult(str(path), finished.status, rollback_item)
