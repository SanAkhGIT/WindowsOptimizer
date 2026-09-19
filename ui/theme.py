from PySide6.QtGui import QFont

APP_STYLE = """
QWidget {
    background: #0a0e13;
    color: #e8eef6;
    font-family: "Segoe UI Variable", "Segoe UI";
    font-size: 10pt;
}
QMainWindow, QAbstractScrollArea, QScrollArea#pageScroll {
    background: #0a0e13;
}
QFrame#sidebar {
    background: #0d131b;
    border-right: 1px solid #1b2632;
}
QFrame#topbar {
    background: #0a0e13;
    border-bottom: 1px solid #1b2632;
}
QFrame#activityPanel {
    background: #0d131b;
    border-top: 1px solid #1b2632;
}
QLabel#brand {
    color: #f7faff;
    font-size: 15pt;
    font-weight: 800;
}
QLabel#brandSub {
    color: #6f7e90;
    font-size: 8pt;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#title {
    color: #f7faff;
    font-size: 20pt;
    font-weight: 750;
}
QLabel#section {
    color: #f3f7fb;
    font-size: 13pt;
    font-weight: 700;
}
QLabel#muted {
    color: #8290a1;
}
QLabel#pageStatus {
    color: #8290a1;
    padding: 3px 0;
}
QPushButton {
    background: #131b25;
    color: #dce5ee;
    border: 1px solid #263442;
    border-radius: 8px;
    padding: 8px 13px;
    min-height: 18px;
    font-weight: 550;
}
QPushButton:hover {
    background: #192431;
    border-color: #3b4d60;
    color: #ffffff;
}
QPushButton:pressed {
    background: #0f1720;
    padding-top: 9px;
}
QPushButton:focus {
    border-color: #4db7dc;
}
QPushButton:disabled {
    color: #536173;
    background: #0d131a;
    border-color: #18222d;
}
QPushButton#primary {
    background: #167da1;
    border-color: #2ba7d2;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#primary:hover {
    background: #1b91b8;
    border-color: #5ac7e8;
}
QPushButton#nav {
    text-align: left;
    padding: 9px 12px;
    min-height: 22px;
    border: 1px solid transparent;
    border-radius: 8px;
    background: transparent;
    color: #8f9dad;
    font-weight: 600;
}
QPushButton#nav:hover {
    background: #131d28;
    color: #e9f1f8;
}
QPushButton#nav:checked {
    background: #12303e;
    border-color: #1e566b;
    color: #7ddcff;
}
QPushButton#activityToggle {
    padding: 5px 10px;
    min-height: 16px;
    border-radius: 7px;
}
QLabel#activityState {
    font-weight: 750;
    min-width: 86px;
}
QLabel#activityState[state="working"] { color: #6fd5ff; }
QLabel#activityState[state="success"] { color: #72dfa1; }
QLabel#activityState[state="error"] { color: #ff8585; }
QLabel#activityState[state="ready"] { color: #8290a1; }
QLabel#activityOperation {
    color: #e9f1f8;
    font-weight: 650;
}
QLabel#activityElapsed, QLabel#activitySummary {
    color: #8290a1;
}
QProgressBar#activityProgress {
    background: #151e28;
    border: 0;
    border-radius: 3px;
}
QProgressBar#activityProgress::chunk {
    background: #2ba7d2;
    border-radius: 3px;
}
QPlainTextEdit#activityLog {
    background: #080c11;
    border: 1px solid #1c2936;
    border-radius: 8px;
    font-family: "Cascadia Mono", "Consolas";
    font-size: 9pt;
}
QFrame#card, QGroupBox#card {
    background: #101821;
    border: 1px solid #1d2a37;
    border-radius: 13px;
}
QFrame#metric, QFrame#updateStat {
    background: #101821;
    border: 1px solid #1d2a37;
    border-radius: 11px;
}
QFrame#metric:hover, QFrame#updateStat:hover {
    border-color: #2c4354;
}
QFrame#updateStat { min-width: 150px; }
QLabel#metricValue, QLabel#updateValue {
    color: #f6f9fc;
    font-size: 17pt;
    font-weight: 750;
}
QLabel#metricAccent {
    color: #6fd5ff;
    font-size: 9pt;
    font-weight: 650;
}
QGroupBox {
    background: #0e151e;
    border: 1px solid #1d2a37;
    border-radius: 11px;
    margin-top: 10px;
    padding: 15px 11px 11px 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #b8c5d2;
    background: #0e151e;
    font-weight: 700;
}
QLineEdit, QComboBox, QTableWidget, QTextEdit, QPlainTextEdit, QListWidget {
    background: #0c131b;
    border: 1px solid #253342;
    border-radius: 8px;
    padding: 7px;
    color: #e7eef5;
    selection-background-color: #1c6078;
}
QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #3aa7cf;
}
QComboBox QAbstractItemView {
    background: #101821;
    color: #e7eef5;
    border: 1px solid #2a3a49;
    selection-background-color: #173b4b;
}
QTabWidget::pane {
    border: 0;
}
QTabBar::tab {
    background: #101821;
    padding: 8px 13px;
    margin-right: 4px;
    border: 1px solid transparent;
    border-radius: 8px;
    color: #8190a0;
    font-weight: 600;
}
QTabBar::tab:hover {
    color: #dce7ef;
    background: #141e28;
}
QTabBar::tab:selected {
    color: #7ddcff;
    background: #12303e;
    border-color: #1e566b;
}
QCheckBox {
    spacing: 8px;
    color: #cbd6e0;
}
QCheckBox::indicator {
    width: 17px;
    height: 17px;
}
QScrollBar:vertical {
    background: transparent;
    width: 9px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #263544;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #34485b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QTableWidget {
    gridline-color: #1b2632;
    alternate-background-color: #101821;
}
QTableWidget::item {
    padding: 4px;
}
QTableWidget::item:selected {
    background: #173c4d;
}
QHeaderView::section {
    background: #111a23;
    color: #91a0af;
    border: 0;
    border-bottom: 1px solid #22303d;
    padding: 8px;
    font-weight: 700;
}
QToolTip {
    background: #111a23;
    color: #edf4fa;
    border: 1px solid #385062;
    padding: 6px 8px;
}
QMessageBox {
    background: #0e151e;
}
"""

def apply_theme(app):
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Segoe UI Variable", 10))
