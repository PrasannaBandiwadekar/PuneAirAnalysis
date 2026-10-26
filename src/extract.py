"""STEP 1 - EXTRACT: download hourly air quality + weather data from Open-Meteo (free, no API key)."""
import logging
import time

import pandas as pd
import requests

from src.config import AIR_COLS, AREAS, RAW_DIR, WEATHER_COLS

log = logging.getLogger(__name__)

AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def _get_json(url: str, params: dict, retries: int = 3) -> dict:
    """GET with simple retry, so one slow response does not kill the whole run."""
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            log.warning("Request failed (attempt %s/%s): %s", attempt, retries, exc)
            if attempt == retries:
                raise
            time.sleep(2 * attempt)


def fetch_area(name: str, lat: float, lon: float, past_days: int) -> pd.DataFrame:
    """Fetch air quality and weather for one area and join them on the timestamp."""
    common = {
        "latitude": lat,
        "longitude": lon,
        "past_days": past_days,   # Open-Meteo allows up to 92
        "forecast_days": 1,
        "timezone": "Asia/Kolkata",
    }
    air = _get_json(AIR_URL, {**common, "hourly": ",".join(AIR_COLS)})
    weather = _get_json(WEATHER_URL, {**common, "hourly": ",".join(WEATHER_COLS)})
    df = pd.DataFrame(air["hourly"]).merge(pd.DataFrame(weather["hourly"]), on="time", how="outer")
    df["area"] = name
    return df


def extract(past_days: int = 60) -> pd.DataFrame:
    """Fetch all areas, save the untouched data as the RAW (bronze) layer, and return it."""
    frames = []
    for name, (lat, lon) in AREAS.items():
        try:
            frames.append(fetch_area(name, lat, lon, past_days))
            log.info("Fetched %s (%s rows)", name, len(frames[-1]))
        except Exception as exc:  # keep going with the other areas
            log.error("Could not fetch %s: %s", name, exc)
    if not frames:
        raise RuntimeError("No data could be downloaded. Check your internet connection.")
    df = pd.concat(frames, ignore_index=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_DIR / "raw_data.csv", index=False)
    log.info("Saved raw layer: %s rows -> data/raw/raw_data.csv", len(df))
    return df
