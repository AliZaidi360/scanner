import os
import sys
import json
import time
import logging
import requests
from dotenv import load_dotenv
import config

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
BASE_URL = "https://api.adzuna.com/v1/api/jobs/us/search"


def fetch_page(term: str, state: str, page: int = 1, retries: int = 3) -> list[dict]:
    url = f"{BASE_URL}/{page}"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "what": term,
        "where": state,
        "max_days_old": config.MAX_DAYS_OLD,
        "results_per_page": config.RESULTS_PER_PAGE,
        "sort_by": "date",
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            elif response.status_code == 429:
                logging.warning(f"Rate limit (429). Waiting 10s (Attempt {attempt}/{retries})...")
                time.sleep(10)
            else:
                logging.error(f"HTTP {response.status_code} for '{term}' in '{state}': {response.text}")
                return []
        except requests.RequestException as err:
            logging.warning(f"Timeout/Error on '{term}' in '{state}' (Attempt {attempt}/{retries}): {err}")
            time.sleep(3 * attempt)

    return []


def fetch_all_jobs() -> list[dict]:
    if not APP_ID or not APP_KEY:
        raise ValueError("Missing ADZUNA_APP_ID or ADZUNA_APP_KEY in .env")

    all_raw_jobs = []
    seen_ids = set()

    for state in config.STATES:
        for term in config.SEARCH_TERMS:
            logging.info(f"Querying Adzuna: '{term}' in {state}")
            for page in range(1, config.MAX_PAGES_PER_QUERY + 1):
                results = fetch_page(term, state, page)
                if not results:
                    break

                for job in results:
                    job_id = str(job.get("id"))
                    if job_id not in seen_ids:
                        seen_ids.add(job_id)
                        all_raw_jobs.append(job)

                if len(results) < config.RESULTS_PER_PAGE:
                    break

                time.sleep(config.REQUEST_DELAY_SECONDS)

            time.sleep(config.REQUEST_DELAY_SECONDS)

    logging.info(f"Finished fetching. Total unique raw jobs collected: {len(all_raw_jobs)}")
    return all_raw_jobs


if __name__ == "__main__":
    if not APP_ID or not APP_KEY:
        print("ERROR: Please set ADZUNA_APP_ID and ADZUNA_APP_KEY in your .env file.")
        sys.exit(1)

    if "--test" in sys.argv:
        logging.info("Running in TEST MODE (fetching 1 query and printing first raw job)...")
        sample_results = fetch_page(config.SEARCH_TERMS[0], config.STATES[0], page=1)
        if sample_results:
            print("\n=== FIRST RAW ADZUNA RESULT ===")
            print(json.dumps(sample_results[0], indent=2))
        else:
            print("No results returned. Check your API keys or query parameters.")
    else:
        jobs = fetch_all_jobs()
        print(f"Fetched {len(jobs)} unique jobs across all states and terms.")