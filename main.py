# -*- coding: utf-8 -*-
import sys
import os
import time
import logging
import glob
import random
from datetime import datetime
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    BG_FOLDER,
    BG_SWITCH_SEC,
    HALF_H,
    WEATHER_SEC,
    CLOCK_UPPER_ZONE,
    CLOCK_LOWER_ZONE,
    DISPLAY_W,
    DISPLAY_H,
)
from drivers.st7796 import ST7796
from modules.clock import load_fonts, render_clock, render_clock_elements
from modules.weather import fetch_weather


def get_bg_images(folder):
    paths = sorted(
        glob.glob(f"{folder}/*.jpg")
        + glob.glob(f"{folder}/*.png")
        + glob.glob(f"{folder}/*.jpeg")
    )
    if not paths:
        print(f"No images in {folder}, using black background")
        return [Image.new("RGB", (DISPLAY_W, DISPLAY_H), (0, 0, 0))]

    images = []
    for path in paths:
        img = Image.open(path).convert("RGB")
        if img.size != (DISPLAY_W, DISPLAY_H):
            canvas = Image.new("RGB", (DISPLAY_W, DISPLAY_H), (0, 0, 0))
            x = (DISPLAY_W - img.size[0]) // 2
            y = (DISPLAY_H - img.size[1]) // 2
            canvas.paste(img, (x, y))
            img = canvas
        images.append(img)
        print(f"Loaded: {path}")

    random.shuffle(images)
    return images


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

    # Initialize with full render
    prev_frame = render_clock(bg_images[bg_index], fonts, upper_weather, lower_weather)
    disp.show_image(prev_frame)

    # Track previous state for change detection
    now_top = datetime.now(CLOCK_UPPER_ZONE["tz"])
    now_bottom = datetime.now(CLOCK_LOWER_ZONE["tz"])
    prev_upper_time = now_top.strftime("%H:%M:%S")
    prev_lower_time = now_bottom.strftime("%H:%M:%S")
    prev_upper_date = now_top.strftime("%Y-%m-%d  %a")
    prev_lower_date = now_bottom.strftime("%Y-%m-%d  %a")
    prev_upper_weather = upper_weather
    prev_lower_weather = lower_weather
    prev_bg_index = bg_index

    print("Start, Ctrl+C to exit")
    try:
        while True:
            now = time.time()

            # Switch background
            bg_changed = False
            if now - last_bg_switch >= BG_SWITCH_SEC:
                bg_index = (bg_index + 1) % len(bg_images)
                last_bg_switch = now
                bg_changed = True

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

            # Get current time strings
            now_top = datetime.now(CLOCK_UPPER_ZONE["tz"])
            now_bottom = datetime.now(CLOCK_LOWER_ZONE["tz"])
            upper_time = now_top.strftime("%H:%M:%S")
            lower_time = now_bottom.strftime("%H:%M:%S")
            upper_date = now_top.strftime("%Y-%m-%d  %a")
            lower_date = now_bottom.strftime("%Y-%m-%d  %a")

            # Detect per-element changes for each zone
            upper_parts = set()
            lower_parts = set()
            if upper_time != prev_upper_time:
                upper_parts.add("time")
            if upper_date != prev_upper_date:
                upper_parts.add("date")
            if upper_weather != prev_upper_weather:
                upper_parts.add("weather")
            if lower_time != prev_lower_time:
                lower_parts.add("time")
            if lower_date != prev_lower_date:
                lower_parts.add("date")
            if lower_weather != prev_lower_weather:
                lower_parts.add("weather")

            # Only render and update if something changed
            current_frame = prev_frame

            if upper_parts:
                current_frame = render_clock_elements(
                    current_frame,
                    bg_images[prev_bg_index],
                    fonts,
                    CLOCK_UPPER_ZONE,
                    upper_time,
                    upper_date,
                    upper_weather,
                    0,
                    upper_parts,
                )
            if lower_parts:
                current_frame = render_clock_elements(
                    current_frame,
                    bg_images[prev_bg_index],
                    fonts,
                    CLOCK_LOWER_ZONE,
                    lower_time,
                    lower_date,
                    lower_weather,
                    HALF_H,
                    lower_parts,
                )
            if upper_parts or lower_parts:
                disp.show_image_partial(current_frame, prev_frame)
                prev_frame = current_frame

            if bg_changed:
                current_frame = render_clock(
                    bg_images[bg_index],
                    fonts,
                    upper_weather,
                    lower_weather,
                    upper_time_str=upper_time,
                    upper_date_str=upper_date,
                    lower_time_str=lower_time,
                    lower_date_str=lower_date,
                )
                disp.show_image(current_frame)
                prev_frame = current_frame

            prev_upper_time = upper_time
            prev_lower_time = lower_time
            prev_upper_date = upper_date
            prev_lower_date = lower_date
            prev_upper_weather = upper_weather
            prev_lower_weather = lower_weather
            prev_bg_index = bg_index

            # Update
            elapsed = time.time() - now
            sleep_time = max(0, 1.0 - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nBye")
        disp.clear()
