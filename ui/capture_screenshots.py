"""Sentinel panelinin demo ekran görüntüsünü üretir."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "screenshots" / "soc-overview.png"


def _application():
    """Windows'ta yazı tipi için native platform, diğerlerinde offscreen kullanır."""
    from PyQt5.QtWidgets import QApplication

    from ui.theme import configure_qt_plugins

    configure_qt_plugins()
    if sys.platform != "win32":
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    elif os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.pop("QT_QPA_PLATFORM", None)
    return QApplication(sys.argv)


def capture(path: Path = OUTPUT) -> Path:
    app = _application()
    from PyQt5.QtCore import QTimer

    from ui.main import Dashboard
    from ui.theme import apply_theme

    apply_theme(app)
    window = Dashboard(demo=True)
    window.resize(1440, 860)
    window.show()
    window.raise_()
    app.processEvents()
    path.parent.mkdir(parents=True, exist_ok=True)

    def grab() -> None:
        app.processEvents()
        pixmap = window.grab()
        if pixmap.isNull() or pixmap.width() < 100:
            raise RuntimeError("Pencere görüntüsü boş döndü.")
        if not pixmap.save(str(path), "PNG"):
            raise RuntimeError(f"Ekran görüntüsü yazılamadı: {path}")
        print(f"Yazıldı: {path}")
        window.close()
        app.quit()

    QTimer.singleShot(800, grab)
    app.exec_()
    if not path.is_file():
        raise RuntimeError(f"Ekran görüntüsü oluşmadı: {path}")
    return path


def main() -> None:
    capture()


if __name__ == "__main__":
    main()
