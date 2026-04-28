# -*- coding: utf-8 -*-
import requests
from config import WMO_ICONS


def fetch_weather(lat, lon):
    """Fetch temperature, humidity, and weather code from Open-Meteo"""
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code"
            f"&temperature_unit=celsius"
        )
        r = requests.get(url, timeout=5)
        data = r.json()["current"]
        return {
            "temp": round(data["temperature_2m"]),
            "humidity": round(data["relative_humidity_2m"]),
            "icon": WMO_ICONS.get(data["weather_code"], "?"),
            "code": data["weather_code"],
        }
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return {"temp": "--", "humidity": "--", "icon": "?"}
