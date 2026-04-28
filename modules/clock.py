# -*- coding: utf-8 -*-
from PIL import ImageDraw, ImageFont
from datetime import datetime
from config import (
    FONT_TIME,
    FONT_DATE,
    FONT_LABEL,
    FONT_WEATHER,
    FONT_ICON,
    CLOCK_UPPER_ZONE,
    CLOCK_LOWER_ZONE,
    DISPLAY_W,
    DISPLAY_H,
    WMO_COLORS,
)

HALF_H = DISPLAY_H // 2


def load_fonts():
    return {
        "time": ImageFont.truetype(FONT_TIME, 72),
        "date": ImageFont.truetype(FONT_DATE, 28),
        "label": ImageFont.truetype(FONT_LABEL, 36),
        "weather": ImageFont.truetype(FONT_WEATHER, 36),
        "icon": ImageFont.truetype(FONT_ICON, 52),
    }


def text_w(text, font):
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def text_h(text, font):
    bbox = font.getbbox(text)
    return bbox[3] - bbox[1]


def draw_text_with_shadow(
    draw,
    pos,
    text,
    font,
    fill,
    shadow_color=(0, 0, 0),
    shadow_offset=(0, 1),
    shadow_blur=1,
):
    """Draw text with shadow"""
    x, y = pos
    sx, sy = shadow_offset

    # Shadow (multi-layer offset to simulate blur)
    for i in range(shadow_blur, 0, -1):
        alpha = int(180 / i)  # Outer layers are more transparent
        blur_color = shadow_color + (alpha,)
        # Create temporary offset layers for shadow
        for dx in range(-i, i + 1, max(1, i - 1)):
            for dy in range(-i, i + 1, max(1, i - 1)):
                draw.text(
                    (x + sx + dx, y + sy + dy), text, font=font, fill=shadow_color
                )

    # Main text
    draw.text((x, y), text, font=font, fill=fill)


def render_clock(bg_image, fonts, upper_weather, lower_weather):
    """Draw dual-zone clock on background image and return the composited Image"""
    now_top = datetime.now(CLOCK_UPPER_ZONE["tz"])
    now_bottom = datetime.now(CLOCK_LOWER_ZONE["tz"])

    image = bg_image.copy()
    draw = ImageDraw.Draw(image)

    # ── Divider ───────────────────────────────────────────
    draw.line([(30, HALF_H), (DISPLAY_W - 30, HALF_H)], fill=(255, 255, 255), width=1)

    # ── Top half ─────────────────────────────────────────────
    _draw_half(
        draw,
        fonts,
        label=CLOCK_UPPER_ZONE["label"],
        time_str=now_top.strftime("%H:%M:%S"),
        date_str=now_top.strftime("%Y-%m-%d  %a"),
        weather=upper_weather,
        y_offset=0,
        time_color=(255, 255, 255),
    )

    # ── Bottom half ──────────────────────────────────────────
    _draw_half(
        draw,
        fonts,
        label=CLOCK_LOWER_ZONE["label"],
        time_str=now_bottom.strftime("%H:%M:%S"),
        date_str=now_bottom.strftime("%Y-%m-%d  %a"),
        weather=lower_weather,
        y_offset=HALF_H,
        time_color=(255, 255, 255),
    )

    return image


def _draw_half(draw, fonts, label, time_str, date_str, weather, y_offset, time_color):
    W = DISPLAY_W
    H = HALF_H
    pad = 12

    temp_str = f"{weather['temp']}\u00b0C"
    humi_str = f"{weather['humidity']}%"
    icon_str = weather["icon"]

    # ── Vertical layout (centered overall) ──────────────────
    # Measure actual height of each element
    label_h = fonts["label"].getbbox(label)[3]
    time_h = fonts["time"].getbbox(time_str)[3]
    date_h = fonts["date"].getbbox(date_str)[3]
    icon_bbox = fonts["icon"].getbbox(icon_str)
    humi_bbox = fonts["weather"].getbbox(humi_str)
    temp_bbox = fonts["weather"].getbbox(temp_str)
    weather_h = max(icon_bbox[3], temp_bbox[3], humi_bbox[3])

    label_gap = 16
    gap = 6
    total_h = label_h + label_gap + time_h + gap + date_h + gap + weather_h
    top = y_offset + (H - total_h) // 2

    # City label (centered)
    lw = text_w(label, fonts["label"])
    draw_text_with_shadow(
        draw,
        pos=((W - lw) // 2, top),
        text=label,
        font=fonts["label"],
        fill=(255, 255, 255),
        shadow_offset=(0, 1),
    )

    # Large time display (centered, Rajdhani)
    tw = text_w(time_str, fonts["time"])
    draw_text_with_shadow(
        draw,
        pos=((W - tw) // 2, top + label_h + label_gap),
        text=time_str,
        font=fonts["time"],
        fill=time_color,
        shadow_offset=(0, 1),
    )

    # Date (centered)
    dw = text_w(date_str, fonts["date"])
    draw_text_with_shadow(
        draw,
        pos=((W - dw) // 2, top + label_h + label_gap + time_h + gap),
        text=date_str,
        font=fonts["date"],
        fill=(255, 255, 255),
        shadow_offset=(0, 1),
    )

    # ── Weather row (left: temp  center: icon  right: humidity) ──
    wy = top + label_h + label_gap + time_h + gap + date_h + gap

    temp_h = temp_bbox[3]
    humi_h = humi_bbox[3]
    icon_h = icon_bbox[3]

    # Use tallest element as baseline, vertically center-align others
    row_h = max(temp_h, humi_h, icon_h)

    def draw_at_vcenter(text, font, x, fill, elem_h):
        # Vertically center each element within row_h
        y = wy + (row_h - elem_h) // 2
        draw_text_with_shadow(draw, (x, y), text, font, fill)

    # Left: temperature
    draw_at_vcenter(temp_str, fonts["weather"], pad, (255, 255, 255), temp_h)

    # Right: humidity
    hw = text_w(humi_str, fonts["weather"])
    draw_at_vcenter(humi_str, fonts["weather"], W - hw - pad, (255, 255, 255), humi_h)

    # Center: icon
    iw = text_w(icon_str, fonts["icon"])
    wmo_code = weather.get("code", 0)
    icon_color = WMO_COLORS.get(wmo_code, (255, 255, 255))
    draw_at_vcenter(icon_str, fonts["icon"], (W - iw) // 2, icon_color, icon_h)
