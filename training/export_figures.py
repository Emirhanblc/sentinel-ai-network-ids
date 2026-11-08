"""Eğitim metriklerinden vitrin figürleri üretir."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shared.features import LABELS

BG = "#0B1220"
SURFACE = "#121A2B"
BORDER = "#1E2A44"
TEXT = "#E5E7EB"
MUTED = "#94A3B8"
ACCENT = "#38BDF8"


def _lerp(start: tuple[int, int, int], end: tuple[int, int, int], t: float) -> str:
    t = max(0.0, min(1.0, t))
    rgb = tuple(int(start[i] + (end[i] - start[i]) * t) for i in range(3))
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def confusion_matrix_svg(matrix: list[list[int]], labels: list[str]) -> str:
    """Koyu temalı karışıklık matrisi SVG metni üretir."""
    size = len(labels)
    cell = 100
    left, top, right, bottom = 160, 96, 40, 68
    width = left + size * cell + right
    height = top + size * cell + bottom
    peak = max(max(row) for row in matrix) or 1
    low = (22, 32, 51)
    high = (56, 189, 248)
    cells: list[str] = []
    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            x = left + col_index * cell
            y = top + row_index * cell
            fill = _lerp(low, high, (value / peak) ** 0.55)
            ink = TEXT if value / peak > 0.35 else MUTED
            cells.append(
                f'<rect x="{x}" y="{y}" width="{cell - 6}" height="{cell - 6}" rx="10" fill="{fill}"/>'
                f'<text x="{x + (cell - 6) / 2}" y="{y + (cell - 6) / 2 + 5}" fill="{ink}" '
                f'font-size="15" font-weight="700" text-anchor="middle">'
                f"{value:,}</text>"
            )
    axis: list[str] = []
    for index, label in enumerate(labels):
        axis.append(
            f'<text x="{left + index * cell + (cell - 6) / 2}" y="{top - 18}" fill="{MUTED}" '
            f'font-size="13" text-anchor="middle">{label}</text>'
        )
        axis.append(
            f'<text x="{left - 16}" y="{top + index * cell + (cell - 6) / 2 + 5}" fill="{MUTED}" '
            f'font-size="13" text-anchor="end">{label}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Segoe UI, system-ui, sans-serif">
  <rect width="100%" height="100%" fill="{BG}"/>
  <rect x="12" y="12" width="{width - 24}" height="{height - 24}" rx="16" fill="{SURFACE}" stroke="{BORDER}"/>
  <text x="{width / 2}" y="42" fill="{TEXT}" font-size="18" font-weight="700" text-anchor="middle">Karışıklık matrisi</text>
  <text x="{width / 2}" y="64" fill="{MUTED}" font-size="12" text-anchor="middle">CICIDS2017 ayrılmış akış testi</text>
  <text x="{left + (size * cell) / 2}" y="{height - 22}" fill="{ACCENT}" font-size="12" text-anchor="middle">Tahmin</text>
  <text x="28" y="{top + (size * cell) / 2}" fill="{ACCENT}" font-size="12" text-anchor="middle" transform="rotate(-90 28 {top + (size * cell) / 2})">Gerçek</text>
  {"".join(axis)}
  {"".join(cells)}
</svg>
"""


def export_confusion_matrix(metrics_path: Path, output_path: Path) -> Path:
    payload = json.loads(metrics_path.read_text(encoding="utf-8"))
    matrix = payload["confusion_matrix"]
    labels = [str(label) for label in payload.get("labels", list(LABELS))]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(confusion_matrix_svg(matrix, labels), encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metrics", type=Path, default=Path("artifacts/metrics.json"))
    parser.add_argument("--output", type=Path, default=Path("docs/figures/confusion-matrix.svg"))
    args = parser.parse_args()
    path = export_confusion_matrix(args.metrics, args.output)
    print(f"Yazıldı: {path}")


if __name__ == "__main__":
    main()
