"""Recovery dialog for operation receipts."""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)
from core.operation_receipts import recent


class RecoveryDialog(QDialog):
    def __init__(self, parent, rollback, restore_backup):
        super().__init__(parent)
        self.rollback = rollback
        self.restore_backup = restore_backup
        self.setWindowTitle("Recovery & Receipts")
        self.resize(900, 620)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Operation-level rollback is available only where the receipt "
            "records a reliable inverse. Registry backups remain a separate "
            "recovery layer."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        body = QHBoxLayout()
        self.receipts = QListWidget()
        self.receipts.currentRowChanged.connect(self._show_items)
        body.addWidget(self.receipts, 1)

        self.items = QListWidget()
        body.addWidget(self.items, 2)
        layout.addLayout(body, 1)

        buttons = QHBoxLayout()
        rollback_button = QPushButton("Rollback Selected")
        rollback_button.setObjectName("primary")
        rollback_button.clicked.connect(self.rollback_selected)
        buttons.addWidget(rollback_button)

        restore_button = QPushButton("Restore Registry Backup")
        restore_button.clicked.connect(self.restore_registry_backup)
        buttons.addWidget(restore_button)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        buttons.addWidget(refresh)
        buttons.addStretch()
        close = QPushButton("Close")
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        layout.addLayout(buttons)

        self.refresh()

    def refresh(self):
        self.entries = recent(limit=30)
        self.receipts.clear()
        for path, receipt in self.entries:
            self.receipts.addItem(
                f"{receipt.created_utc} • {receipt.status} • "
                f"{receipt.profile_id or receipt.source} • {len(receipt.items)} item(s)"
            )
        self.items.clear()
        if self.entries:
            self.receipts.setCurrentRow(0)

    def _show_items(self, row):
        self.items.clear()
        if row < 0 or row >= len(self.entries):
            return
        _, receipt = self.entries[row]
        for index, item in enumerate(receipt.items):
            marker = "ROLLBACK AVAILABLE" if item.rollback_supported else "NO OPERATION ROLLBACK"
            widget = QListWidgetItem(
                f"{index}: {item.identifier} • {item.action} • {item.status}\n"
                f"{marker} • {item.verification}"
            )
            widget.setData(32, index)
            self.items.addItem(widget)

    def rollback_selected(self):
        receipt_row = self.receipts.currentRow()
        item_row = self.items.currentRow()
        if receipt_row < 0 or item_row < 0:
            QMessageBox.information(self, "Select an operation", "Select a receipt and an operation.")
            return
        path, receipt = self.entries[receipt_row]
        item = receipt.items[item_row]
        if not item.rollback_supported:
            QMessageBox.information(
                self, "Rollback unavailable",
                "This operation does not have a safe operation-level inverse."
            )
            return
        if QMessageBox.question(
            self,
            "Confirm rollback",
            f"Rollback '{item.identifier}' using its declared inverse?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self.rollback(str(path), item_row)

    def restore_registry_backup(self):
        receipt_row = self.receipts.currentRow()
        if receipt_row < 0:
            QMessageBox.information(self, "Select a receipt", "Select a receipt with a backup first.")
            return
        path, receipt = self.entries[receipt_row]
        if not receipt.backup_path:
            QMessageBox.information(self, "No backup", "This receipt does not reference a registry backup.")
            return
        if QMessageBox.question(
            self,
            "Restore registry backup",
            "Restore the registry values captured before this operation batch? "
            "This is a broad recovery action and may overwrite changes made after the backup.",
        ) != QMessageBox.StandardButton.Yes:
            return
        self.restore_backup(receipt.backup_path)
