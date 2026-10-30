import logging
import db
import fetcher
import normalizer
import filters
import scoring

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)


def run_pipeline():
    logging.info("1. Initializing SQLite database...")
    db.init_db()

    logging.info("2. Fetching raw job listings from Adzuna...")
    raw_jobs = fetcher.fetch_all_jobs()
    logging.info(f"   Fetched {len(raw_jobs)} unique raw jobs.")

    logging.info("3. Normalizing records...")
    normalized_jobs = normalizer.normalize_batch(raw_jobs)

    logging.info("4. Applying hard filters (salary floor, seniority, experience, state)...")
    filtered_jobs = filters.filter_jobs(normalized_jobs)
    logging.info(f"   {len(filtered_jobs)} jobs passed hard filters (dropped {len(normalized_jobs) - len(filtered_jobs)}).")

    logging.info("5. Scoring and ranking jobs...")
    scored_jobs = scoring.score_jobs(filtered_jobs)

    logging.info("6. Saving new jobs to SQLite (deduplicating on ID and Company+Title+Location)...")
    inserted_count = db.save_jobs(scored_jobs)
    logging.info(f"Pipeline complete! Added {inserted_count} brand-new jobs to jobs.db.")


if __name__ == "__main__":
    run_pipeline()