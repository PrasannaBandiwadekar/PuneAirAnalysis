"""Central settings: paths, areas, column lists, database URL, logging."""
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
MODELS_DIR = ROOT / "models"
SQL_DIR = ROOT / "sql"
REPORTS_DIR = ROOT / "reports"

# Five areas of Pune / Pimpri-Chinchwad: name -> (latitude, longitude)
AREAS = {
    "Pimpri-Chinchwad": (18.63, 73.80),
    "Hinjewadi": (18.59, 73.74),
    "Kothrud": (18.51, 73.81),
    "Hadapsar": (18.51, 73.93),
    "Shivajinagar": (18.53, 73.85),
}

AIR_COLS = ["pm2_5", "pm10", "nitrogen_dioxide", "ozone", "us_aqi"]
WEATHER_COLS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation"]
NUM_COLS = AIR_COLS + WEATHER_COLS

# Columns of the final table "air_quality" (same order as sql/schema.sql)
FINAL_COLUMNS = (
    ["area", "obs_time"]
    + NUM_COLS
    + ["obs_date", "hour_of_day", "day_of_week", "is_weekend", "aqi_category"]
)


def get_database_url() -> str:
    """Return the DB URL. Falls back to a local SQLite file if DATABASE_URL is empty."""
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        return f"sqlite:///{ROOT / 'data' / 'puneair.db'}"
    # Providers give "postgres://" or "postgresql://". We use the psycopg2 driver (see requirements.txt),
    # and name it explicitly because newer SQLAlchemy versions would otherwise pick a different driver.
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            url = "postgresql+psycopg2://" + url[len(prefix):]
    return url


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
