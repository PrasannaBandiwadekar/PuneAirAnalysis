-- Main table. PRIMARY KEY (area, obs_time) means one row per area per hour,
-- so loading the same hour twice can never create a duplicate.
CREATE TABLE IF NOT EXISTS air_quality (
    area                  TEXT      NOT NULL,
    obs_time              TIMESTAMP NOT NULL,
    pm2_5                 DOUBLE PRECISION,
    pm10                  DOUBLE PRECISION,
    nitrogen_dioxide      DOUBLE PRECISION,
    ozone                 DOUBLE PRECISION,
    us_aqi                DOUBLE PRECISION,
    temperature_2m        DOUBLE PRECISION,
    relative_humidity_2m  DOUBLE PRECISION,
    wind_speed_10m        DOUBLE PRECISION,
    precipitation         DOUBLE PRECISION,
    obs_date              TEXT,
    hour_of_day           INTEGER,
    day_of_week           INTEGER,
    is_weekend            INTEGER,
    aqi_category          TEXT,
    PRIMARY KEY (area, obs_time)
);
