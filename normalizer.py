from datetime import datetime, timezone


def normalize_adzuna_job(raw_job: dict) -> dict:
    areas = raw_job.get("location", {}).get("area", [])
    state = areas[1] if len(areas) > 1 else ""
    city = areas[-1] if len(areas) > 2 else (areas[1] if len(areas) > 1 else "Unknown")

    return {
        "source_id": str(raw_job.get("id", "")),
        "source": "adzuna",
        "title": raw_job.get("title", "").strip(),
        "company": raw_job.get("company", {}).get("display_name", "Unknown").strip(),
        "city": city,
        "state": state,
        "salary_min": raw_job.get("salary_min"),
        "salary_max": raw_job.get("salary_max"),
        "description": raw_job.get("description", "").strip(),
        "posted_date": raw_job.get("created", ""),
        "url": raw_job.get("redirect_url", ""),
        "first_seen": datetime.now(timezone.utc).isoformat(),
    }


def normalize_batch(raw_jobs: list[dict]) -> list[dict]:
    return [normalize_adzuna_job(job) for job in raw_jobs if job.get("id")]