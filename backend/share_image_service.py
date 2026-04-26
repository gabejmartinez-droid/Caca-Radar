from __future__ import annotations

from html import escape
from typing import Iterable


IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 630

BG_TOP = "#FFF7F2"
BG_BOTTOM = "#FFE1D6"
TEXT_DARK = "#2B2D42"
TEXT_MUTED = "#5C677D"
ACCENT = "#FF6B6B"
ACCENT_SOFT = "#FFE7E1"
CARD_BG = "#FFFFFF"
FRESH = "#4CAF50"
OLDER = "#FF9800"
FOSSIL = "#E53935"
MAP_BG = "#F7F0E6"
MAP_WATER = "#C9E7FF"
MAP_ROAD = "#FFFFFF"
MAP_REGION = "#FAD6D0"


def _truncate(text: str, max_chars: int) -> str:
    text = str(text or "")
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _svg_header() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {IMAGE_WIDTH} {IMAGE_HEIGHT}" width="{IMAGE_WIDTH}" height="{IMAGE_HEIGHT}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{BG_TOP}"/>
      <stop offset="100%" stop-color="{BG_BOTTOM}"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="10" stdDeviation="16" flood-color="#000000" flood-opacity="0.12"/>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
"""


def _svg_footer() -> str:
    return "</svg>"


def build_rankings_share_png(title: str, subtitle: str, rows: Iterable[dict], footer: str = "Caca Radar") -> bytes:
    rows = list(rows)[:5]
    parts = [_svg_header()]
    parts.append(
        f"""
  <rect x="40" y="38" width="180" height="72" rx="26" fill="{ACCENT_SOFT}"/>
  <text x="62" y="84" font-size="28" font-weight="800" fill="{ACCENT}" font-family="Arial, Helvetica, sans-serif">Caca Radar</text>
  <text x="40" y="145" font-size="58" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(title, 34))}</text>
  <text x="40" y="214" font-size="26" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(subtitle, 70))}</text>
"""
    )
    top = 276
    for index, row in enumerate(rows):
        y = top + index * 80
        parts.append(
            f"""
  <rect x="40" y="{y}" width="1120" height="66" rx="24" fill="{CARD_BG}"/>
  <rect x="58" y="{y + 13}" width="46" height="40" rx="18" fill="{ACCENT_SOFT}"/>
  <text x="81" y="{y + 40}" text-anchor="middle" font-size="28" font-weight="800" fill="{ACCENT}" font-family="Arial, Helvetica, sans-serif">{escape(str(row.get("rank", index + 1)))}</text>
  <text x="126" y="{y + 30}" font-size="30" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(row.get("label", ""), 34))}</text>
  <text x="126" y="{y + 54}" font-size="20" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(row.get("meta", ""), 52))}</text>
  <text x="1102" y="{y + 39}" text-anchor="end" font-size="28" font-weight="800" fill="{ACCENT}" font-family="Arial, Helvetica, sans-serif">{escape(str(row.get("value", "")))}</text>
"""
        )
    parts.append(
        f'<text x="40" y="588" font-size="20" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(footer, 80))}</text>'
    )
    parts.append(_svg_footer())
    return "".join(parts).encode("utf-8")


def _stat_box(x: int, label: str, value: str, note: str, color: str) -> str:
    return f"""
  <rect x="{x}" y="248" width="266" height="166" rx="22" fill="{CARD_BG}"/>
  <text x="{x + 18}" y="282" font-size="22" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(label)}</text>
  <text x="{x + 18}" y="352" font-size="42" font-weight="800" fill="{color}" font-family="Arial, Helvetica, sans-serif">{escape(value)}</text>
  <text x="{x + 18}" y="388" font-size="18" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(note)}</text>
