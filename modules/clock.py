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
    HALF_H,
    WMO_COLORS,
)

# ── Layout constants ─────────────────────────────────────────
PAD = 36  # horizontal padding for weather row
GAP = 4  # gap between elements
SHADOW_PAD = 2  # extra pixels above/below text strip for shadow coverage


def load_fonts():
    return {
        "time": ImageFont.truetype(FONT_TIME, 66),
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
    shadow_color=(130, 130, 130),
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


def _calc_layout(fonts, label, time_str, date_str, weather, y_offset):
    """Calculate y-positions for all elements in one half."""
    temp_str = f"{weather['temp']}\u00b0C"
    humi_str = f"{weather['humidity']}%"
    icon_str = weather["icon"]

    label_h = fonts["label"].getbbox(label)[3]
    time_h = fonts["time"].getbbox(time_str)[3]
    date_h = fonts["date"].getbbox(date_str)[3]
    weather_h = max(
        fonts["icon"].getbbox(icon_str)[3],
        fonts["weather"].getbbox(temp_str)[3],
        fonts["weather"].getbbox(humi_str)[3],
    )

    total_h = label_h + GAP + time_h + GAP + date_h + GAP + weather_h
    top = y_offset + (HALF_H - total_h) // 2

    return {
        "top": top,
        "label_h": label_h,
        "time_y": top + label_h + GAP,
        "time_h": time_h,
        "date_y": top + label_h + GAP + time_h + GAP,
        "date_h": date_h,
        "weather_y": top + label_h + GAP + time_h + GAP + date_h + GAP,
        "weather_h": weather_h,
    }


def render_clock(
    bg_image,
    fonts,
    upper_weather,
    lower_weather,
    upper_time_str=None,
    upper_date_str=None,
    lower_time_str=None,
    lower_date_str=None,
):
    """Draw dual-zone clock on background image and return the composited Image.
    Pass pre-captured time/date strings to ensure display matches state tracking."""
    now_top = datetime.now(CLOCK_UPPER_ZONE["tz"])
    now_bottom = datetime.now(CLOCK_LOWER_ZONE["tz"])

    image = bg_image.copy()
    draw = ImageDraw.Draw(image)

    # ── Divider ───────────────────────────────────────────
    # draw.line([(30, HALF_H), (DISPLAY_W - 30, HALF_H)], fill=(255, 255, 255), width=1)

    # ── Top half ─────────────────────────────────────────────
    _draw_half(
        draw,
        fonts,
        label=CLOCK_UPPER_ZONE["label"],
        time_str=upper_time_str or now_top.strftime("%H:%M:%S"),
        date_str=upper_date_str or now_top.strftime("%Y-%m-%d  %a"),
        weather=upper_weather,
        y_offset=0,
        time_color=(255, 255, 255),
    )

    # ── Bottom half ──────────────────────────────────────────
    _draw_half(
        draw,
        fonts,
        label=CLOCK_LOWER_ZONE["label"],
        time_str=lower_time_str or now_bottom.strftime("%H:%M:%S"),
        date_str=lower_date_str or now_bottom.strftime("%Y-%m-%d  %a"),
        weather=lower_weather,
        y_offset=HALF_H,
        time_color=(255, 255, 255),
    )

    return image


def render_clock_elements(
    prev_frame,
    bg_image,
    fonts,
    zone_config,
    time_str,
    date_str,
    weather,
    y_offset,
    parts,
):
    """Selectively update individual elements in one zone on prev_frame.

    parts: set containing any of 'time', 'date', 'weather'
    For each element in parts: restores the background strip, then redraws only that element.
    Returns updated frame (unchanged pixels remain identical to prev_frame).
    """
    W = DISPLAY_W
    label = zone_config["label"]
    layout = _calc_layout(fonts, label, time_str, date_str, weather, y_offset)

    temp_str = f"{weather['temp']}\u00b0C"
    humi_str = f"{weather['humidity']}%"
    icon_str = weather["icon"]

    image = prev_frame.copy()

    def erase_strip(y, h):
        """Restore background pixels in this element's horizontal band."""
        y0 = y
        y1 = min(DISPLAY_H, y + h + SHADOW_PAD)
        image.paste(bg_image.crop((0, y0, W, y1)), (0, y0))

    if "time" in parts:
        erase_strip(layout["time_y"], layout["time_h"])
        draw = ImageDraw.Draw(image)
        tw = text_w(time_str, fonts["time"])
        draw_text_with_shadow(
            draw,
            ((W - tw) // 2, layout["time_y"]),
            time_str,
            fonts["time"],
            (255, 255, 255),
            shadow_offset=(0, 1),
        )

    if "date" in parts:
        erase_strip(layout["date_y"], layout["date_h"])
        draw = ImageDraw.Draw(image)
        dw = text_w(date_str, fonts["date"])
        draw_text_with_shadow(
            draw,
            ((W - dw) // 2, layout["date_y"]),
            date_str,
            fonts["date"],
            (255, 255, 255),
            shadow_offset=(0, 1),
        )

    if "weather" in parts:
        temp_h = fonts["weather"].getbbox(temp_str)[3]
        humi_h = fonts["weather"].getbbox(humi_str)[3]
        icon_h = fonts["icon"].getbbox(icon_str)[3]
        row_h = max(temp_h, humi_h, icon_h)
        wy = layout["weather_y"]

        erase_strip(wy, row_h)
        draw = ImageDraw.Draw(image)

        def draw_at_vcenter(text, font, x, fill, elem_h):
            y = wy + (row_h - elem_h) // 2
            draw_text_with_shadow(draw, (x, y), text, font, fill)

        draw_at_vcenter(temp_str, fonts["weather"], PAD, (255, 255, 255), temp_h)
        hw = text_w(humi_str, fonts["weather"])
        draw_at_vcenter(
            humi_str, fonts["weather"], W - hw - PAD, (255, 255, 255), humi_h
        )
        iw = text_w(icon_str, fonts["icon"])
        wmo_code = weather.get("code", 0)
        icon_color = WMO_COLORS.get(wmo_code, (255, 255, 255))
        draw_at_vcenter(icon_str, fonts["icon"], (W - iw) // 2, icon_color, icon_h)

    return image


def _draw_half(draw, fonts, label, time_str, date_str, weather, y_offset, time_color):
    W = DISPLAY_W

    temp_str = f"{weather['temp']}\u00b0C"
    humi_str = f"{weather['humidity']}%"
    icon_str = weather["icon"]

    layout = _calc_layout(fonts, label, time_str, date_str, weather, y_offset)

    # City label (centered)
    lw = text_w(label, fonts["label"])
    draw_text_with_shadow(
        draw,
        pos=((W - lw) // 2, layout["top"]),
        text=label,
        font=fonts["label"],
        fill=(255, 255, 255),
        shadow_offset=(0, 1),
    )

    # Large time display (centered, Rajdhani)
    tw = text_w(time_str, fonts["time"])
    draw_text_with_shadow(
        draw,
        pos=((W - tw) // 2, layout["time_y"]),
        text=time_str,
        font=fonts["time"],
        fill=time_color,
        shadow_offset=(0, 1),
    )

    # Date (centered)
    dw = text_w(date_str, fonts["date"])
    draw_text_with_shadow(
        draw,
        pos=((W - dw) // 2, layout["date_y"]),
        text=date_str,
        font=fonts["date"],
        fill=(255, 255, 255),
        shadow_offset=(0, 1),
    )

    # ── Weather row (left: temp  center: icon  right: humidity) ──
    wy = layout["weather_y"]
    temp_h = fonts["weather"].getbbox(temp_str)[3]
    humi_h = fonts["weather"].getbbox(humi_str)[3]
    icon_h = fonts["icon"].getbbox(icon_str)[3]
    row_h = max(temp_h, humi_h, icon_h)

    def draw_at_vcenter(text, font, x, fill, elem_h):
        y = wy + (row_h - elem_h) // 2
        draw_text_with_shadow(draw, (x, y), text, font, fill)

    # Left: temperature
    draw_at_vcenter(temp_str, fonts["weather"], PAD, (255, 255, 255), temp_h)

    # Right: humidity
    hw = text_w(humi_str, fonts["weather"])
    draw_at_vcenter(humi_str, fonts["weather"], W - hw - PAD, (255, 255, 255), humi_h)

    # Center: icon
    iw = text_w(icon_str, fonts["icon"])
    wmo_code = weather.get("code", 0)
    icon_color = WMO_COLORS.get(wmo_code, (255, 255, 255))
    draw_at_vcenter(icon_str, fonts["icon"], (W - iw) // 2, icon_color, icon_h)
