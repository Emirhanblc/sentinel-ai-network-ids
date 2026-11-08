"""SOC paneli kartları, haplar ve stilli tablolar."""

from __future__ import annotations

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QPainter
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme import LABEL_COLORS, MUTED, SAFE, TEXT

_MONO: QFont | None = None


def _mono_font() -> QFont:
    global _MONO
    if _MONO is None:
        preferred = QFont("Cascadia Mono", 10)
        _MONO = preferred if preferred.exactMatch() else QFont("Consolas", 10)
    return _MONO


def _shadow(widget: QWidget) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(28)
    effect.setOffset(0, 8)
    effect.setColor(QColor(0, 0, 0, 90))
    widget.setGraphicsEffect(effect)


def format_clock(value: object) -> tuple[str, str]:
    raw = str(value or "")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.strftime("%H:%M:%S"), raw
    except ValueError:
        return raw, raw


def format_size(value: object) -> str:
    try:
        size = int(value)
    except (TypeError, ValueError):
        return str(value)
    if size < 1024:
        return f"{size} B"
    return f"{size / 1024:.1f} KB"


def format_endpoint(ip: object, port: object) -> str:
    return f"{ip}:{port}"


def label_color(name: str, fallback: str = MUTED) -> str:
    return LABEL_COLORS.get(name, fallback)


class AccentRowDelegate(QStyledItemDelegate):
    def __init__(self, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._accent = QColor(accent)

    def paint(self, painter: QPainter, option, index) -> None:  # type: ignore[override]
        super().paint(painter, option, index)
        if index.column() == 0:
            painter.fillRect(option.rect.x(), option.rect.y(), 3, option.rect.height(), self._accent)


class StatusPill(QFrame):
    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("pill")
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 14, 0)
        layout.setSpacing(8)
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._text = QLabel(f"{title}: denetleniyor")
        self._text.setObjectName("pillText")
        layout.addWidget(self._dot, 0, Qt.AlignVCenter)
        layout.addWidget(self._text)
        self._title = title
        self.set_state("denetleniyor", MUTED)

    def set_state(self, status: str, color: str) -> None:
        self._text.setText(f"{self._title}: {status}")
        self._dot.setStyleSheet(
            f"background: {color}; border-radius: 4px; min-width: 8px; min-height: 8px;"
        )


class LiveBadge(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("liveBadge")
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 14, 0)
        layout.setSpacing(8)
        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._label = QLabel("BEKLEMEDE")
        self._label.setObjectName("liveText")
        layout.addWidget(self._dot, 0, Qt.AlignVCenter)
        layout.addWidget(self._label)
        self._running = False
        self.set_running(False)

    def set_running(self, running: bool) -> None:
        self._running = running
        self._label.setText("CANLI" if running else "BEKLEMEDE")
        self.set_pulse(running)

    def set_pulse(self, on: bool) -> None:
        color = SAFE if (on and self._running) else MUTED
        self._dot.setStyleSheet(
            f"background: {color}; border-radius: 4px; min-width: 8px; min-height: 8px;"
        )


class MetricCard(QFrame):
    def __init__(self, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(108)
        _shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        title = QLabel(label.upper())
        title.setObjectName("metricLabel")
        self._value = QLabel("—")
        self._value.setObjectName("metricValue")
        self._hint = QLabel("veri bekleniyor")
        self._hint.setObjectName("metricHint")
        layout.addWidget(title)
        layout.addWidget(self._value)
        layout.addWidget(self._hint)

    def set_metric(self, value: str, hint: str, color: str = TEXT) -> None:
        self._value.setText(value)
        self._value.setStyleSheet(f"color: {color};")
        self._hint.setText(hint)


class StreamPanel(QFrame):
    def __init__(
        self,
        title: str,
        headers: list[str],
        accent: str,
        empty_hint: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("panel")
        _shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        header = QHBoxLayout()
        heading = QLabel(title.upper())
        heading.setObjectName("panelTitle")
        heading.setStyleSheet(f"color: {accent};")
        self._count = QLabel("0 kayıt")
        self._count.setObjectName("panelCount")
        header.addWidget(heading)
        header.addStretch(1)
        header.addWidget(self._count)
        layout.addLayout(header)
        self.table = make_table(headers, accent)
        empty = QLabel(f"Kayıt yok\n{empty_hint}")
        empty.setObjectName("emptyHint")
        empty.setAlignment(Qt.AlignCenter)
        empty.setWordWrap(True)
        self._stack = QStackedWidget()
        self._stack.addWidget(self.table)
        self._stack.addWidget(empty)
        layout.addWidget(self._stack)
        self.show_rows(0)

    def show_rows(self, count: int) -> None:
        self._count.setText("kayıt yok" if count == 0 else f"{count} kayıt")
        self._stack.setCurrentIndex(1 if count == 0 else 0)


def make_table(headers: list[str], accent: str) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.verticalHeader().setVisible(False)
    table.verticalHeader().setDefaultSectionSize(40)
    table.setShowGrid(False)
    table.setEditTriggers(QTableWidget.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.setSelectionMode(QAbstractItemView.SingleSelection)
    table.setAlternatingRowColors(False)
    table.setFocusPolicy(Qt.NoFocus)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.horizontalHeader().setStretchLastSection(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
    table.setColumnWidth(0, 96)
    table.setItemDelegate(AccentRowDelegate(accent, table))
    return table


def make_item(
    text: str,
    background: str,
    tooltip: str = "",
    monospace: bool = False,
    color: str = TEXT,
    align: Qt.AlignmentFlag = Qt.AlignVCenter | Qt.AlignLeft,
) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setBackground(QColor(background))
    item.setForeground(QColor(color))
    item.setFlags(item.flags() ^ Qt.ItemIsEditable)
    item.setTextAlignment(align)
    if tooltip:
        item.setToolTip(tooltip)
    if monospace:
        item.setFont(_mono_font())
    return item


def make_badge(text: str, color: str, background: str) -> QLabel:
    badge = QLabel(text)
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(
        f"""
        QLabel {{
            background: {background};
            color: {color};
            border: 1px solid {color};
            border-radius: 8px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
            margin: 6px 8px;
        }}
        """
    )
    return badge


def fill_table(table: QTableWidget, rows: list[list[object]]) -> None:
    scrollbar = table.verticalScrollBar()
    previous = scrollbar.value()
    at_top = previous == 0
    table.setRowCount(0)
    table.setRowCount(len(rows))
    for row_index, row in enumerate(rows):
        for column, cell in enumerate(row):
            if isinstance(cell, tuple) and len(cell) == 2:
                item, widget = cell
                table.setItem(row_index, column, item)
                table.setCellWidget(row_index, column, widget)
            elif isinstance(cell, QWidget):
                table.setCellWidget(row_index, column, cell)
            elif isinstance(cell, QTableWidgetItem):
                table.setItem(row_index, column, cell)
            else:
                table.setItem(row_index, column, QTableWidgetItem(str(cell)))
    if not at_top:
        scrollbar.setValue(previous)


def restore_column_widths(table: QTableWidget, widths: dict[int, int], stretch: int) -> None:
    header = table.horizontalHeader()
    for index in range(table.columnCount()):
        header.setSectionResizeMode(index, QHeaderView.Fixed if index in widths else QHeaderView.Stretch)
        if index in widths:
            table.setColumnWidth(index, widths[index])
    header.setSectionResizeMode(stretch, QHeaderView.Stretch)
