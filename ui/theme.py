from PySide6.QtGui import QFont

APP_STYLE = """
QWidget {
    background: #0b0f14;
    color: #e7edf5;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QMainWindow { background: #0b0f14; }
QFrame#sidebar {
    background: #0f151d;
    border-right: 1px solid #202a36;
}
QFrame#topbar {
    background: #0b0f14;
    border-bottom: 1px solid #202a36;
}
QFrame#card, QGroupBox#card {
    background: #111821;
    border: 1px solid #202a36;
    border-radius: 14px;
}
QFrame#metric {
    background: #111821;
    border: 1px solid #202a36;
    border-radius: 14px;
}
QLabel#muted { color: #8e9aaa; }
QLabel#title { font-size: 20pt; font-weight: 700; color: #f5f8fc; }
QLabel#section { font-size: 13pt; font-weight: 650; color: #f5f8fc; }
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
QLineEdit, QComboBox, QTableWidget, QTextEdit, QListWidget {
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
QToolTip { background: #111821; color: #e7edf5; border: 1px solid #334354; padding: 6px; }
"""


def apply_theme(app):
    app.setStyleSheet(APP_STYLE)
    app.setFont(QFont("Segoe UI", 10))
