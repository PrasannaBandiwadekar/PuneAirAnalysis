"""Synthetic (fake) data in the same shape as the API output.

ONLY for testing the code without internet. Never present these numbers as real results.
"""
import numpy as np
import pandas as pd

from src.config import AREAS

HOUR = pd.Timedelta(hours=1)


def make_sample_data(days: int = 60, seed: int = 42, end: pd.Timestamp | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    end = (end if end is not None else pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)).floor("h")
    idx = pd.date_range(end=end, periods=days * 24, freq=HOUR)
    n = len(idx)
    hour = idx.hour.to_numpy()
    dow = idx.dayofweek.to_numpy()

    frames = []
    for i, area in enumerate(AREAS):
        # slow-moving "pollution level" (AR(1) noise) so the data has memory like real data
        level = np.zeros(n)
        for t in range(1, n):
            level[t] = 0.985 * level[t - 1] + rng.normal(0, 3)
        wind = rng.gamma(2.0, 3.0, n)
        rain = (rng.random(n) < 0.05) * rng.exponential(1.5, n)
        daily = 12 * np.exp(-((hour - 8.5) ** 2) / 8) + 16 * np.exp(-((hour - 21) ** 2) / 10)
        pm25 = 45 + i * 6 + level + daily - 1.2 * wind - 4 * rain
        pm25 = pm25 * np.where(dow >= 5, 0.9, 1.0) + rng.normal(0, 2, n)
        pm25 = np.clip(pm25, 3, None)
        df = pd.DataFrame({
            "time": idx.strftime("%Y-%m-%dT%H:%M"),
            "pm2_5": pm25,
            "pm10": pm25 * 1.6 + rng.normal(0, 4, n),
            "nitrogen_dioxide": 0.35 * pm25 + rng.normal(0, 2, n),
            "ozone": 70 - 0.2 * pm25 + 15 * np.sin((hour - 9) * 2 * np.pi / 24) + rng.normal(0, 3, n),
            "us_aqi": pm25 * 2.0,
            "temperature_2m": 26 + 6 * np.sin((hour - 9) * 2 * np.pi / 24) + rng.normal(0, 0.5, n),
            "relative_humidity_2m": np.clip(60 - 20 * np.sin((hour - 9) * 2 * np.pi / 24) + rng.normal(0, 3, n), 5, 100),
            "wind_speed_10m": wind,
            "precipitation": rain,
            "area": area,
        })
        # --- add typical real-world mess so the cleaning step has work to do ---
        df.loc[rng.choice(n, size=int(n * 0.01), replace=False), "pm2_5"] = np.nan   # random holes
        g = int(n * 0.35)
        df.loc[g:g + 2, ["pm2_5", "pm10"]] = np.nan                                  # a 3-hour gap
        df.loc[[int(n * 0.07), int(n * 0.5), int(n * 0.62)], "pm10"] = -5.0                                       # impossible values
        df.loc[int(n * 0.2), "relative_humidity_2m"] = 120.0                                   # impossible humidity
        future = df.tail(12).copy()                                                    # API also returns future hours
        future["time"] = (idx[-12:] + 12 * HOUR).strftime("%Y-%m-%dT%H:%M")
        df = pd.concat([df, df.sample(5, random_state=seed), future], ignore_index=True)  # duplicates + future
        frames.append(df)
    return pd.concat(frames, ignore_index=True)
