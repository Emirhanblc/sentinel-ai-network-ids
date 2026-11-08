"""IDS canlı trafik ve tehdit paneli."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from PyQt5.QtCore import QProcess, Qt, QTimer, QUrl
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .theme import (
    MUTED,
    SAFE,
    SAFE_BG,
    SAFE_NEW,
    THREAT,
    THREAT_BG,
    THREAT_NEW,
    apply_theme,
    configure_qt_plugins,
)
from .widgets import (
    LiveBadge,
    MetricCard,
    StatusPill,
    StreamPanel,
    fill_table,
    format_clock,
    format_endpoint,
    format_size,
    label_color,
    make_badge,
    make_item,
    restore_column_widths,
)

configure_qt_plugins()


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


class Dashboard(QMainWindow):
    def __init__(self, demo: bool = False) -> None:
        super().__init__()
        self.demo = demo
        self.api_url = os.getenv("IDS_API_URL", "http://127.0.0.1:8000").rstrip("/")
        self.network = QNetworkAccessManager(self)
        self._replies: set[QNetworkReply] = set()
        self._seen_traffic_ids: set[int] = set()
        self._seen_alert_ids: set[int] = set()
        self._traffic_signature: tuple[int, ...] | None = None
        self._alerts_signature: tuple[int, ...] | None = None
        self._traffic_ready = False
        self._alerts_ready = False
        self._generation = 0
        self._pulse_on = True
        self.sniffer = QProcess(self)
        self.sniffer.setProcessChannelMode(QProcess.MergedChannels)
        self.sniffer.stateChanged.connect(self._process_state_changed)
        self.setWindowTitle("Sentinel — Yapay Zeka Destekli Ağ IDS")
        self.resize(1440, 860)
        self.setMinimumSize(1100, 720)
        self._build_ui()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._pulse_live)
        self.pulse_timer.start(700)
        if demo:
            self._load_demo()
        else:
            self.timer.start(1500)
            self.refresh()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(22, 18, 22, 16)
        layout.setSpacing(16)
        layout.addLayout(self._build_header())
        layout.addLayout(self._build_metrics())
        layout.addLayout(self._build_streams(), 1)
        self.message = QLabel("")
        self.message.setObjectName("message")
        self.message.setWordWrap(True)
        self.message.hide()
        layout.addWidget(self.message)
        self.setCentralWidget(root)

    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(12)
        brand = QVBoxLayout()
        brand.setSpacing(0)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        mark = QLabel("◆")
        mark.setObjectName("brandMark")
        title = QLabel("SENTINEL")
        title.setObjectName("brandTitle")
        title_row.addWidget(mark)
        title_row.addWidget(title)
        title_row.addStretch(1)
        subtitle = QLabel("Yapay Zeka Destekli Ağ IDS")
        subtitle.setObjectName("brandSubtitle")
        brand.addLayout(title_row)
        brand.addWidget(subtitle)
        header.addLayout(brand, 1)

        self.listener_status = StatusPill("Dinleyici")
        self.listener_status.set_state("durdu", MUTED)
        self.api_status = StatusPill("Karar motoru")
        self.live_badge = LiveBadge()
        self.interface = QLineEdit(os.getenv("SNIFFER_INTERFACE", ""))
        self.interface.setPlaceholderText("Ağ arayüzü adı")
        self.interface.setFixedWidth(200)
        self.toggle = QPushButton("Dinleyiciyi başlat")
        self.toggle.setObjectName("toggle")
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.clicked.connect(self.toggle_sniffer)
        header.addWidget(self.listener_status)
        header.addWidget(self.api_status)
        header.addWidget(self.live_badge)
        header.addWidget(self.interface)
        header.addWidget(self.toggle)
        return header

    def _build_metrics(self) -> QHBoxLayout:
        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.clean_card = MetricCard("Temiz trafik")
        self.threat_card = MetricCard("Tehditler")
        self.latest_card = MetricCard("Son tehdit")
        self.engine_card = MetricCard("Karar motoru")
        for card in (self.clean_card, self.threat_card, self.latest_card, self.engine_card):
            metrics.addWidget(card)
        return metrics

    def _build_streams(self) -> QHBoxLayout:
        streams = QHBoxLayout()
        streams.setSpacing(14)
        self.traffic_panel = StreamPanel(
            "Güvenli akış",
            ["Zaman", "Protokol", "Akış", "Boyut"],
            SAFE,
            "Henüz temiz trafik yok",
        )
        self.alerts_panel = StreamPanel(
            "Aktif tehditler",
            ["Zaman", "Sınıf", "Kaynak IP", "Hedef IP", "Hedef port"],
            THREAT,
            "Henüz tehdit tespit edilmedi",
        )
        self.traffic = self.traffic_panel.table
        self.alerts = self.alerts_panel.table
        restore_column_widths(self.traffic, {0: 96, 1: 102, 3: 84}, stretch=2)
        restore_column_widths(self.alerts, {0: 96, 1: 128, 4: 92}, stretch=3)
        streams.addWidget(self.traffic_panel, 3)
        streams.addWidget(self.alerts_panel, 2)
        return streams

    def _load_demo(self) -> None:
        from .demo_data import DEMO_ALERTS, DEMO_TRAFFIC

        self.api_status.set_state("çalışıyor", SAFE)
        self.engine_card.set_metric("Hazır", "demo verisi yüklü", SAFE)
        self.listener_status.set_state("çalışıyor", SAFE)
        self.live_badge.set_running(True)
        self.interface.setText("Ethernet (demo)")
        self.interface.setEnabled(False)
        self.toggle.setEnabled(False)
        self.toggle.setText("Demo modu")
        self._traffic_ready = True
        self._alerts_ready = True
        self._seen_traffic_ids = {int(row["id"]) for row in DEMO_TRAFFIC[2:]}
        self._seen_alert_ids = {int(row["id"]) for row in DEMO_ALERTS[2:]}
        self._traffic_received(DEMO_TRAFFIC)
        self._alerts_received(DEMO_ALERTS)
        self._set_message("")

    def refresh(self) -> None:
        if self.demo:
            return
        self._generation += 1
        generation = self._generation
        for reply in tuple(self._replies):
            reply.abort()
        self._get("/health", self._health_received, generation)
        self._get("/traffic?limit=100&verdict=Temiz", self._traffic_received, generation)
        self._get("/alerts?limit=100", self._alerts_received, generation)

    def _get(self, path: str, callback, generation: int) -> None:
        reply = self.network.get(QNetworkRequest(QUrl(self.api_url + path)))
        self._replies.add(reply)
        reply.finished.connect(lambda: self._handle_reply(reply, callback, generation))

    def _handle_reply(self, reply: QNetworkReply, callback, generation: int) -> None:
        self._replies.discard(reply)
        if generation != self._generation:
            reply.deleteLater()
            return
        if reply.error() != QNetworkReply.NoError:
            self.api_status.set_state("hazır değil", THREAT)
            self.engine_card.set_metric("Hazır değil", "servise ulaşılamadı", THREAT)
            self._set_message(f"Servis hatası: {reply.errorString()}")
        else:
            try:
                callback(json.loads(bytes(reply.readAll()).decode("utf-8")))
                self._set_message("")
            except (ValueError, TypeError, KeyError):
                self._set_message("Servisten geçersiz yanıt alındı; eski veriler korunuyor.")
        reply.deleteLater()

    def _set_message(self, text: str) -> None:
        self.message.setText(text)
        self.message.setVisible(bool(text))

    def _health_received(self, data: dict) -> None:
        ready = bool(data.get("ready"))
        status = "çalışıyor" if ready else "hazır değil"
        color = SAFE if ready else THREAT
        self.api_status.set_state(status, color)
        self.engine_card.set_metric(
            "Hazır" if ready else "Hazır değil",
            "model ve veritabanı bağlı" if ready else "model veya veritabanı yok",
            color,
        )

    def _traffic_received(self, rows: list[dict]) -> None:
        signature = tuple(int(row["id"]) for row in rows)
        if signature == self._traffic_signature:
            return
        count = len(rows)
        self.clean_card.set_metric(str(count), "son 100 kayıt", SAFE if count else MUTED)
        if not rows:
            self.traffic_panel.show_rows(0)
            self._traffic_signature = signature
            self._seen_traffic_ids.clear()
            return
        new_ids = self._new_ids(rows, self._seen_traffic_ids, self._traffic_ready)
        self._traffic_ready = True
        self._seen_traffic_ids = set(signature)
        filled = []
        for row in rows:
            fresh = int(row["id"]) in new_ids
            background = SAFE_NEW if fresh else SAFE_BG
            clock, tooltip = format_clock(row["captured_at"])
            protocol = str(row["protocol"])
            flow = f"{format_endpoint(row['src_ip'], row['src_port'])}  →  {format_endpoint(row['dst_ip'], row['dst_port'])}"
            color = label_color(protocol, SAFE)
            filled.append(
                [
                    make_item(clock, background, tooltip),
                    (
                        make_item("", background),
                        make_badge(protocol, color, background),
                    ),
                    make_item(flow, background, monospace=True),
                    make_item(format_size(row["packet_size"]), background, color=MUTED),
                ]
            )
        fill_table(self.traffic, filled)
        self.traffic_panel.show_rows(count)
        self._traffic_signature = signature

    def _alerts_received(self, rows: list[dict]) -> None:
        signature = tuple(int(row["id"]) for row in rows)
        if signature == self._alerts_signature:
            return
        count = len(rows)
        latest = str(rows[0]["label"]) if rows else "—"
        latest_color = label_color(latest, MUTED) if rows else MUTED
        self.threat_card.set_metric(str(count), "son 100 uyarı", THREAT if count else MUTED)
        self.latest_card.set_metric(latest, "en yeni sınıflandırma" if rows else "uyarı yok", latest_color)
        if not rows:
            self.alerts_panel.show_rows(0)
            self._alerts_signature = signature
            self._seen_alert_ids.clear()
            return
        new_ids = self._new_ids(rows, self._seen_alert_ids, self._alerts_ready)
        self._alerts_ready = True
        self._seen_alert_ids = set(signature)
        filled = []
        for row in rows:
            fresh = int(row["id"]) in new_ids
            background = THREAT_NEW if fresh else THREAT_BG
            clock, tooltip = format_clock(row["captured_at"])
            label = str(row["label"])
            color = label_color(label, THREAT)
            filled.append(
                [
                    make_item(clock, background, tooltip),
                    (
                        make_item("", background),
                        make_badge(label, color, background),
                    ),
                    make_item(str(row["src_ip"]), background, monospace=True),
                    make_item(str(row["dst_ip"]), background, monospace=True),
                    make_item(str(row["dst_port"]), background, color=MUTED, align=Qt.AlignVCenter | Qt.AlignRight),
                ]
            )
        fill_table(self.alerts, filled)
        self.alerts_panel.show_rows(count)
        self._alerts_signature = signature

    @staticmethod
    def _new_ids(rows: list[dict], seen: set[int], ready: bool) -> set[int]:
        current = {int(row["id"]) for row in rows}
        if not ready:
            return set()
        return current - seen

    def toggle_sniffer(self) -> None:
        if self.demo:
            return
        if self.sniffer.state() != QProcess.NotRunning:
            self.sniffer.terminate()
            if not self.sniffer.waitForFinished(1500):
                self.sniffer.kill()
            return
        project_root = Path(__file__).resolve().parents[1]
        arguments = [
            str(project_root / "src" / "sniffer.py"),
            "--output",
            "http",
            "--api-url",
            self.api_url,
        ]
        if self.interface.text().strip():
            arguments.extend(["--iface", self.interface.text().strip()])
        self.sniffer.setWorkingDirectory(str(project_root))
        self.sniffer.start(sys.executable, arguments)

    def _process_state_changed(self, state: QProcess.ProcessState) -> None:
        running = state == QProcess.Running
        self.listener_status.set_state("çalışıyor" if running else "durdu", SAFE if running else MUTED)
        self.live_badge.set_running(running)
        self.toggle.setText("Dinleyiciyi durdur" if running else "Dinleyiciyi başlat")
        self.toggle.setProperty("running", running)
        self.toggle.style().unpolish(self.toggle)
        self.toggle.style().polish(self.toggle)
        self.interface.setEnabled(not running)

    def _pulse_live(self) -> None:
        self._pulse_on = not self._pulse_on
        self.live_badge.set_pulse(self._pulse_on)

    def closeEvent(self, event) -> None:
        self.timer.stop()
        self.pulse_timer.stop()
        self._generation += 1
        for reply in tuple(self._replies):
            reply.disconnect()
            reply.abort()
            reply.deleteLater()
        self._replies.clear()
        if self.sniffer.state() != QProcess.NotRunning:
            self.sniffer.terminate()
            self.sniffer.waitForFinished(1000)
        super().closeEvent(event)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sentinel IDS masaüstü paneli")
    parser.add_argument(
        "--demo",
        action="store_true",
        default=_env_flag("IDS_DEMO"),
        help="API olmadan örnek laboratuvar kayıtlarıyla paneli açar.",
    )
    args, qt_args = parser.parse_known_args()
    application = QApplication([sys.argv[0], *qt_args])
    apply_theme(application)
    window = Dashboard(demo=args.demo)
    window.show()
    raise SystemExit(application.exec_())


if __name__ == "__main__":
    main()
