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

    # Auto-purge any old jobs in jobs.db that violate current filters!
    with db.get_connection() as conn:
        existing_rows = [dict(r) for r in conn.execute("SELECT * FROM jobs").fetchall()]
        bad_ids = [(r["source_id"],) for r in existing_rows if not filters.passes_hard_filters(r)]
        if bad_ids:
            conn.executemany("DELETE FROM jobs WHERE source_id = ?", bad_ids)
            conn.commit()
            logging.info(f"   Purged {len(bad_ids)} outdated/unrelated jobs from jobs.db.")

    logging.info("2. Fetching raw job listings from Adzuna...")
    raw_jobs = fetcher.fetch_all_jobs()
    logging.info(f"   Fetched {len(raw_jobs)} unique raw jobs.")

    logging.info("3. Normalizing records...")
    normalized_jobs = normalizer.normalize_batch(raw_jobs)

    logging.info("4. Applying hard filters...")
    filtered_jobs = filters.filter_jobs(normalized_jobs)
    logging.info(f"   {len(filtered_jobs)} jobs passed hard filters.")

    logging.info("5. Scoring and ranking jobs...")
    scored_jobs = scoring.score_jobs(filtered_jobs)

    logging.info("6. Saving new jobs to SQLite...")
    inserted_count = db.save_jobs(scored_jobs)
    logging.info(f"Pipeline complete! Added {inserted_count} brand-new jobs to jobs.db.")


if __name__ == "__main__":
    run_pipeline()
