"""Review and approve individual profile plan operations."""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMessageBox, QPushButton, QVBoxLayout,
)


class OperationApprovalDialog(QDialog):
    def __init__(self, parent, plan, execute):
        super().__init__(parent)
        self.plan = plan
        self.execute = execute
        self.setWindowTitle("Approve profile operations")
        self.resize(820, 560)

        layout = QVBoxLayout(self)
        intro = QLabel(
            f"Review each operation from '{plan.profile_name}'. "
            "Only checked items will be executed. A single registry backup is "
            "created before the approved batch."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        self.items = QListWidget()
        for item in plan.items:
            row = QListWidgetItem(
                f"{item.action.upper():<7}  {item.kind:<18} {item.identifier}\n"
                f"Reason: {item.reason}"
            )
            row.setCheckState(2 if item.action != "skip" else 0)
            row.setData(32, item)
            self.items.addItem(row)
        layout.addWidget(self.items, 1)

        buttons = QHBoxLayout()
        select_all = QPushButton("Select All")
        select_all.clicked.connect(self.select_all)
        buttons.addWidget(select_all)

        clear = QPushButton("Clear")
        clear.clicked.connect(self.clear)
        buttons.addWidget(clear)
        buttons.addStretch()

        approve = QPushButton("Approve Selected & Apply")
        approve.setObjectName("primary")
        approve.clicked.connect(self.approve_selected)
        buttons.addWidget(approve)

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        layout.addLayout(buttons)

    def selected_items(self):
        return tuple(
            self.items.item(index).data(32)
            for index in range(self.items.count())
            if self.items.item(index).checkState() == 2
        )

    def select_all(self):
        for index in range(self.items.count()):
            item = self.items.item(index)
            if item.data(32).action != "skip":
                item.setCheckState(2)

    def clear(self):
        for index in range(self.items.count()):
            self.items.item(index).setCheckState(0)

    def approve_selected(self):
        selected = self.selected_items()
        if not selected:
            QMessageBox.information(
                self, "Nothing approved", "Select at least one actionable operation."
            )
            return

        if QMessageBox.question(
            self,
            "Confirm approved operations",
            f"Execute {len(selected)} approved operation(s)? "
            "The selected operations will run in order and each result will be recorded.",
        ) != QMessageBox.StandardButton.Yes:
            return

        self.accept()
        self.execute(selected)
