"""Run the whole pipeline with one command:

    python run_pipeline.py                 # real data (needs internet)
    python run_pipeline.py --sample        # fake data, only to test that the code works
"""
import argparse
import logging
import os
import time

from src import config
from src.config import setup_logging

log = logging.getLogger("pipeline")


def main() -> None:
    parser = argparse.ArgumentParser(description="PuneAir ETL + ML pipeline")
    parser.add_argument("--past-days", type=int, default=60, help="days of history to download (max 92)")
    parser.add_argument("--sample", action="store_true", help="use synthetic data and a separate SQLite file")
    parser.add_argument("--skip-train", action="store_true", help="skip model training and prediction")
    args = parser.parse_args()

    setup_logging()
    if args.sample:
        # Keep fake data away from your real (cloud) database.
        os.environ["DATABASE_URL"] = f"sqlite:///{config.ROOT / 'data' / 'puneair_sample.db'}"
        log.warning("SAMPLE MODE: synthetic data, saved to data/puneair_sample.db. Do not quote these results anywhere.")

    # imported here so that the DATABASE_URL set above is used
    from src.extract import extract
    from src.load import get_engine, load
    from src.predict import predict_latest
    from src.sample_data import make_sample_data
    from src.train import train
    from src.transform import clean, save_clean

    t0 = time.time()
    log.info("STEP 1/5  Extract")
    raw = make_sample_data(days=args.past_days) if args.sample else extract(args.past_days)

    log.info("STEP 2/5  Transform (clean + feature columns)")
    clean_df, _ = clean(raw)
    save_clean(clean_df)

    log.info("STEP 3/5  Load into the database")
    engine = get_engine()
    load(clean_df, engine)

    if args.skip_train:
        log.info("Skipping training and prediction (--skip-train)")
    else:
        log.info("STEP 4/5  Train model")
        metrics = train(engine)
        log.info("STEP 5/5  Predict next 24 hours")
        predictions = predict_latest(engine)
        print("\nModel results:", metrics)
        print("\nNext-24h forecast:\n", predictions.to_string(index=False))

    log.info("Pipeline finished in %.1f seconds", time.time() - t0)


if __name__ == "__main__":
    main()
