import re
import config

EXPERIENCE_REGEX = re.compile(r"\b([4-9]|\d{2,})\+?\s*(?:-\s*\d+\s*)?years?\b", re.IGNORECASE)
CLEARANCE_REGEX = re.compile(r"\b(ts/sci|top secret|secret clearance|polygraph|active clearance)\b", re.IGNORECASE)


def passes_hard_filters(job: dict) -> bool:
    title_lower = job["title"].lower()
    desc_lower = job["description"].lower()

    for word in config.EXCLUDED_TITLE_KEYWORDS:
        if word in title_lower:
            return False

    if job["state"] not in config.STATES and "remote" not in title_lower and "remote" not in desc_lower:
        return False

    sal_max = job.get("salary_max")
    sal_min = job.get("salary_min")
    effective_max = sal_max if sal_max is not None else sal_min

    if effective_max is None:
        job["salary_flag"] = "salary unknown"
    else:
        if effective_max < config.SALARY_FLOOR:
            return False
        job["salary_flag"] = "listed"

    if EXPERIENCE_REGEX.search(desc_lower):
        return False

    if config.EXCLUDE_CLEARANCE and CLEARANCE_REGEX.search(desc_lower):
        return False

    return True


def filter_jobs(jobs: list[dict]) -> list[dict]:
    return [job for job in jobs if passes_hard_filters(job)]