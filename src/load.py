"""STEP 3 - LOAD: write the clean data into the database (PostgreSQL in the cloud, or local SQLite)."""
import logging

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import FINAL_COLUMNS, SQL_DIR, get_database_url

log = logging.getLogger(__name__)


def get_engine() -> Engine:
    return create_engine(get_database_url(), pool_pre_ping=True)


def run_sql_file(engine: Engine, filename: str) -> None:
    """Run every statement of a .sql file (statements are separated by semicolons)."""
    lines = (SQL_DIR / filename).read_text().splitlines()
    sql = "\n".join(line for line in lines if not line.strip().startswith("--"))
    with engine.begin() as conn:
        for statement in sql.split(";"):
            if statement.strip():
                conn.execute(text(statement))


def load(df: pd.DataFrame, engine: Engine | None = None) -> dict:
    """Idempotent load: re-running with the same data never creates duplicates.

    1. copy the data into a temporary staging table
    2. INSERT ... ON CONFLICT (area, obs_time) DO UPDATE  (an "upsert")
    3. drop the staging table
    """
    engine = engine or get_engine()
    run_sql_file(engine, "schema.sql")

    df[FINAL_COLUMNS].to_sql("staging_air_quality", engine, if_exists="replace", index=False)

    cols = ", ".join(FINAL_COLUMNS)
    updates = ", ".join(f"{c} = excluded.{c}" for c in FINAL_COLUMNS if c not in ("area", "obs_time"))
    upsert = (
        f"INSERT INTO air_quality ({cols}) "
        f"SELECT {cols} FROM staging_air_quality WHERE 1 = 1 "
        f"ON CONFLICT (area, obs_time) DO UPDATE SET {updates}"
    )
    with engine.begin() as conn:
        before = conn.execute(text("SELECT COUNT(*) FROM air_quality")).scalar()
        conn.execute(text(upsert))
        after = conn.execute(text("SELECT COUNT(*) FROM air_quality")).scalar()
        conn.execute(text("DROP TABLE staging_air_quality"))

    run_sql_file(engine, "analysis.sql")  # (re)create the analysis views
    result = {"rows_in_batch": len(df), "new_rows_added": int(after - before), "total_rows_in_table": int(after)}
    log.info("Load finished: %s", result)
    return result


def read_air_quality(engine: Engine | None = None) -> pd.DataFrame:
    engine = engine or get_engine()
    return pd.read_sql("SELECT * FROM air_quality ORDER BY area, obs_time", engine, parse_dates=["obs_time"])
