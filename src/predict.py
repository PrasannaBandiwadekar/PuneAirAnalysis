"""STEP 5 - PREDICT: use the saved model to forecast PM2.5 for the next 24 hours, per area."""
import logging

import joblib
import pandas as pd

from src.config import MODELS_DIR
from src.load import get_engine, read_air_quality
from src.train import HOUR, add_features
from src.transform import categorize

log = logging.getLogger(__name__)


def predict_latest(engine=None) -> pd.DataFrame:
    engine = engine or get_engine()
    bundle = joblib.load(MODELS_DIR / "pm25_model.joblib")
    model, features = bundle["model"], bundle["features"]

    data = add_features(read_air_quality(engine))
    latest = data.sort_values("obs_time").groupby("area").tail(1)      # newest row of each area
    X = latest.reindex(columns=features, fill_value=0)                 # missing area columns -> 0
    X = X.apply(lambda col: col.fillna(col.median())).fillna(0)

    out = pd.DataFrame({
        "area": latest["area"].to_numpy(),
        "based_on_time": latest["obs_time"].to_numpy(),
        "predicted_for": (latest["obs_time"] + 24 * HOUR).to_numpy(),
        "predicted_pm2_5": model.predict(X).round(1),
    })
    out["predicted_category"] = categorize(out["predicted_pm2_5"]).to_numpy()
    out.to_sql("predictions", engine, if_exists="replace", index=False)
    log.info("Saved %s predictions to table 'predictions'", len(out))
    return out
