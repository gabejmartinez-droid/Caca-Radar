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
