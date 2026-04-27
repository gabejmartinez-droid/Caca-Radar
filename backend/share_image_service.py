from __future__ import annotations

import io
from html import escape
from typing import Iterable

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - production installs pillow, local fallback stays SVG
    Image = None
    ImageDraw = None
    ImageFont = None


IMAGE_WIDTH = 1200
IMAGE_HEIGHT = 630
LOCATION_PNG_SCALE = 2

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

LOCATION_HEADLINE = "¿Cuánta caca de perro hay en nuestras aceras?"
LOCATION_SUBTITLE = "Mapa colaborativo"
LOCATION_FOOTER = "Reporta. Mejora. Respeta."


def get_share_image_media_type() -> str:
    return "image/png" if Image is not None else "image/svg+xml"


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


def _get_font(size: int, bold: bool = False):
    if ImageFont is None:
        return None
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/SFNS.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def _hex_to_rgb(value: str):
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def _draw_text(draw, xy, text, *, font, fill, anchor=None):
    draw.text(xy, str(text or ""), font=font, fill=fill, anchor=anchor)


def _render_gradient_background(image):
    top = _hex_to_rgb(BG_TOP)
    bottom = _hex_to_rgb(BG_BOTTOM)
    draw = ImageDraw.Draw(image)
    for y in range(IMAGE_HEIGHT):
        ratio = y / max(IMAGE_HEIGHT - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (IMAGE_WIDTH, y)], fill=color)


def _rounded(draw, box, radius, fill, outline=None, width=1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def _draw_map_png(draw, summary: dict, scale: int = 1):
    map_x, map_y, map_w, map_h = 64 * scale, 388 * scale, 1072 * scale, 162 * scale
    _rounded(draw, (map_x, map_y, map_x + map_w, map_y + map_h), 20, MAP_BG)
    draw.polygon(
        [
            (map_x + map_w * 0.72, map_y),
            (map_x + map_w, map_y),
            (map_x + map_w, map_y + map_h),
            (map_x + map_w * 0.84, map_y + map_h * 0.72),
        ],
        fill=MAP_WATER,
    )
    for offset in range(20, map_w, 58):
        draw.line(
            [(map_x + offset, map_y), (map_x + offset - 110, map_y + map_h)],
            fill=MAP_ROAD,
            width=7,
        )
    for offset in range(10, map_h, 54):
        draw.line(
            [(map_x, map_y + offset), (map_x + map_w, map_y + offset + 26)],
            fill=MAP_ROAD,
            width=7,
        )

    bounds = summary.get("map_bounds") or {}
    south, north = bounds.get("south"), bounds.get("north")
    west, east = bounds.get("west"), bounds.get("east")
    points = summary.get("preview_points") or []
    normalized = []
    if points and None not in {south, north, west, east} and east != west and north != south:
        for point in points[:40]:
            px = map_x + 36 + ((point["lng"] - west) / (east - west)) * (map_w - 72)
            py = map_y + 24 + (1 - ((point["lat"] - south) / (north - south))) * (map_h - 48)
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
        draw.polygon(region, fill=MAP_REGION, outline="#E8A5A0")
        colors = {"fresh": FRESH, "older": OLDER, "fossil": FOSSIL}
        for px, py, bucket in normalized:
            color = colors.get(bucket, FOSSIL)
            draw.ellipse((px - 8, py - 8, px + 8, py + 8), fill=color, outline="white", width=2)

    title_font = _get_font(28 * scale, bold=True)
    barrio_font = _get_font(20 * scale)
    _draw_text(draw, (map_x + 18 * scale, map_y + 10 * scale), _truncate(str(summary.get("city", "")).upper(), 24), font=title_font, fill=TEXT_DARK)
    if summary.get("barrio"):
        _draw_text(draw, (map_x + 18 * scale, map_y + 44 * scale), _truncate(summary.get("barrio", ""), 28), font=barrio_font, fill=TEXT_MUTED)


def _image_bytes(image) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def _stat_box_png(draw, x: int, label: str, value: str, note: str, color: str, scale: int = 1):
    top = 236 * scale
    height = 132 * scale
    width = 252 * scale
    _rounded(draw, (x, top, x + width, top + height), 22 * scale, CARD_BG)
    label_font = _get_font(24 * scale)
    value_font = _get_font(52 * scale, bold=True)
    note_font = _get_font(18 * scale)
    _draw_text(draw, (x + 18 * scale, top + 18 * scale), label, font=label_font, fill=TEXT_DARK)
    _draw_text(draw, (x + 18 * scale, top + 56 * scale), value, font=value_font, fill=color)
    _draw_text(draw, (x + 18 * scale, top + 104 * scale), note, font=note_font, fill=TEXT_MUTED)


def build_rankings_share_png(title: str, subtitle: str, rows: Iterable[dict], footer: str = "Caca Radar") -> bytes:
    if Image is not None:
        rows = list(rows)[:5]
        image = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), BG_TOP)
        _render_gradient_background(image)
        draw = ImageDraw.Draw(image)
        _rounded(draw, (40, 38, 220, 110), 26, ACCENT_SOFT)
        _draw_text(draw, (62, 56), "Caca Radar", font=_get_font(28, bold=True), fill=ACCENT)
        _draw_text(draw, (40, 122), _truncate(title, 34), font=_get_font(58, bold=True), fill=TEXT_DARK)
        _draw_text(draw, (40, 190), _truncate(subtitle, 70), font=_get_font(26), fill=TEXT_MUTED)
        top = 276
        for index, row in enumerate(rows):
            y = top + index * 80
            _rounded(draw, (40, y, 1160, y + 66), 24, CARD_BG)
            _rounded(draw, (58, y + 13, 104, y + 53), 18, ACCENT_SOFT)
            _draw_text(draw, (81, y + 22), str(row.get("rank", index + 1)), font=_get_font(28, bold=True), fill=ACCENT, anchor="ma")
            _draw_text(draw, (126, y + 10), _truncate(row.get("label", ""), 34), font=_get_font(30, bold=True), fill=TEXT_DARK)
            _draw_text(draw, (126, y + 38), _truncate(row.get("meta", ""), 52), font=_get_font(20), fill=TEXT_MUTED)
            _draw_text(draw, (1102, y + 19), str(row.get("value", "")), font=_get_font(28, bold=True), fill=ACCENT, anchor="ra")
        _draw_text(draw, (40, 568), _truncate(footer, 80), font=_get_font(20), fill=TEXT_MUTED)
        return _image_bytes(image)

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
  <rect x="{x}" y="236" width="252" height="132" rx="22" fill="{CARD_BG}"/>
  <text x="{x + 18}" y="266" font-size="24" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(label)}</text>
  <text x="{x + 18}" y="324" font-size="52" font-weight="800" fill="{color}" font-family="Arial, Helvetica, sans-serif">{escape(value)}</text>
  <text x="{x + 18}" y="352" font-size="18" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(note)}</text>
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


