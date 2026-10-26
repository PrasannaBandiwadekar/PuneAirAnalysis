"""STEP 2 - TRANSFORM: clean the raw data and add useful columns (the CLEAN / silver layer)."""
import logging

import numpy as np
import pandas as pd

from src.config import AIR_COLS, CLEAN_DIR, FINAL_COLUMNS, NUM_COLS

log = logging.getLogger(__name__)
HOUR = pd.Timedelta(hours=1)


def categorize(pm25: pd.Series) -> pd.Series:
    """Label PM2.5 using India's CPCB bands (CPCB defines them for 24h averages,
    so on hourly data this is an approximation)."""
    conditions = [pm25 <= 30, pm25 <= 60, pm25 <= 90, pm25 <= 120, pm25 <= 250]
    labels = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor"]
    return pd.Series(np.select(conditions, labels, default="Severe"), index=pm25.index)


def _regularize(group: pd.DataFrame, area: str) -> pd.DataFrame:
    """Make the timeline strictly hourly: any missing hour becomes a row of NaN."""
    group = group.set_index("obs_time").asfreq(HOUR)
    group["area"] = area
    return group.reset_index()


def clean(raw: pd.DataFrame, now: pd.Timestamp | None = None) -> tuple[pd.DataFrame, dict]:
    """Return (clean_dataframe, report). The report counts every fix, which is great for the README."""
    report = {"rows_in": len(raw)}
    df = raw.copy().rename(columns={"time": "obs_time"})
    df["obs_time"] = pd.to_datetime(df["obs_time"], errors="coerce")
    df = df.dropna(subset=["obs_time", "area"])

    # 1) duplicates
    before = len(df)
    df = df.drop_duplicates(["area", "obs_time"], keep="last")
    report["duplicates_removed"] = before - len(df)

    # 2) rows from the future (the API also returns the rest of today as a forecast)
    now = now if now is not None else pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)
    before = len(df)
    df = df[df["obs_time"] <= now]
    report["future_rows_dropped"] = before - len(df)

    # 3) make sure all numeric columns exist and are numbers
    for col in NUM_COLS:
        if col not in df.columns:
            df[col] = np.nan
    df[NUM_COLS] = df[NUM_COLS].apply(pd.to_numeric, errors="coerce")

    # 4) impossible values -> NaN (they will be filled in step 6)
    invalid = 0
    for col in AIR_COLS + ["wind_speed_10m", "precipitation"]:
        bad = df[col] < 0
        invalid += int(bad.sum())
        df.loc[bad, col] = np.nan
    bad = (df["relative_humidity_2m"] < 0) | (df["relative_humidity_2m"] > 100)
    invalid += int(bad.sum())
    df.loc[bad, "relative_humidity_2m"] = np.nan
    bad = df["pm2_5"] > 1000
    invalid += int(bad.sum())
    df.loc[bad, "pm2_5"] = np.nan
    report["invalid_values_set_to_nan"] = invalid

    # 5) strictly hourly timeline per area
    df = pd.concat([_regularize(g, a) for a, g in df.groupby("area")], ignore_index=True)
    df = df.sort_values(["area", "obs_time"]).reset_index(drop=True)
    report["missing_values_before_fill"] = int(df[NUM_COLS].isna().sum().sum())

    # 6) fill small gaps (up to 6 hours) by straight-line interpolation inside each area
    df[NUM_COLS] = df.groupby("area")[NUM_COLS].transform(lambda s: s.interpolate(limit=6, limit_direction="both"))

    # 7) rows that still have no PM2.5 cannot be used
    before = len(df)
    df = df.dropna(subset=["pm2_5"])
    report["rows_dropped_no_pm25"] = before - len(df)

    # 8) new columns
    df["obs_date"] = df["obs_time"].dt.strftime("%Y-%m-%d")
    df["hour_of_day"] = df["obs_time"].dt.hour
    df["day_of_week"] = df["obs_time"].dt.dayofweek          # Monday = 0
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["aqi_category"] = categorize(df["pm2_5"])

    df = df[FINAL_COLUMNS].reset_index(drop=True)
    report["rows_out"] = len(df)
    for key, value in report.items():
        log.info("  %-28s %s", key, value)
    return df, report


def save_clean(df: pd.DataFrame) -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(CLEAN_DIR / "clean_data.parquet", index=False)
    log.info("Saved clean layer -> data/clean/clean_data.parquet")
