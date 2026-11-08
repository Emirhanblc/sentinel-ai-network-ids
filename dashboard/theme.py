"""Koyu SOC paleti ve uygulama QSS stilleri."""

from __future__ import annotations

import os
import sys

from PyQt5.QtGui import QColor, QFont, QPalette
from PyQt5.QtWidgets import QApplication

BG = "#0B1220"
SURFACE = "#121A2B"
SURFACE_ALT = "#162033"
BORDER = "#1E2A44"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"
SAFE = "#22C55E"
SAFE_BG = "#0F2A1C"
SAFE_NEW = "#163D28"
THREAT = "#F43F5E"
THREAT_BG = "#2A1218"
THREAT_NEW = "#3B1820"
ACCENT = "#38BDF8"
DDOS = "#F97316"
PORT_SCAN = "#A78BFA"
BRUTE = "#FACC15"
TCP = "#38BDF8"
UDP = "#2DD4BF"

LABEL_COLORS = {
    "DDoS": DDOS,
    "Port Scan": PORT_SCAN,
    "Brute Force": BRUTE,
    "Temiz": SAFE,
    "TCP": TCP,
    "UDP": UDP,
}

APP_QSS = f"""
QMainWindow {{
    background: {BG};
}}
QWidget#root {{
    background: {BG};
    color: {TEXT};
    font-family: "Segoe UI";
    font-size: 13px;
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QLabel#brandMark {{
    color: {SAFE};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 3px;
}}
QLabel#brandTitle {{
    color: {TEXT};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 2px;
}}
QLabel#brandSubtitle {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#panelTitle {{
    color: {TEXT};
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.2px;
}}
QLabel#panelCount {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#metricLabel {{
    color: {MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.1px;
}}
QLabel#metricValue {{
    color: {TEXT};
    font-size: 28px;
    font-weight: 800;
}}
QLabel#metricHint {{
    color: {MUTED};
    font-size: 12px;
}}
QLabel#pillText {{
    color: {TEXT};
    font-size: 12px;
    font-weight: 600;
}}
QLabel#liveText {{
    color: {TEXT};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.4px;
}}
QLabel#emptyHint {{
    color: {MUTED};
    font-size: 14px;
    padding: 24px;
}}
QLabel#message {{
    color: {THREAT};
    font-size: 12px;
    padding: 8px 12px;
    border: 1px solid {THREAT};
    border-radius: 8px;
    background: rgba(244, 63, 94, 30);
}}
QFrame#card, QFrame#panel, QFrame#pill, QFrame#liveBadge {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QFrame#pill, QFrame#liveBadge {{
    border-radius: 18px;
}}
QLineEdit {{
    background: {SURFACE_ALT};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px 12px;
    min-width: 180px;
    selection-background-color: {BORDER};
}}
QLineEdit:disabled {{
    color: {MUTED};
}}
QPushButton#toggle {{
    background: {SAFE};
    color: {BG};
    border: none;
    border-radius: 10px;
    padding: 9px 18px;
    font-weight: 700;
}}
QPushButton#toggle:hover {{
    background: #4ADE80;
}}
QPushButton#toggle[running="true"] {{
    background: {THREAT};
    color: {TEXT};
}}
QPushButton#toggle[running="true"]:hover {{
    background: #FB7185;
}}
QTableWidget {{
    background: {SURFACE};
    alternate-background-color: {SURFACE};
    color: {TEXT};
    border: none;
    gridline-color: transparent;
    outline: none;
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {BORDER};
    color: {TEXT};
}}
QHeaderView::section {{
    background: {SURFACE_ALT};
    color: {MUTED};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}}
QTableCornerButton::section {{
    background: {SURFACE_ALT};
    border: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 4px 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: none;
}}
QScrollBar:horizontal {{
    height: 0;
}}
QStackedWidget {{
    background: transparent;
}}
"""


def configure_qt_plugins() -> None:
    """Windows sanal ortamında Qt platform eklentisinin yolunu sabitler."""
    if sys.platform != "win32":
        return
    plugin_dir = os.path.join(
        sys.prefix, "Lib", "site-packages", "PyQt5", "Qt5", "plugins", "platforms"
    )
    if os.path.isdir(plugin_dir):
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = plugin_dir


def apply_theme(application: QApplication) -> None:
    application.setStyle("Fusion")
    application.setFont(QFont("Segoe UI", 10))
    palette = QPalette()
    background = QColor(BG)
    surface = QColor(SURFACE)
    text = QColor(TEXT)
    muted = QColor(MUTED)
    highlight = QColor(BORDER)
    palette.setColor(QPalette.Window, background)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, surface)
    palette.setColor(QPalette.AlternateBase, QColor(SURFACE_ALT))
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, surface)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, text)
    palette.setColor(QPalette.PlaceholderText, muted)
    palette.setColor(QPalette.ToolTipBase, surface)
    palette.setColor(QPalette.ToolTipText, text)
    application.setPalette(palette)
    application.setStyleSheet(APP_QSS)