"""


def _build_map_svg(summary: dict) -> str:
    map_x, map_y, map_w, map_h = 64, 434, 1072, 130
    parts = [f'<g transform="translate({map_x} {map_y})">']
    parts.append(f'<rect width="{map_w}" height="{map_h}" rx="20" fill="{MAP_BG}"/>')
    parts.append(f'<polygon points="{map_w * 0.72},0 {map_w},0 {map_w},{map_h} {map_w * 0.84},{map_h * 0.72}" fill="{MAP_WATER}"/>')
    for offset in range(20, map_w, 58):
        parts.append(f'<line x1="{offset}" y1="0" x2="{offset - 110}" y2="{map_h}" stroke="{MAP_ROAD}" stroke-width="7"/>')
    for offset in range(10, map_h, 54):
        parts.append(f'<line x1="0" y1="{offset}" x2="{map_w}" y2="{offset + 26}" stroke="{MAP_ROAD}" stroke-width="7"/>')

    bounds = summary.get("map_bounds") or {}
    south, north = bounds.get("south"), bounds.get("north")
    west, east = bounds.get("west"), bounds.get("east")
    points = summary.get("preview_points") or []
    normalized = []
    if points and None not in {south, north, west, east} and east != west and north != south:
        for point in points[:40]:
            px = 36 + ((point["lng"] - west) / (east - west)) * (map_w - 72)
            py = 24 + (1 - ((point["lat"] - south) / (north - south))) * (map_h - 48)
            normalized.append((px, py, point.get("bucket", "fossil")))

    if normalized:
        min_x = min(p[0] for p in normalized)
        max_x = max(p[0] for p in normalized)
        min_y = min(p[1] for p in normalized)
        max_y = max(p[1] for p in normalized)
        region = [
            (min_x - 34, min_y + 18),
            ((min_x + max_x) / 2, min_y - 24),
            (max_x + 28, min_y + 24),
            (max_x + 16, max_y - 28),
            ((min_x + max_x) / 2, max_y + 26),
            (min_x - 28, max_y - 8),
        ]
        parts.append(
            '<polygon points="' +
            " ".join(f"{x:.1f},{y:.1f}" for x, y in region) +
            f'" fill="{MAP_REGION}" stroke="#E8A5A0" stroke-width="2"/>'
        )
        colors = {"fresh": FRESH, "older": OLDER, "fossil": FOSSIL}
        for px, py, bucket in normalized:
            color = colors.get(bucket, FOSSIL)
            parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="8.5" fill="{color}" stroke="white" stroke-width="2"/>')

    parts.append(f'<text x="18" y="30" font-size="28" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(str(summary.get("city", "")).upper(), 24))}</text>')
    if summary.get("barrio"):
        parts.append(f'<text x="18" y="54" font-size="18" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(summary.get("barrio", ""), 28))}</text>')
    parts.append("</g>")
    return "".join(parts)


def build_barrio_snapshot_png(summary: dict) -> bytes:
    location = summary.get("city", "")
    if summary.get("barrio"):
        location = f'{summary.get("city", "")} — {summary.get("barrio", "")}'

    parts = [_svg_header()]
    parts.append(
        f"""
  <rect x="28" y="24" width="1144" height="582" rx="34" fill="#FFFDFC" stroke="#E7DED8" stroke-width="3" filter="url(#shadow)"/>
  <text x="82" y="84" font-size="32" font-weight="800" fill="#A21414" font-family="Arial, Helvetica, sans-serif">¿Cuánta caca de perro hay en nuestras aceras?</text>
  <text x="72" y="152" font-size="54" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(location, 28))}</text>
  <text x="166" y="224" font-size="34" font-weight="800" fill="{FRESH}" font-family="Arial, Helvetica, sans-serif">{summary.get("fresh_reports", 0)}</text>
  <text x="240" y="228" font-size="26" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">frescos,</text>
  <text x="418" y="224" font-size="34" font-weight="800" fill="{OLDER}" font-family="Arial, Helvetica, sans-serif">{summary.get("older_reports", 0)}</text>
  <text x="500" y="228" font-size="26" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">antiguos,</text>
  <text x="744" y="224" font-size="34" font-weight="800" fill="{FOSSIL}" font-family="Arial, Helvetica, sans-serif">{summary.get("fossil_reports", 0)}</text>
  <text x="834" y="228" font-size="26" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">fósiles</text>
"""
    )
    parts.append(_stat_box(64, "Reportes activos", str(summary.get("total_active_reports", 0)), "", FOSSIL))
    parts.append(_stat_box(346, "Frescos", str(summary.get("fresh_reports", 0)), "(≤ 48h)", FRESH))
    parts.append(_stat_box(628, "Antiguos", str(summary.get("older_reports", 0)), "(2–6 días)", OLDER))
    parts.append(_stat_box(910, "Fósiles", str(summary.get("fossil_reports", 0)), "(≥ 7 días)", FOSSIL))
    parts.append(_build_map_svg(summary))
    parts.append(
        f"""
  <text x="74" y="590" font-size="26" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">Caca Radar</text>
  <text x="274" y="592" font-size="18" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">Mapa colaborativo · Reporta. Mejora. Respeta.</text>
"""
    )
    parts.append(_svg_footer())
    return "".join(parts).encode("utf-8")
