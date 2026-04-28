# -*- coding: utf-8 -*-
import sys
import os
import time
import logging

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    BG_FOLDER,
    BG_SWITCH_SEC,
    WEATHER_SEC,
    CLOCK_UPPER_ZONE,
    CLOCK_LOWER_ZONE,
)
from drivers.st7796 import ST7796
from modules.clock import load_fonts, render_clock
from modules.weather import fetch_weather
from modules.display import get_bg_images

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    disp = ST7796()
    fonts = load_fonts()

    print("Loading images...")
    bg_images = get_bg_images(BG_FOLDER)
    bg_index = 0

    print("Fetching weather...")
    upper_weather = fetch_weather(CLOCK_UPPER_ZONE["lat"], CLOCK_UPPER_ZONE["lon"])
    lower_weather = fetch_weather(CLOCK_LOWER_ZONE["lat"], CLOCK_LOWER_ZONE["lon"])
    print(f"{CLOCK_UPPER_ZONE['label']}: {upper_weather}")
    print(f"{CLOCK_LOWER_ZONE['label']}: {lower_weather}")

    last_bg_switch = time.time()
    last_weather = time.time()

    print("Start, Ctrl+C to exit")
    try:
        while True:
            now = time.time()

            # Switch background
            if now - last_bg_switch >= BG_SWITCH_SEC:
                bg_index = (bg_index + 1) % len(bg_images)
                last_bg_switch = now

            # Update weather
            if now - last_weather >= WEATHER_SEC:
                upper_weather = fetch_weather(
                    CLOCK_UPPER_ZONE["lat"], CLOCK_UPPER_ZONE["lon"]
                )
                lower_weather = fetch_weather(
                    CLOCK_LOWER_ZONE["lat"], CLOCK_LOWER_ZONE["lon"]
                )
                last_weather = now
                print(f"Weather updated: upper={upper_weather}, lower={lower_weather}")

            # Render clock frame and display
            frame = render_clock(bg_images[bg_index], fonts, upper_weather, lower_weather)
            disp.show_image(frame)

            # Update
            elapsed = time.time() - now
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nBye")
        disp.clear()
