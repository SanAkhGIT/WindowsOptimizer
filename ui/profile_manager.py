"""Profile manager dialog for named, versioned user profiles."""
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QInputDialog, QLabel, QListWidget,
    QMessageBox, QPushButton, QTextEdit, QVBoxLayout,
)
from core.profile_manager import (
    build_plan, delete_profile, format_plan, list_profiles, save_profile,
)
from core.configuration import build


class ProfileManagerDialog(QDialog):
    def __init__(self, parent, get_state, apply_profile):
        super().__init__(parent)
        self.get_state = get_state
        self.apply_profile = apply_profile
        self.setWindowTitle("Profile Manager")
        self.resize(720, 560)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "Named profiles are stored separately from the built-in profiles. "
            "Loading a profile prepares selections; it does not change Windows."
        )
        intro.setWordWrap(True)
        intro.setObjectName("muted")
        layout.addWidget(intro)

        self.list = QListWidget()
        self.list.currentRowChanged.connect(self._show_selected)
        layout.addWidget(self.list, 1)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(150)
        layout.addWidget(self.details)

        buttons = QHBoxLayout()
        for text, fn in (
            ("Save Current", self.save_current),
            ("Load Selected", self.load_selected),
            ("Review Plan", self.review_plan),
            ("Delete Custom", self.delete_selected),
            ("Close", self.close),
        ):
            button = QPushButton(text)
            button.clicked.connect(fn)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self):
        self.profiles = list_profiles()
        self.list.clear()
        for profile in self.profiles:
            marker = "Built-in" if profile.builtin else f"Custom v{profile.version}"
            self.list.addItem(f"{profile.name}  •  {marker}")
        if self.profiles:
            self.list.setCurrentRow(0)

    def _selected(self):
        row = self.list.currentRow()
        return self.profiles[row] if 0 <= row < len(self.profiles) else None

    def _show_selected(self, _row):
        profile = self._selected()
        if not profile:
            self.details.clear()
            return
        cfg = profile.configuration
        self.details.setPlainText(
            f"{profile.name} ({profile.id})\n"
            f"{profile.description}\n"
            f"Version {profile.version} • Updated {profile.updated_utc}\n\n"
            f"Tweaks: {len(cfg.get('tweaks', []))}\n"
            f"Apps: {len(cfg.get('apps', []))}\n"
            f"Windows features: {len(cfg.get('windows_features', []))}"
        )

    def save_current(self):
        state = self.get_state()
        name, ok = QInputDialog.getText(self, "Save profile", "Profile name:")
        if not ok or not name.strip():
            return
        profile_id, ok = QInputDialog.getText(
            self, "Profile ID", "Stable ID (letters, numbers, '-' or '_'):",
            text=name.strip().lower().replace(" ", "-"),
        )
        if not ok or not profile_id.strip():
            return
        description, ok = QInputDialog.getText(self, "Description", "Profile description:")
        if not ok:
            return
        try:
            config = build(
                state["tweaks"], state["apps"], state["features"],
                state.get("power_plan"), state.get("maintenance"),
            )
            profile = save_profile(profile_id, name, description, config)
            self.refresh()
            for row, item in enumerate(self.profiles):
                if item.id == profile.id:
                    self.list.setCurrentRow(row)
                    break
            self.details.append(f"\nSaved profile version {profile.version}.")
        except Exception as exc:
            QMessageBox.critical(self, "Profile save failed", str(exc))

    def load_selected(self):
        profile = self._selected()
        if not profile:
            return
        self.apply_profile(profile.configuration)
        self.accept()

    def review_plan(self):
        profile = self._selected()
        if not profile:
            return
        state = self.get_state()
        plan = build_plan(profile, state["tweaks"], state["apps"], state["features"])
        self.details.setPlainText(format_plan(plan))

    def delete_selected(self):
        profile = self._selected()
        if not profile:
            return
        if profile.builtin:
            QMessageBox.information(self, "Built-in profile", "Built-in profiles are read-only.")
            return
        if QMessageBox.question(
            self, "Delete profile", f"Delete '{profile.name}' version {profile.version}?"
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_profile(profile.id)
            self.refresh()
        except Exception as exc:
            QMessageBox.critical(self, "Profile delete failed", str(exc))
