"""STEP 7 - DASHBOARD.   Run:  streamlit run app/streamlit_app.py"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st
from sqlalchemy import text

# On Streamlit Community Cloud the DB URL comes from "Secrets"; locally from .env
try:
    if "DATABASE_URL" in st.secrets:
        os.environ["DATABASE_URL"] = st.secrets["DATABASE_URL"]
except Exception:
    pass

from src.load import get_engine  # noqa: E402

st.set_page_config(page_title="PuneAir", page_icon="🌫️", layout="wide")


@st.cache_resource
def engine():
    return get_engine()


@st.cache_data(ttl=600)
def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    return pd.read_sql(text(sql), engine(), params=params or {})


st.title("🌫️ PuneAir: air quality in Pune")
st.caption("Hourly PM2.5 and weather for 5 areas. Source: Open-Meteo (CAMS model data, not ground sensors). "
           "Pipeline: API -> Pandas cleaning -> PostgreSQL -> SQL views -> ML forecast -> this dashboard.")

try:
    latest = query("SELECT * FROM v_latest_reading ORDER BY area")
except Exception:
    st.error("No data found yet. Run `python run_pipeline.py` first, then refresh this page.")
    st.stop()

area = st.sidebar.selectbox("Area", sorted(latest["area"]))
days = st.sidebar.slider("Days to show in trend", 3, 60, 14)
st.sidebar.markdown("Data is refreshed whenever the pipeline runs (daily via GitHub Actions).")

# ---- KPI row ----
row = latest[latest["area"] == area].iloc[0]
try:
    pred = query("SELECT * FROM predictions")
    pred_row = pred[pred["area"] == area].iloc[0]
except Exception:
    pred_row = None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest PM2.5 (ug/m3)", f"{row['pm2_5']:.1f}")
c2.metric("Category (CPCB)", row["aqi_category"])
if pred_row is not None:
    c3.metric("Predicted PM2.5, next 24h", f"{pred_row['predicted_pm2_5']:.1f}",
              delta=f"{pred_row['predicted_pm2_5'] - row['pm2_5']:+.1f} vs now", delta_color="inverse")
    c4.metric("Predicted category", pred_row["predicted_category"])
st.caption(f"Latest reading: {pd.to_datetime(row['obs_time']):%d %b %Y, %H:%M}")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Trend", "🏙️ Compare areas", "🕒 Patterns", "🔮 Forecast"])

with tab1:
    series = query("SELECT obs_time, pm2_5 FROM air_quality WHERE area = :a ORDER BY obs_time", {"a": area})
    series["obs_time"] = pd.to_datetime(series["obs_time"])
    series = series[series["obs_time"] >= series["obs_time"].max() - pd.Timedelta(days=days)].set_index("obs_time")
    series["24h average"] = series["pm2_5"].rolling(24, min_periods=1).mean()
    st.line_chart(series.rename(columns={"pm2_5": "hourly PM2.5"}))

with tab2:
    ranking = query("SELECT area, avg_pm25, pollution_rank FROM v_area_ranking ORDER BY pollution_rank")
    st.subheader("Average PM2.5 by area (rank 1 = most polluted)")
    st.bar_chart(ranking.set_index("area")["avg_pm25"])
    st.dataframe(latest[["area", "pm2_5", "aqi_category", "temperature_2m", "wind_speed_10m"]], hide_index=True)

with tab3:
    left, right = st.columns(2)
    hourly = query("SELECT hour_of_day, avg_pm25 FROM v_hourly_pattern WHERE area = :a ORDER BY hour_of_day", {"a": area})
    left.subheader("Average PM2.5 by hour of day")
    left.line_chart(hourly.set_index("hour_of_day")["avg_pm25"])
    wind = query("SELECT wind_band, avg_pm25 FROM v_wind_effect WHERE area = :a ORDER BY wind_band", {"a": area})
    right.subheader("PM2.5 by wind speed")
    right.bar_chart(wind.set_index("wind_band")["avg_pm25"])
    st.caption("Calm air traps pollution, wind clears it.")

with tab4:
    if pred_row is None:
        st.info("Run the pipeline without --skip-train to create forecasts.")
    else:
        st.subheader("Predicted PM2.5, next 24 hours")
        st.dataframe(pred, hide_index=True)
        metrics_file = ROOT / "models" / "metrics.json"
        if metrics_file.exists():
            st.subheader("How good is the model?")
            st.json(metrics_file.read_text())
        st.caption("The model is compared with a simple baseline ('tomorrow = now') on the last 7 unseen days.")
