from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QStackedWidget, QWidget, QVBoxLayout

from app import MainWindow


def test_operation_control_gate_disables_all_pages_and_restores_state():
    app = QApplication.instance() or QApplication([])
    window = QMainWindow()
    stack = QStackedWidget()
    page_one = QWidget()
    page_two = QWidget()

    first = QPushButton("first", page_one)
    second = QPushButton("second", page_two)
    second.setEnabled(False)

    QVBoxLayout(page_one).addWidget(first)
    QVBoxLayout(page_two).addWidget(second)
    stack.addWidget(page_one)
    stack.addWidget(page_two)

    window.stack = stack
    window._operation_control_states = {}

    MainWindow._set_page_controls_enabled(window, False)
    assert not first.isEnabled()
    assert not second.isEnabled()
    app.processEvents()

    MainWindow._set_page_controls_enabled(window, True)
    assert first.isEnabled()
    assert not second.isEnabled()



def test_profile_manager_receives_recovery_callbacks(monkeypatch):
    captured = {}

    class FakeDialog:
        def __init__(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs

        def exec(self):
            captured["executed"] = True

    window = MainWindow.__new__(MainWindow)
    monkeypatch.setattr("app.ProfileManagerDialog", FakeDialog)

    MainWindow._show_profile_manager(window, {})

    assert captured["kwargs"]["rollback"] == window.rollback_receipt
    assert captured["kwargs"]["restore_backup"] == window.restore_backup
    assert captured["executed"] is True

