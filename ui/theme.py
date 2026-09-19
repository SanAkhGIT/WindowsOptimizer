from PySide6.QtGui import QFont

APP_STYLE = """
QWidget {
    background: #0b0f14;
    color: #e7edf5;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QAbstractScrollArea { background: #0b0f14; }
QScrollArea#pageScroll { border: 0; background: #0b0f14; }
QMainWindow { background: #0b0f14; }
QFrame#sidebar {
    background: #0f151d;
    border-right: 1px solid #202a36;
}
QFrame#topbar {
    background: #0b0f14;
    border-bottom: 1px solid #202a36;
}
QFrame#activityPanel {
    background: #0f151d;
    border-top: 1px solid #202a36;
}
QLabel#activityState { font-weight: 700; min-width: 82px; }
QLabel#activityState[state="working"] { color: #72d6ff; }
QLabel#activityState[state="success"] { color: #72e0a0; }
QLabel#activityState[state="error"] { color: #ff8080; }
QLabel#activityOperation { color: #e7edf5; font-weight: 600; }
QLabel#activityElapsed, QLabel#activitySummary { color: #8e9aaa; }
QPushButton#activityToggle {
    padding: 5px 9px;
    border-radius: 7px;
    min-width: 72px;
}
QProgressBar#activityProgress {
    background: #151e28;
    border: 0;
    border-radius: 3px;
}
QProgressBar#activityProgress::chunk {
    background: #2ca7cf;
    border-radius: 3px;
}
QPlainTextEdit#activityLog {
    border-radius: 8px;
    font-family: "Cascadia Mono", "Consolas";
    font-size: 9pt;
}
QFrame#card, QGroupBox#card {
    background: #111821;
    border: 1px solid #202a36;
    border-radius: 14px;
}
QFrame#metric, QFrame#updateStat {
    background: #111821;
    border: 1px solid #202a36;
    border-radius: 12px;
}
QFrame#updateStat { min-width: 150px; }
QLabel#updateValue { font-size: 17pt; font-weight: 700; color: #f5f8fc; }
QLabel#muted { color: #8e9aaa; }
QLabel#title { font-size: 20pt; font-weight: 700; color: #f5f8fc; }
QLabel#section { font-size: 13pt; font-weight: 650; color: #f5f8fc; }
QLabel#pageStatus { color: #8e9aaa; padding: 3px 0; }
QGroupBox {
    border: 1px solid #202a36;
    border-radius: 12px;
    margin-top: 10px;
    padding: 14px 10px 10px 10px;
    background: #0f151d;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 5px;
    color: #b9c5d3;
    font-weight: 650;
}
QLabel#metricValue { font-size: 17pt; font-weight: 700; color: #f5f8fc; }
QLabel#metricAccent { color: #72d6ff; font-size: 9pt; font-weight: 650; }
QPushButton {
    background: #151e28;
    border: 1px solid #283442;
    border-radius: 9px;
    padding: 8px 12px;
}
QPushButton:hover { background: #1b2733; border-color: #3a4b5e; }
QPushButton:pressed { background: #111821; }
QPushButton:disabled { color: #586575; background: #10151c; }
QPushButton#primary {
    background: #1d86a8;
    border-color: #2ca7cf;
    color: white;
    font-weight: 650;
}
QPushButton#primary:hover { background: #2498bb; }
QPushButton#nav {
    text-align: left;
    padding: 10px 12px;
    border: 1px solid transparent;
    background: transparent;
    color: #aeb9c7;
}
QPushButton#nav:hover { background: #151e28; color: #eef4fb; }
QPushButton#nav:checked {
    background: #162d39;
    border-color: #23546a;
    color: #7ddcff;
}
QLineEdit, QComboBox, QTableWidget, QTextEdit, QPlainTextEdit, QListWidget {
    background: #0f151d;
    border: 1px solid #283442;
    border-radius: 9px;
    padding: 7px;
    color: #e7edf5;
}
QComboBox QAbstractItemView { background: #111821; color: #e7edf5; }
QTabWidget::pane { border: 0; }
QTabBar::tab {
    background: #111821;
    padding: 8px 12px;
    margin-right: 4px;
    border-radius: 8px;
    color: #8e9aaa;
}
QTabBar::tab:selected { color: #7ddcff; background: #162d39; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #2a3542; border-radius: 5px; min-height: 30px; }
QTableWidget {
    gridline-color: #202a36;
    alternate-background-color: #111821;
}
QHeaderView::section {
    background: #111821;
    color: #9eabb9;
    border: 0;
    border-bottom: 1px solid #202a36;
    padding: 7px;
    font-weight: 600;
}
QToolTip { background: #111821; color: #e7edf5; border: 1px solid #334354; padding: 6px; }
"""


def apply_theme(app):
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Segoe UI", 10))
