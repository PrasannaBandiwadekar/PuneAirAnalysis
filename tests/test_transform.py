import pandas as pd

from src.sample_data import make_sample_data
from src.transform import categorize, clean


def _clean_sample():
    return clean(make_sample_data(days=10, seed=1))


def test_no_duplicates_and_no_future_rows():
    df, report = _clean_sample()
    assert not df.duplicated(["area", "obs_time"]).any()
    assert df["obs_time"].max() <= pd.Timestamp.now(tz="Asia/Kolkata").tz_localize(None)
    assert report["duplicates_removed"] > 0
    assert report["future_rows_dropped"] > 0


def test_invalid_values_are_fixed():
    df, _ = _clean_sample()
    assert (df["pm10"].dropna() >= 0).all()
    assert df["relative_humidity_2m"].dropna().between(0, 100).all()
    assert df["pm2_5"].notna().all()


def test_timeline_is_strictly_hourly():
    df, _ = _clean_sample()
    for _, group in df.groupby("area"):
        assert (group["obs_time"].diff().dropna() == pd.Timedelta(hours=1)).all()


def test_categories():
    result = categorize(pd.Series([10, 45, 75, 100, 200, 400]))
    assert list(result) == ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]
