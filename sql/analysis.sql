-- Analysis views (the GOLD layer). The dashboard reads from these.
-- Written to run on both PostgreSQL and SQLite.

-- Drop first the view that depends on another view (PostgreSQL requires this order)
DROP VIEW IF EXISTS v_daily_change;

-- 1) Daily average and maximum PM2.5 per area
DROP VIEW IF EXISTS v_daily_avg_pm25;
CREATE VIEW v_daily_avg_pm25 AS
SELECT area,
       obs_date,
       AVG(pm2_5) AS avg_pm25,
       MAX(pm2_5) AS max_pm25
FROM air_quality
GROUP BY area, obs_date;

-- 2) Ranking of areas from most to least polluted (window function RANK)
DROP VIEW IF EXISTS v_area_ranking;
CREATE VIEW v_area_ranking AS
SELECT area,
       AVG(pm2_5) AS avg_pm25,
       RANK() OVER (ORDER BY AVG(pm2_5) DESC) AS pollution_rank
FROM air_quality
GROUP BY area;

-- 3) Average PM2.5 for each hour of the day (finds rush-hour peaks)
DROP VIEW IF EXISTS v_hourly_pattern;
CREATE VIEW v_hourly_pattern AS
SELECT area,
       hour_of_day,
       AVG(pm2_5) AS avg_pm25
FROM air_quality
GROUP BY area, hour_of_day;

-- 4) Weather effect: PM2.5 in calm, breezy and windy hours
DROP VIEW IF EXISTS v_wind_effect;
CREATE VIEW v_wind_effect AS
SELECT area,
       wind_band,
       AVG(pm2_5) AS avg_pm25,
       COUNT(*)   AS hours
FROM (
    SELECT area,
           pm2_5,
           CASE WHEN wind_speed_10m < 5  THEN '1 Calm (under 5 km/h)'
                WHEN wind_speed_10m < 12 THEN '2 Breezy (5 to 12 km/h)'
                ELSE                          '3 Windy (over 12 km/h)'
           END AS wind_band
    FROM air_quality
) AS banded
GROUP BY area, wind_band;

-- 5) Latest reading per area (window function ROW_NUMBER)
DROP VIEW IF EXISTS v_latest_reading;
CREATE VIEW v_latest_reading AS
SELECT area, obs_time, pm2_5, pm10, us_aqi, aqi_category,
       temperature_2m, relative_humidity_2m, wind_speed_10m
FROM (
    SELECT a.*,
           ROW_NUMBER() OVER (PARTITION BY area ORDER BY obs_time DESC) AS rn
    FROM air_quality a
) AS ranked
WHERE rn = 1;

-- 6) Day-over-day change in average PM2.5 (window function LAG)
CREATE VIEW v_daily_change AS
SELECT area,
       obs_date,
       avg_pm25,
       avg_pm25 - LAG(avg_pm25) OVER (PARTITION BY area ORDER BY obs_date) AS change_vs_prev_day
FROM v_daily_avg_pm25;
