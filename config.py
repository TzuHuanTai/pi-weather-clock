# -*- coding: utf-8 -*-
import pytz

# ── Font Settings ────────────────────────────────────────────
FONT_TIME = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_DATE = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_LABEL = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_WEATHER = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
FONT_ICON = "/usr/share/fonts/truetype/noto/NotoSansSymbols2-Regular.ttf"

# ── Display Settings ─────────────────────────────────────────
DISPLAY_W = 320
DISPLAY_H = 480
HALF_H = DISPLAY_H // 2
BG_FOLDER = "/home/pi/photos/"
BG_SWITCH_SEC = 10
WEATHER_SEC = 300

# ── Clock Zones (top/bottom) ─────────────────────────────────
CLOCK_UPPER_ZONE = {
    "label": "Seattle",
    "tz": pytz.timezone("America/Los_Angeles"),
    "lat": 47.6745,
    "lon": -122.3184,
}

CLOCK_LOWER_ZONE = {
    "label": "Taiwan",
    "tz": pytz.timezone("Asia/Taipei"),
    "lat": 23.3354,
    "lon": 120.2439,
}

# WMO weather code to emoji mapping
WMO_ICONS = {
    0: "☀",  # Clear
    1: "🌤",  # Mostly clear
    2: "⛅",  # Partly cloudy
    3: "☁",  # Overcast
    45: "🌫",  # Fog
    48: "🌫",
    51: "🌦",  # Drizzle
    53: "🌦",
    55: "🌧",
    61: "🌧",  # Rain
    63: "🌧",
    65: "🌧",
    71: "🌨",  # Snow
    73: "🌨",
    75: "❄",
    80: "🌦",  # Showers
    81: "🌧",
    82: "⛈",
    95: "⛈",  # Thunderstorm
    96: "⛈",
    99: "⛈",
}

LABEL_COLOR = (255, 255, 255)
TIME_COLOR = (255, 255, 255)
DATE_COLOR = (255, 255, 255)
TEMP_COLOR = (255, 255, 255)
HUMI_COLOR = (255, 255, 255)
ICON_COLOR = (255, 255, 255)
WMO_COLORS = {
    0: (255, 220, 80),  # Clear → yellow
    1: (255, 220, 80),
    2: (180, 200, 220),  # Cloudy → gray-blue
    3: (255, 255, 255),  # Overcast → gray
    45: (160, 160, 160),  # Fog → gray
    48: (160, 160, 160),
    51: (100, 180, 255),  # Drizzle → light blue
    53: (100, 180, 255),
    55: (60, 140, 255),  # Rain → blue
    61: (60, 140, 255),
    63: (60, 140, 255),
    65: (40, 100, 220),
    71: (200, 230, 255),  # Snow → ice white
    73: (200, 230, 255),
    75: (220, 240, 255),
    80: (80, 160, 255),  # Showers
    81: (60, 140, 220),
    82: (40, 100, 200),
    95: (180, 100, 255),  # Thunderstorm → purple
    96: (180, 100, 255),
    99: (150, 80, 220),
}
