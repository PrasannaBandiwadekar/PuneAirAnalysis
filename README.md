# 🌫️ PuneAir: Air Quality Data Pipeline (ETL + SQL + ML + Dashboard)

An end-to-end data engineering project. Every hour of **real air quality and weather data** for 5 areas of
Pune is downloaded, cleaned, stored in a cloud database, analysed with SQL, used to train a machine learning
model that forecasts PM2.5 for the next 24 hours, and shown in a live dashboard.

Built to match the V4C.ai **Associate Data Engineer** and **Associate Data Scientist** job descriptions.

---

## 1. The big picture

```
 Open-Meteo APIs (free, no key)
        |
        v
 [1 EXTRACT]   src/extract.py      download hourly data for 5 areas       -> data/raw/raw_data.csv   (RAW layer)
        |
        v
 [2 TRANSFORM] src/transform.py    clean + add columns (Pandas, NumPy)    -> data/clean/*.parquet    (CLEAN layer)
        |
        v
 [3 LOAD]      src/load.py         upsert into PostgreSQL (or SQLite)     -> table air_quality
        |
        v
 [SQL VIEWS]   sql/analysis.sql    rankings, hourly pattern, wind effect  -> 6 views                 (GOLD layer)
        |
        +--> [4 TRAIN]   src/train.py     scikit-learn model vs baseline   -> models/pm25_model.joblib
        |        |
        |        +--> [5 PREDICT] src/predict.py   next-24h forecast       -> table predictions
        |
        +--> [6 EDA]     notebooks/eda.py   4 charts + written insights    -> reports/
        |
        +--> [7 DASHBOARD] app/streamlit_app.py                            -> live web page

 Automation: GitHub Actions runs the pipeline every day.   Packaging: Docker + docker-compose.
```

**How the JD keywords are covered**

| JD keyword | Where |
|---|---|
| Data pipelines, ETL, processing systems | `run_pipeline.py` and the `src/` steps 1 to 5 |
| Collection, cleaning, preprocessing of data | `src/transform.py` |
| Real-world datasets | Live Open-Meteo data, about 7,000 rows after 60 days |
| Python, Pandas, NumPy | `src/transform.py`, `src/train.py` |
| SQL | `sql/schema.sql`, `sql/analysis.sql` (window functions, views, upserts, CASE, subqueries) |
| Cloud-based platforms | Neon (cloud PostgreSQL), Streamlit Cloud, GitHub Actions |
| Machine learning models and algorithms | `src/train.py` (Random Forest vs baseline) |
| Exploratory data analysis, patterns, insights | `notebooks/eda.py` produces `reports/insights.md` |
| Documenting findings and presenting | This README, the reports, the dashboard |

## 2. Honest notes (good to say in interviews)

* The data is **CAMS model data from Open-Meteo**, not readings from ground sensors. Say "satellite and model based air quality data".
* PM2.5 categories use India's **CPCB bands**, which are officially for 24-hour averages. Applied to hourly data they are an approximation.
* `--sample` mode creates **fake data** just to test the code offline. Never quote numbers from sample mode on your resume.
* The model is compared with a simple baseline ("tomorrow = right now"). Report the real result, even if the improvement is small.

## 3. Folder structure

```
puneair/
├── README.md                  <- you are here
├── requirements.txt           <- Python libraries
├── run_pipeline.py            <- ONE command that runs everything
├── .env.example               <- copy to .env and put your database link
├── src/
│   ├── config.py              <- settings: areas, columns, database URL
│   ├── extract.py             <- step 1: download data
│   ├── transform.py           <- step 2: clean data
│   ├── load.py                <- step 3: save to database
│   ├── train.py               <- step 4: train model
│   ├── predict.py             <- step 5: forecast
│   └── sample_data.py         <- fake data for offline testing
├── sql/
│   ├── schema.sql             <- table definition
│   └── analysis.sql           <- 6 analysis views
├── notebooks/eda.py           <- charts and insights
├── app/streamlit_app.py       <- dashboard
├── tests/test_transform.py    <- automatic tests
├── Dockerfile, docker-compose.yml
├── .github/workflows/daily.yml<- daily automation
└── docs/
    ├── INTERVIEW_QA.md        <- questions and answers to practise
    └── RESUME.md              <- resume bullets and where to get your real numbers
```

