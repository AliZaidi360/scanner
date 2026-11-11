SEARCH_TERMS = [
    "junior devops engineer",
    "System Administrator",
    "IT specialist",
    "Associate",
    "cloud engineer",
    "infrastructure engineer",
    "platform engineer",
    "junior site reliability engineer",
    "associate cloud engineer",
    "Data Analyst"
]

STATES = [
    "Virginia",
    "Illinois",
    "California",
    "New York",
    "Texas",
]

MAX_DAYS_OLD = 14
RESULTS_PER_PAGE = 50
MAX_PAGES_PER_QUERY = 1
REQUEST_DELAY_SECONDS = 1.0

SALARY_FLOOR = 70000
EXCLUDED_TITLE_KEYWORDS = [
    "Clearence","clearence","Senior""senior", "sr.", "sr ", "staff", "principal",
    "lead", "manager", "director", "architect", "vp"
]
MAX_YEARS_EXPERIENCE = 3
EXCLUDE_CLEARANCE = True

WEIGHTS = {
    "title_strong_match": 10,
    "entry_level_signal": 5,
    "fresh_48h": 5,
    "salary_clears_floor": 3,
    "target_employer": 8,
    "skills": {
        "linux": 2,
        "aws": 2,
        "bash": 2,
        "python": 2,
        "docker": 1,
        "github actions": 1,
        "terraform": 1,
        "ci/cd": 1,
        "kubernetes": 1,
    },
    "state_bonus": {
        "Virginia": 2,
        "New York": 2,
        "California": 1,
        "Texas": 1,
        "Illinois": 2,
    }
}

TARGET_EMPLOYERS = ["planet labs", "oneweb", "eutelsat", "maxar"]

ENTRY_LEVEL_KEYWORDS = [
    "junior", "entry level", "entry-level", "associate", "0-2 years", "1-2 years", "jr"
]
