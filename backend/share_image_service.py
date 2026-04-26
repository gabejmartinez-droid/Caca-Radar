from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


IMAGE_SIZE = (1200, 630)
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


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if bold:
      candidates.extend([
          "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
          "/System/Library/Fonts/Supplemental/Helvetica.ttc",
      ])
    else:
      candidates.extend([
          "/System/Library/Fonts/Supplemental/Arial.ttf",
          "/System/Library/Fonts/Supplemental/Helvetica.ttc",
      ])

    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def _draw_vertical_gradient(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    top = ImageColor.hex_to_rgb(BG_TOP)
    bottom = ImageColor.hex_to_rgb(BG_BOTTOM)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)


class ImageColor:
    @staticmethod
    def hex_to_rgb(value: str) -> tuple[int, int, int]:
        value = value.lstrip("#")
        return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def _truncate(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    ellipsis = "..."
    trimmed = text
    while trimmed and draw.textlength(trimmed + ellipsis, font=font) > max_width:
        trimmed = trimmed[:-1]
    return (trimmed + ellipsis) if trimmed else ellipsis


def build_rankings_share_png(
    title: str,
    subtitle: str,
    rows: Iterable[dict],
    footer: str = "Caca Radar",
) -> bytes:
    image = Image.new("RGB", IMAGE_SIZE, BG_TOP)
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, *IMAGE_SIZE)

    width, height = IMAGE_SIZE
    title_font = _load_font(58, bold=True)
    subtitle_font = _load_font(26, bold=False)
    brand_font = _load_font(28, bold=True)
    row_rank_font = _load_font(28, bold=True)
    row_label_font = _load_font(30, bold=True)
    row_meta_font = _load_font(20, bold=False)
    row_value_font = _load_font(28, bold=True)
    footer_font = _load_font(20, bold=False)

    draw.rounded_rectangle((40, 38, 220, 110), radius=26, fill=ACCENT_SOFT)
    draw.text((62, 58), "Caca Radar", font=brand_font, fill=ACCENT)

    draw.text((40, 145), title, font=title_font, fill=TEXT_DARK)
    draw.text((40, 214), subtitle, font=subtitle_font, fill=TEXT_MUTED)

    top = 276
    row_height = 66
    row_gap = 14
    rows = list(rows)[:5]
    for index, row in enumerate(rows):
        y1 = top + index * (row_height + row_gap)
        y2 = y1 + row_height
        draw.rounded_rectangle((40, y1, width - 40, y2), radius=24, fill=CARD_BG)
        draw.rounded_rectangle((58, y1 + 13, 104, y2 - 13), radius=18, fill=ACCENT_SOFT)
        draw.text((74, y1 + 19), str(row.get("rank", index + 1)), font=row_rank_font, fill=ACCENT)

        label = _truncate(str(row.get("label", "")), row_label_font, 620, draw)
        meta = _truncate(str(row.get("meta", "")), row_meta_font, 620, draw) if row.get("meta") else ""
        draw.text((126, y1 + 10), label, font=row_label_font, fill=TEXT_DARK)
        if meta:
            draw.text((126, y1 + 39), meta, font=row_meta_font, fill=TEXT_MUTED)

        value = str(row.get("value", ""))
        value_width = draw.textlength(value, font=row_value_font)
        draw.text((width - 58 - value_width, y1 + 18), value, font=row_value_font, fill=ACCENT)

    draw.text((40, height - 42), footer, font=footer_font, fill=TEXT_MUTED)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _draw_stat_box(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], label: str, value: str, note: str, color: str) -> None:
    x1, y1, x2, y2 = box
    label_font = _load_font(22, bold=False)
    value_font = _load_font(42, bold=True)
    note_font = _load_font(18, bold=False)
    draw.rounded_rectangle(box, radius=22, fill=CARD_BG)
    draw.text((x1 + 18, y1 + 16), label, font=label_font, fill=TEXT_DARK)
    draw.text((x1 + 18, y1 + 52), value, font=value_font, fill=color)
    if note:
        draw.text((x1 + 18, y2 - 30), note, font=note_font, fill=TEXT_MUTED)


