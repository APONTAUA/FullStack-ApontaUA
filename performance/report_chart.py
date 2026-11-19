"""Generate a small SVG chart from a Locust summary CSV."""

import csv
import sys
from html import escape
from pathlib import Path


def main() -> None:
    source = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    with source.open(newline="", encoding="utf-8") as csv_file:
        rows = [row for row in csv.DictReader(csv_file) if row["Type"] == "GET"]

    width = 960
    left = 245
    bar_width = 520
    row_height = 72
    height = 150 + row_height * len(rows)
    max_latency = max(float(row["95%"] or 0) for row in rows) or 1
    scale = bar_width / max_latency
    parts = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}">'
        ),
        '<rect width="100%" height="100%" fill="#fff"/>',
        (
            "<style>text{font:14px sans-serif;fill:#202124}"
            ".title{font-size:20px;font-weight:700}.avg{fill:#4285f4}"
            ".p95{fill:#fbbc04}.grid{stroke:#dadce0;stroke-width:1}</style>"
        ),
        '<text x="24" y="32" class="title">Locust local run — latency by endpoint (ms)</text>',
        (
            '<rect x="24" y="51" width="14" height="14" class="avg"/>'
            '<text x="44" y="63">Average</text>'
        ),
        (
            '<rect x="132" y="51" width="14" height="14" class="p95"/>'
            '<text x="152" y="63">p95 (approx.)</text>'
        ),
    ]
    for tick in range(0, int(max_latency) + 1, max(1, int(max_latency // 5 or 1))):
        x = left + tick * scale
        parts.append(f'<line x1="{x:.1f}" y1="82" x2="{x:.1f}" y2="{height - 34}" class="grid"/>')
        parts.append(f'<text x="{x:.1f}" y="{height - 12}" text-anchor="middle">{tick}</text>')
    for index, row in enumerate(rows):
        y = 105 + row_height * index
        endpoint = escape(row["Name"])
        average = float(row["Average Response Time"] or 0)
        p95 = float(row["95%"] or 0)
        requests = int(row["Request Count"])
        failures = int(row["Failure Count"])
        parts.extend(
            [
                f'<text x="24" y="{y + 19}">{endpoint}</text>',
                (
                    f'<rect x="{left}" y="{y}" width="{average * scale:.1f}" '
                    'height="18" rx="3" class="avg"/>'
                ),
                (
                    f'<rect x="{left}" y="{y + 23}" width="{p95 * scale:.1f}" '
                    'height="18" rx="3" class="p95"/>'
                ),
                (
                    f'<text x="{left + bar_width + 24}" y="{y + 20}">'
                    f'{requests} requests · {failures} errors</text>'
                ),
            ]
        )
    parts.append("</svg>")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(parts), encoding="utf-8")


if __name__ == "__main__":
    main()
