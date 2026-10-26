"""STEP 4 - MACHINE LEARNING: predict PM2.5 for the next 24 hours and compare with a simple baseline."""
import json
import logging

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.config import MODELS_DIR
from src.load import read_air_quality

log = logging.getLogger(__name__)

BASE_FEATURES = [
    "pm2_5", "pm10", "nitrogen_dioxide", "ozone",
    "temperature_2m", "relative_humidity_2m", "wind_speed_10m", "precipitation",
    "hour_of_day", "day_of_week", "is_weekend",
    "pm25_lag_24h", "pm25_roll_24h",
]
HOUR = pd.Timedelta(hours=1)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build model inputs. Because the clean data is strictly hourly, shift(24) means 'exactly 24 hours'."""
    df = df.sort_values(["area", "obs_time"]).reset_index(drop=True).copy()
    grouped = df.groupby("area")["pm2_5"]
    df["pm25_lag_24h"] = grouped.shift(24)                                   # PM2.5 one day ago
    df["pm25_roll_24h"] = grouped.transform(lambda s: s.rolling(24, min_periods=12).mean())
    df["target"] = grouped.shift(-24)                                        # PM2.5 one day ahead (what we predict)
    dummies = pd.get_dummies(df["area"], prefix="area", dtype=int)           # area -> 0/1 columns
    return pd.concat([df, dummies], axis=1)


def train(engine=None, test_days: int = 7) -> dict:
    data = add_features(read_air_quality(engine))
    features = BASE_FEATURES + [c for c in data.columns if c.startswith("area_")]
    labeled = data.dropna(subset=features + ["target"])

    # Time-based split: the model never sees the future while training.
    last_time = labeled["obs_time"].max()
    cutoff = last_time - pd.Timedelta(days=test_days)
    train_df = labeled[labeled["obs_time"] <= cutoff - 24 * HOUR]   # -24h so no training target overlaps the test period
    test_df = labeled[labeled["obs_time"] > cutoff]
    if len(train_df) < 200 or len(test_df) < 24:
        raise RuntimeError(
            f"Not enough data to train (train={len(train_df)}, test={len(test_df)}). "
            "Run the pipeline with --past-days 60 first."
        )

    model = RandomForestRegressor(n_estimators=200, min_samples_leaf=3, n_jobs=-1, random_state=42)
    model.fit(train_df[features], train_df["target"])

    pred = model.predict(test_df[features])
    baseline = test_df["pm2_5"]  # "persistence": tomorrow will be the same as right now
    y = test_df["target"]
    mae_model = mean_absolute_error(y, pred)
    mae_base = mean_absolute_error(y, baseline)
    metrics = {
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "test_period": f"{test_df['obs_time'].min():%Y-%m-%d} to {test_df['obs_time'].max():%Y-%m-%d}",
        "mae_model": round(float(mae_model), 2),
        "mae_baseline": round(float(mae_base), 2),
        "rmse_model": round(float(np.sqrt(mean_squared_error(y, pred))), 2),
        "rmse_baseline": round(float(np.sqrt(mean_squared_error(y, baseline))), 2),
        "improvement_over_baseline_pct": round(float((mae_base - mae_model) / mae_base * 100), 1),
        "top_features": dict(sorted(zip(features, map(lambda v: round(float(v), 3), model.feature_importances_)),
                                    key=lambda kv: -kv[1])[:6]),
    }

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "features": features}, MODELS_DIR / "pm25_model.joblib")
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))
    log.info("Model MAE %.2f vs baseline MAE %.2f (%.1f%% better)", mae_model, mae_base,
             metrics["improvement_over_baseline_pct"])
    return metrics
