# Resume bullets for PuneAir

Replace every `[X]` with **your real number**. Where to find each number:

| Number | Where to find it |
|---|---|
| Records processed | the `rows_in` line printed by `python run_pipeline.py` (or `rows_out` after cleaning) |
| Issues fixed | the `duplicates_removed`, `invalid_values_set_to_nan`, `missing_values_before_fill` lines |
| MAE and improvement % | `models/metrics.json` (`mae_model`, `improvement_over_baseline_pct`) |
| Key finding | `reports/insights.md` |

## Project entry

**PuneAir: Air Quality Data Pipeline** | Python, Pandas, NumPy, SQL, PostgreSQL, scikit-learn, Docker, GitHub Actions, Streamlit  
[GitHub link] | [Live dashboard link]

- Built an end-to-end **ETL pipeline** that ingests hourly air quality and weather data for 5 Pune areas from public APIs and processes [X]+ records with **Pandas and NumPy**.
- **Cleaned and validated** the data (removed [X] duplicates, fixed [X] invalid values, filled [X] gaps) and loaded it into **cloud PostgreSQL** using idempotent upserts.
- Performed **exploratory data analysis** and wrote **SQL** (window functions, views) to find patterns by hour, area and weather, for example [your key finding].
- Trained a **machine learning model** to forecast next-day PM2.5 with MAE [X], [X]% better than a baseline.
- Automated daily runs with **GitHub Actions**, containerized the stack with **Docker**, and deployed a live **Streamlit** dashboard with full documentation.

## Skills line to add

`ETL/ELT pipelines, data cleaning and preprocessing, exploratory data analysis (EDA), machine learning, Pandas, NumPy, scikit-learn, SQL, PostgreSQL, cloud databases, Docker, CI/CD`

Only list what you can explain. If an interviewer asks "where did you use X?", you should be able to point to a file in this project.
