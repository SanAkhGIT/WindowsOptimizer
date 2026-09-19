from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QWidget, QVBoxLayout

from app import MainWindow


def test_operation_control_gate_disables_all_pages_and_restores_state():
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

    MainWindow._set_page_controls_enabled(window, True)
    assert first.isEnabled()
    assert not second.isEnabled()