def _draw_map_panel(draw: ImageDraw.ImageDraw, image: Image.Image, box: tuple[int, int, int, int], summary: dict) -> None:
    x1, y1, x2, y2 = box
    panel = Image.new("RGB", (x2 - x1, y2 - y1), MAP_BG)
    panel_draw = ImageDraw.Draw(panel)

    # soft "water" block to keep the map from feeling too flat
    panel_draw.polygon(
        [(panel.width * 0.72, 0), (panel.width, 0), (panel.width, panel.height), (panel.width * 0.84, panel.height * 0.72)],
        fill=MAP_WATER,
    )

    # simple road grid
    for offset in range(20, panel.width, 58):
        panel_draw.line([(offset, 0), (offset - 110, panel.height)], fill=MAP_ROAD, width=7)
    for offset in range(10, panel.height, 54):
        panel_draw.line([(0, offset), (panel.width, offset + 26)], fill=MAP_ROAD, width=7)

    bounds = summary.get("map_bounds") or {}
    south = bounds.get("south")
    north = bounds.get("north")
    west = bounds.get("west")
    east = bounds.get("east")
    points = summary.get("preview_points") or []

    if points and None not in {south, north, west, east} and east != west and north != south:
        pad_x = 36
        pad_y = 24
        normalized = []
        for point in points[:40]:
            px = pad_x + ((point["lng"] - west) / (east - west)) * (panel.width - pad_x * 2)
            py = pad_y + (1 - ((point["lat"] - south) / (north - south))) * (panel.height - pad_y * 2)
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
            panel_draw.polygon(region, fill=MAP_REGION, outline="#E8A5A0")

            dot_colors = {"fresh": FRESH, "older": OLDER, "fossil": FOSSIL}
            for px, py, bucket in normalized:
                color = dot_colors.get(bucket, FOSSIL)
                panel_draw.ellipse((px - 9, py - 9, px + 9, py + 9), fill=color, outline="white", width=2)

    label_font = _load_font(28, bold=True)
    city_font = _load_font(18, bold=False)
    panel_draw.text((18, 14), str(summary.get("city", "")).upper(), font=label_font, fill=TEXT_DARK)
    if summary.get("barrio"):
        panel_draw.text((18, 48), str(summary["barrio"]), font=city_font, fill=TEXT_MUTED)

    image.paste(panel, box)


def build_barrio_snapshot_png(summary: dict) -> bytes:
    image = Image.new("RGB", IMAGE_SIZE, BG_TOP)
    draw = ImageDraw.Draw(image)
    _draw_vertical_gradient(draw, *IMAGE_SIZE)

    title_font = _load_font(32, bold=True)
    location_font = _load_font(54, bold=True)
    summary_font = _load_font(26, bold=False)
    footer_font = _load_font(18, bold=False)

    draw.rounded_rectangle((28, 24, 1172, 606), radius=34, fill="#FFFDFC", outline="#E7DED8", width=3)
    draw.text((82, 54), "¿Cuánta caca de perro hay en nuestras aceras?", font=title_font, fill="#A21414")

    location = summary.get("city", "")
    if summary.get("barrio"):
        location = f'{summary.get("city", "")} — {summary.get("barrio", "")}'
    draw.text((72, 118), location, font=location_font, fill=TEXT_DARK)

    line_y = 190
    draw.text((166, line_y), str(summary.get("fresh_reports", 0)), font=_load_font(34, bold=True), fill=FRESH)
    draw.text((240, line_y + 4), "frescos,", font=summary_font, fill=TEXT_DARK)
    draw.text((418, line_y), str(summary.get("older_reports", 0)), font=_load_font(34, bold=True), fill=OLDER)
    draw.text((500, line_y + 4), "antiguos,", font=summary_font, fill=TEXT_DARK)
    draw.text((744, line_y), str(summary.get("fossil_reports", 0)), font=_load_font(34, bold=True), fill=FOSSIL)
    draw.text((834, line_y + 4), "fósiles", font=summary_font, fill=TEXT_DARK)

    stat_y1, stat_y2 = 248, 414
    widths = [(64, 330), (346, 612), (628, 894), (910, 1136)]
    _draw_stat_box(draw, (widths[0][0], stat_y1, widths[0][1], stat_y2), "Reportes activos", str(summary.get("total_active_reports", 0)), "", FOSSIL)
    _draw_stat_box(draw, (widths[1][0], stat_y1, widths[1][1], stat_y2), "Frescos", str(summary.get("fresh_reports", 0)), "(≤ 48h)", FRESH)
    _draw_stat_box(draw, (widths[2][0], stat_y1, widths[2][1], stat_y2), "Antiguos", str(summary.get("older_reports", 0)), "(2–6 días)", OLDER)
    _draw_stat_box(draw, (widths[3][0], stat_y1, widths[3][1], stat_y2), "Fósiles", str(summary.get("fossil_reports", 0)), "(≥ 7 días)", FOSSIL)

    _draw_map_panel(draw, image, (64, 434, 1136, 564), summary)

    draw.text((74, 576), "Caca Radar", font=_load_font(26, bold=True), fill=TEXT_DARK)
    draw.text((274, 580), "Mapa colaborativo · Reporta. Mejora. Respeta.", font=footer_font, fill=TEXT_MUTED)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()
