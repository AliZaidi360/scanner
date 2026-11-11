import sqlite3
from typing import Optional

DB_PATH = "jobs.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                source_id TEXT PRIMARY KEY,
                source TEXT,
                title TEXT,
                company TEXT,
                city TEXT,
                state TEXT,
                salary_min REAL,
                salary_max REAL,
                salary_flag TEXT,
                description TEXT,
                posted_date TEXT,
                url TEXT,
                first_seen TEXT,
                score INTEGER DEFAULT 0,
                status TEXT DEFAULT 'new',
                notes TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()


def is_duplicate(conn: sqlite3.Connection, job: dict) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM jobs WHERE source_id = ?", (job["source_id"],))
    if cur.fetchone():
        return True

    cur.execute("""
        SELECT 1 FROM jobs
        WHERE LOWER(company) = LOWER(?)
          AND LOWER(title) = LOWER(?)
          AND LOWER(city) = LOWER(?)
          AND LOWER(state) = LOWER(?)
    """, (job["company"], job["title"], job["city"], job["state"]))
    return cur.fetchone() is not None


def save_jobs(jobs: list[dict]) -> int:
    inserted = 0
    with get_connection() as conn:
        for job in jobs:
            if not is_duplicate(conn, job):
                conn.execute("""
                    INSERT INTO jobs (
                        source_id, source, title, company, city, state,
                        salary_min, salary_max, salary_flag, description,
                        posted_date, url, first_seen, score, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    job["source_id"], job["source"], job["title"], job["company"],
                    job["city"], job["state"], job["salary_min"], job["salary_max"],
                    job.get("salary_flag", "listed"), job["description"],
                    job["posted_date"], job["url"], job["first_seen"],
                    job.get("score", 0), job.get("status", "new"), job.get("notes", "")
                ))
                inserted += 1
        conn.commit()
    return inserted


def update_job_status_and_notes(source_id: str, status: str, notes: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET status = ?, notes = ? WHERE source_id = ?",
            (status, notes, source_id)
        )
        conn.commit()


def get_meta(key: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else None


def set_meta(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value)
        )
        conn.commit()
