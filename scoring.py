from datetime import datetime, timezone
import config


def score_job(job: dict) -> int:
    score = 0
    w = config.WEIGHTS
    title_lower = job["title"].lower()
    desc_lower = job["description"].lower()
    company_lower = job["company"].lower()
    combined_text = f"{title_lower} {desc_lower}"

    if any(term in title_lower for term in ["devops", "cloud", "platform", "sre", "site reliability", "infrastructure"]):
        score += w["title_strong_match"]

    if any(sig in combined_text for sig in config.ENTRY_LEVEL_KEYWORDS):
        score += w["entry_level_signal"]

    for skill, pts in w["skills"].items():
        if skill in combined_text:
            score += pts

    sal_min = job.get("salary_min")
    if sal_min and sal_min >= config.SALARY_FLOOR:
        score += w["salary_clears_floor"]

    posted_str = job.get("posted_date")
    if posted_str:
        try:
            posted_dt = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
            hours_old = (datetime.now(timezone.utc) - posted_dt).total_seconds() / 3600
            if hours_old <= 48:
                score += w["fresh_48h"]
        except ValueError:
            pass

    score += w["state_bonus"].get(job.get("state", ""), 0)

    if any(emp in company_lower for emp in config.TARGET_EMPLOYERS):
        score += w["target_employer"]

    job["score"] = score
    return score


def score_jobs(jobs: list[dict]) -> list[dict]:
    for job in jobs:
        score_job(job)
    return sorted(jobs, key=lambda x: x["score"], reverse=True)