## 4. Your 2-day plan

**Day 1: run it and understand it (about 5 hours)**
- [ ] Set up Python and install libraries (section 5)
- [ ] Test everything with `python run_pipeline.py --sample` (about 10 seconds)
- [ ] Run with real data: `python run_pipeline.py`
- [ ] Open `data/raw/raw_data.csv` and `data/clean/clean_data.parquet` and compare them
- [ ] Read `src/transform.py` line by line. This is the file interviewers will ask about
- [ ] Create a free Neon database (section 6) and run the pipeline again so the data goes to the cloud
- [ ] Run `python run_pipeline.py` a **second time** and see `new_rows_added` go to about 0. That is an idempotent load

**Day 2: show it and package it (about 5 hours)**
- [ ] `python notebooks/eda.py`, then read `reports/insights.md` and look at the 4 charts
- [ ] `streamlit run app/streamlit_app.py` and take screenshots (save in a `docs/` folder)
- [ ] Push to GitHub, add the `DATABASE_URL` secret, run the workflow once (section 8)
- [ ] Deploy the dashboard on Streamlit Cloud (section 9)
- [ ] Copy your **real** numbers into the resume bullets (`docs/RESUME.md`)
- [ ] Practise `docs/INTERVIEW_QA.md` out loud

## 5. Setup (first time only)

You need **Python 3.10 or newer** (check with `python --version`).

```bash
# 1. open a terminal inside the puneair folder, then create a virtual environment
python -m venv .venv

# 2. activate it
#   Windows (PowerShell):   .venv\Scripts\Activate.ps1
#   Windows (CMD):          .venv\Scripts\activate.bat
#   Mac / Linux:            source .venv/bin/activate

# 3. install the libraries
pip install -r requirements.txt

# 4. check that the tests pass
python -m pytest -q
```

## 6. Running the project

### A) Quick test with fake data (no internet needed)
```bash
python run_pipeline.py --sample
```
This writes to `data/puneair_sample.db`, never to your real database.
To look at the sample data in the charts or dashboard, point them at that file first:

```bash
# Windows PowerShell
$env:DATABASE_URL="sqlite:///data/puneair_sample.db"
# Windows CMD
set DATABASE_URL=sqlite:///data/puneair_sample.db
# Mac / Linux
export DATABASE_URL=sqlite:///data/puneair_sample.db
```
(Close the terminal or unset the variable when you want to go back to real data.)

### B) Real data, saved in a local file (SQLite)
```bash
python run_pipeline.py
```
It downloads 60 days of history for 5 areas, cleans it, saves it to `data/puneair.db`, trains the model and prints a forecast.
Use `--past-days 30` for less history. The maximum is 92.

### C) Real data in a cloud database (Neon, recommended for the resume)
1. Go to **neon.tech**, sign up (free), and create a project.
2. Copy the **connection string** (it starts with `postgresql://`).
3. Copy `.env.example` to `.env` and paste it after `DATABASE_URL=`:
   `DATABASE_URL=postgresql://user:password@ep-xxxx.aws.neon.tech/neondb?sslmode=require`
4. Run `python run_pipeline.py` again. The data now lives in the cloud.

### D) Charts and insights
```bash
python notebooks/eda.py
```
Creates 4 images in `reports/figures/` and `reports/insights.md` (findings written from your real data).

### E) Dashboard
```bash
streamlit run app/streamlit_app.py
```
Opens in your browser at http://localhost:8501.

### F) Everything in Docker (optional)
```bash
docker compose up --build
```
Starts PostgreSQL, runs the pipeline, and serves the dashboard on http://localhost:8501.

## 7. How each step works (in simple words)

**Step 1, Extract (`extract.py`).** For each of the 5 areas we call two free APIs, one for air quality and one for weather, and join
them on the timestamp. If a call fails, it retries 3 times. The untouched result is saved as `data/raw/raw_data.csv`. Keeping the raw
copy means we can always re-run the cleaning without downloading again.

