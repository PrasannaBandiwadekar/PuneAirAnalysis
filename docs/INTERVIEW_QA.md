# Interview questions for PuneAir (practise out loud)

**1. Explain your project in 30 seconds.**
I built a pipeline that downloads hourly air quality and weather data for 5 areas of Pune, cleans it with Pandas, loads it into a cloud PostgreSQL database, analyses it with SQL views, trains a model to forecast PM2.5 for the next 24 hours, and shows everything in a Streamlit dashboard. It runs daily through GitHub Actions.

**2. What is ETL?**
Extract (get data from a source), Transform (clean and reshape), Load (store in a database). In my project: API → Pandas → PostgreSQL.

**3. What does idempotent mean, and how did you achieve it?**
Running the pipeline many times gives the same result with no duplicates. I used a primary key on (area, obs_time) and an upsert: `INSERT ... ON CONFLICT DO UPDATE`.

**4. Why a staging table?**
I load the batch into a temporary table first, then merge it into the main table in one SQL statement. It keeps the main table safe if something fails halfway.

**5. How did you handle missing and bad data?**
I made the timeline strictly hourly, marked impossible values as missing (negative pollution, humidity above 100), and interpolated gaps of up to 6 hours. Longer gaps were dropped, because inventing a long stretch of data would be misleading.

**6. What are raw, clean and gold layers?**
Raw is the untouched download (CSV). Clean is the validated data (Parquet and the main table). Gold is analysis-ready output (SQL views). Keeping raw lets me re-run cleaning without downloading again.

**7. Which SQL features did you use?**
Primary keys, upsert, `GROUP BY`, `CASE`, subqueries, views, and window functions: `RANK()`, `ROW_NUMBER()` and `LAG()`.

**8. Difference between RANK, ROW_NUMBER and LAG?**
RANK gives equal rows the same rank. ROW_NUMBER gives every row a unique number (I used it to pick the latest row per area). LAG reads the previous row's value (I used it for day-over-day change).

**9. Why did you split train and test by time instead of randomly?**
This is time series data. A random split would let the model see the future during training and give fake-good scores. I trained on older data and tested on the last 7 unseen days.

**10. How did you know the model is any good?**
I compared it with a baseline that says "tomorrow equals now" and reported both errors (MAE and RMSE). The model is only useful if it beats the baseline. My improvement was [X]%.

**11. What features did you create?**
PM2.5 from 24 hours ago, the 24-hour rolling average, hour of day, weekday, weekend flag, and the area as 0/1 columns.

**12. What are the limitations?**
Only 60 days of data, so no seasonal patterns. The data is from a model (CAMS), not ground sensors. CPCB categories are meant for 24-hour averages.

**13. How would you scale it to millions of rows?**
Use Spark for processing, Parquet files on an S3 data lake, and Airflow to schedule and monitor, with partitions by date. For real-time data, stream through Kafka.

**14. How would you monitor data quality?**
Add checks (row counts, null rates, value ranges) with a tool such as Great Expectations, fail the run or alert when a check breaks, and log every fix like my cleaning report does.

**15. Why PostgreSQL and not just CSV files?**
A database gives primary keys, fast queries, concurrent access, and a shared source of truth for the dashboard and the model.

**16. What would you improve with more time?**
Longer history, ground sensor data, Airflow, automated data quality checks, and model monitoring.