def build_location_share_card_image(summary: dict) -> bytes:
    if Image is not None:
        scale = LOCATION_PNG_SCALE
        image = Image.new("RGB", (IMAGE_WIDTH * scale, IMAGE_HEIGHT * scale), BG_TOP)
        _render_gradient_background(image)
        draw = ImageDraw.Draw(image)
        _rounded(draw, (28 * scale, 24 * scale, 1172 * scale, 606 * scale), 34 * scale, "#FFFDFC", outline="#E7DED8", width=3 * scale)
        location = summary.get("display_label") or summary.get("city", "")
        _draw_text(draw, (74 * scale, 46 * scale), "Caca Radar", font=_get_font(28 * scale, bold=True), fill=ACCENT)
        _draw_text(draw, (278 * scale, 48 * scale), LOCATION_SUBTITLE, font=_get_font(20 * scale), fill=TEXT_MUTED)
        _draw_text(draw, (74 * scale, 94 * scale), LOCATION_HEADLINE, font=_get_font(40 * scale, bold=True), fill="#A21414")
        _draw_text(draw, (72 * scale, 156 * scale), _truncate(location, 24), font=_get_font(72 * scale, bold=True), fill=TEXT_DARK)
        recent = summary.get("recent_report_count", summary.get("fresh_count", summary.get("fresh_reports", 0)))
        _draw_text(draw, (72 * scale, 222 * scale), f"{recent} reportes recientes", font=_get_font(46 * scale, bold=True), fill=ACCENT)
        _draw_text(draw, (72 * scale, 268 * scale), summary.get("time_window_label", "últimas 24 h"), font=_get_font(24 * scale), fill=TEXT_MUTED)
        _draw_text(draw, (72 * scale, 314 * scale), f"{summary.get('fresh_count', summary.get('fresh_reports', 0))} frescos", font=_get_font(34 * scale, bold=True), fill=FRESH)
        _draw_text(draw, (394 * scale, 314 * scale), f"{summary.get('old_count', summary.get('older_reports', 0))} antiguos", font=_get_font(34 * scale, bold=True), fill=OLDER)
        _draw_text(draw, (786 * scale, 314 * scale), f"{summary.get('fossil_count', summary.get('fossil_reports', 0))} fósiles", font=_get_font(34 * scale, bold=True), fill=FOSSIL)
        _stat_box_png(draw, 64 * scale, "Activos", str(summary.get("active_report_count", summary.get("total_active_reports", 0))), "", FOSSIL, scale)
        _stat_box_png(draw, 338 * scale, "Frescos", str(summary.get("fresh_count", summary.get("fresh_reports", 0))), "≤ 24h", FRESH, scale)
        _stat_box_png(draw, 612 * scale, "Antiguos", str(summary.get("old_count", summary.get("older_reports", 0))), "1–7 días", OLDER, scale)
        _stat_box_png(draw, 886 * scale, "Fósiles", str(summary.get("fossil_count", summary.get("fossil_reports", 0))), "> 7 días", FOSSIL, scale)
        _draw_map_png(draw, summary, scale)
        _draw_text(draw, (74 * scale, 582 * scale), "Caca Radar", font=_get_font(28 * scale, bold=True), fill=TEXT_DARK)
        _draw_text(draw, (274 * scale, 586 * scale), f"{LOCATION_SUBTITLE} · {LOCATION_FOOTER}", font=_get_font(20 * scale), fill=TEXT_MUTED)
        return _image_bytes(image)

    location = summary.get("display_label") or summary.get("city", "")
    recent = summary.get("recent_report_count", summary.get("fresh_count", summary.get("fresh_reports", 0)))

    parts = [_svg_header()]
    parts.append(
        f"""
  <rect x="28" y="24" width="1144" height="582" rx="34" fill="#FFFDFC" stroke="#E7DED8" stroke-width="3" filter="url(#shadow)"/>
  <text x="74" y="54" font-size="24" font-weight="800" fill="{ACCENT}" font-family="Arial, Helvetica, sans-serif">Caca Radar</text>
  <text x="248" y="56" font-size="16" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{LOCATION_SUBTITLE}</text>
  <text x="78" y="104" font-size="40" font-weight="800" fill="#A21414" font-family="Arial, Helvetica, sans-serif">{LOCATION_HEADLINE}</text>
  <text x="72" y="172" font-size="72" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">{escape(_truncate(location, 24))}</text>
  <text x="72" y="234" font-size="46" font-weight="800" fill="{ACCENT}" font-family="Arial, Helvetica, sans-serif">{recent} reportes recientes</text>
  <text x="72" y="270" font-size="24" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{escape(summary.get("time_window_label", "últimas 24 h"))}</text>
  <text x="72" y="316" font-size="34" font-weight="800" fill="{FRESH}" font-family="Arial, Helvetica, sans-serif">{summary.get("fresh_count", summary.get("fresh_reports", 0))} frescos</text>
  <text x="394" y="316" font-size="34" font-weight="800" fill="{OLDER}" font-family="Arial, Helvetica, sans-serif">{summary.get("old_count", summary.get("older_reports", 0))} antiguos</text>
  <text x="786" y="316" font-size="34" font-weight="800" fill="{FOSSIL}" font-family="Arial, Helvetica, sans-serif">{summary.get("fossil_count", summary.get("fossil_reports", 0))} fósiles</text>
"""
    )
    parts.append(_stat_box(64, "Activos", str(summary.get("active_report_count", summary.get("total_active_reports", 0))), "", FOSSIL))
    parts.append(_stat_box(346, "Frescos", str(summary.get("fresh_count", summary.get("fresh_reports", 0))), "≤ 24h", FRESH))
    parts.append(_stat_box(628, "Antiguos", str(summary.get("old_count", summary.get("older_reports", 0))), "1–7 días", OLDER))
    parts.append(_stat_box(910, "Fósiles", str(summary.get("fossil_count", summary.get("fossil_reports", 0))), "> 7 días", FOSSIL))
    parts.append(_build_map_svg(summary))
    parts.append(
        f"""
  <text x="74" y="590" font-size="26" font-weight="800" fill="{TEXT_DARK}" font-family="Arial, Helvetica, sans-serif">Caca Radar</text>
  <text x="274" y="592" font-size="18" fill="{TEXT_MUTED}" font-family="Arial, Helvetica, sans-serif">{LOCATION_SUBTITLE} · {LOCATION_FOOTER}</text>
"""
    )
    parts.append(_svg_footer())
    return "".join(parts).encode("utf-8")


def build_barrio_snapshot_png(summary: dict) -> bytes:
    return build_location_share_card_image(summary)