**Step 2, Transform (`transform.py`).** The cleaning steps, in order:
1. remove duplicate rows (same area and same hour)
2. drop rows from the future (the API also returns the rest of today as a forecast)
3. turn text into numbers
4. mark impossible values as missing (negative pollution, humidity above 100)
5. make the timeline strictly hourly, so a missing hour becomes an empty row
6. fill small gaps (up to 6 hours) by interpolation, which draws a straight line between the known points
7. drop rows that still have no PM2.5
8. add columns: date, hour, weekday, weekend flag, and an air quality category

The function also returns a **report** with a count for each fix. Quote these numbers in interviews.

**Step 3, Load (`load.py`).** Data is first copied into a temporary *staging* table, then moved with
`INSERT ... ON CONFLICT (area, obs_time) DO UPDATE`. This is called an **upsert**. Because `(area, obs_time)` is the primary key, running the
pipeline twice never creates duplicates. This property is called **idempotent**, and it is what makes a pipeline safe to schedule.

**SQL views (`sql/analysis.sql`).** Six saved queries used by the dashboard: daily average, area ranking (`RANK()`),
hourly pattern, wind effect, latest reading (`ROW_NUMBER()`), and day-over-day change (`LAG()`).

**Step 4, Train (`train.py`).** The goal is to predict PM2.5 **24 hours ahead**. Inputs are current pollution and weather, the hour and weekday,
PM2.5 from one day ago, the 24-hour average, and the area. We split **by time**: train on older data, test on the last 7 days. A random split
would leak the future into training. The model (Random Forest) is compared with a baseline that says "tomorrow = now". Results go to `models/metrics.json`.

**Step 5, Predict (`predict.py`).** Takes the newest row of each area and writes a forecast into the `predictions` table.

**Step 6, EDA (`notebooks/eda.py`).** Four charts (trend, hour-by-weekday heatmap, area comparison, correlations) plus automatic written findings.

**Step 7, Dashboard (`app/streamlit_app.py`).** Reads only from the database views. It shows the latest PM2.5, a 24-hour forecast, trends, area ranking and patterns.

## 8. Daily automation with GitHub Actions

1. Push the project to a new GitHub repository.
2. In the repo go to **Settings → Secrets and variables → Actions → New repository secret**.
   Name: `DATABASE_URL`, value: your Neon connection string.
3. Go to the **Actions** tab, choose **Daily PuneAir pipeline**, click **Run workflow**, and set `past_days` to `60` for the first run.
4. After that it runs every day at 07:00 IST and downloads the last 3 days, which the upsert merges safely.

Note: GitHub pauses scheduled workflows if the repository has no activity for 60 days. Press **Run workflow** to wake it up.

## 9. Deploy the dashboard (Streamlit Community Cloud, free)

1. Push the repo to GitHub (the dashboard works from the database, so no data files are needed).
2. Go to **share.streamlit.io**, click **New app**, pick your repo, branch `main`, main file `app/streamlit_app.py`.
3. Under **Advanced settings → Secrets** paste:
   ```toml
   DATABASE_URL = "postgresql://user:password@ep-xxxx.aws.neon.tech/neondb?sslmode=require"
   ```
4. Deploy, and put the live link on your resume and GitHub README.

The "How good is the model?" box needs `models/metrics.json`, which exists after training. It is only available locally or in Docker, so on Streamlit Cloud it is simply hidden.

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| `No data could be downloaded` | Check your internet. Try again in a minute. Or test with `--sample`. |
| `No data found. Run python run_pipeline.py first` | The database is empty. Run the pipeline. If you used `--sample`, set `DATABASE_URL` as in section 6A. |
| `ModuleNotFoundError` | Activate the virtual environment and run `pip install -r requirements.txt`. |
| `could not connect to server` / SSL error | Re-copy the Neon connection string. It must end with `?sslmode=require`. |
| `Not enough data to train` | Run with the default `--past-days 60`. |
| Dashboard shows old data | It caches for 10 minutes. Refresh later or press **R**. |

## 11. Limitations and next steps (say these in interviews)

* Only 60 days of history, so the model cannot learn seasons. A longer history would help.
* For larger volumes I would replace the daily GitHub Actions job with **Apache Airflow**, use **Spark** for processing, and an **S3 data lake** with Parquet.
* I would add data quality tooling such as Great Expectations, and monitoring for model drift.
* Data comes from a model, so adding real ground sensor data (for example CPCB stations) would improve it.
