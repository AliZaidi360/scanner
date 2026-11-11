import os
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import db
import config
import main

st.set_page_config(page_title="Job Scanner", layout="wide")
db.init_db()

st.title("🚀Job Scanner")

# 1. Sidebar Filters & Admin Controls (Rendered first so you can always fetch!)
st.sidebar.header("Filter Jobs")
selected_states = st.sidebar.multiselect("State", options=config.STATES, default=config.STATES)
min_sal_filter = st.sidebar.number_input("Minimum Listed Salary ($)", value=config.SALARY_FLOOR, step=5000)
include_unknown_sal = st.sidebar.checkbox("Include 'Salary Unknown'", value=True)
max_age_days = st.sidebar.slider("Posted Within (Days)", 1, 30, 14)
status_options = ["new", "interested", "applied", "interview", "rejected", "ignored"]
selected_statuses = st.sidebar.multiselect(
    "Status", options=status_options, default=["new", "interested", "applied", "interview"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔒 Admin Controls")
admin_pass = st.sidebar.text_input("Admin Password (to edit/fetch)", type="password")
expected_pass = os.getenv("ADMIN_PASSWORD", "devops2026")
is_admin = (admin_pass == expected_pass)

if is_admin:
    st.sidebar.success("Admin unlocked")
    if st.sidebar.button("🔄 Fetch Fresh Jobs Now"):
        with st.spinner("Fetching and scoring jobs from Adzuna..."):
            main.run_pipeline()
        st.rerun()

# 2. Track Last Visit Timestamp
last_visit_str = db.get_meta("last_visit")
if "visit_logged" not in st.session_state:
    st.session_state["last_visit_snapshot"] = last_visit_str
    db.set_meta("last_visit", datetime.now(timezone.utc).isoformat())
    st.session_state["visit_logged"] = True

snapshot_visit = st.session_state.get("last_visit_snapshot")

# 3. Load Jobs from SQLite
with db.get_connection() as conn:
    df = pd.read_sql_query("SELECT * FROM jobs ORDER BY score DESC, posted_date DESC", conn)

if df.empty:
    st.info("No jobs in database yet. Unlock Admin Controls in the sidebar and click 'Fetch Fresh Jobs Now', or run `python main.py`!")
    st.stop()

# 4. Top Metrics
now_utc = datetime.now(timezone.utc)
today_cutoff = (now_utc - timedelta(hours=24)).isoformat()
df["is_new_today"] = df["first_seen"] >= today_cutoff
df["new_since_visit"] = df["first_seen"] > snapshot_visit if snapshot_visit else True

col1, col2, col3, col4 = st.columns(4)
col1.metric("Fetched Last 24h", int(df["is_new_today"].sum()))
col2.metric("New Since Last Visit", int(df["new_since_visit"].sum()))
col3.metric("Total Applied", int((df["status"] == "applied").sum()))
col4.metric("Interviews", int((df["status"] == "interview").sum()))

# 5. Apply Sidebar Filters to DataFrame
filtered_df = df[df["state"].isin(selected_states) & df["status"].isin(selected_statuses)].copy()

if not include_unknown_sal:
    filtered_df = filtered_df[filtered_df["salary_flag"] != "salary unknown"]
else:
    filtered_df = filtered_df[
        (filtered_df["salary_flag"] == "salary unknown") |
        (filtered_df["salary_max"].fillna(filtered_df["salary_min"]).fillna(0) >= min_sal_filter)
    ]

cutoff_date = (now_utc - timedelta(days=max_age_days)).isoformat()
filtered_df = filtered_df[filtered_df["posted_date"] >= cutoff_date]


def format_salary(row):
    if row["salary_flag"] == "salary unknown":
        return "Unknown"
    s_min = f"${int(row['salary_min']):,}" if pd.notna(row["salary_min"]) else ""
    s_max = f"${int(row['salary_max']):,}" if pd.notna(row["salary_max"]) else ""
    return f"{s_min} - {s_max}".strip(" -")


filtered_df["Location"] = filtered_df["city"] + ", " + filtered_df["state"]
filtered_df["Salary"] = filtered_df.apply(format_salary, axis=1)
filtered_df["Fresh"] = filtered_df["new_since_visit"].apply(lambda x: "🟢 NEW" if x else "")
filtered_df["Posted"] = filtered_df["posted_date"].str.slice(0, 10)

display_cols = ["source_id", "Fresh", "score", "status", "title", "company", "Location", "Salary", "Posted", "url", "notes"]
editor_df = filtered_df[display_cols].copy()

# 6. Render Interactive Table
st.subheader(f"Showing {len(editor_df)} Ranked Jobs")

edited_df = st.data_editor(
    editor_df,
    hide_index=True,
    use_container_width=True,
    disabled=["source_id", "Fresh", "score", "title", "company", "Location", "Salary", "Posted", "url"],
    column_config={
        "source_id": None,
        "Fresh": st.column_config.TextColumn("New?", width="small"),
        "score": st.column_config.NumberColumn("Score", format="%d", width="small"),
        "status": st.column_config.SelectboxColumn("Status", options=status_options, required=True, width="medium"),
        "title": st.column_config.TextColumn("Role Title", width="large"),
        "company": st.column_config.TextColumn("Company", width="medium"),
        "url": st.column_config.LinkColumn("Apply", display_text="Open Posting ↗", width="small"),
        "notes": st.column_config.TextColumn("Notes", width="large"),
    }
)

# 7. Save Button (Protected by Admin Password)
if is_admin:
    if st.button("💾 Save Status & Notes Changes", type="primary"):
        changes = 0
        for idx, row in edited_df.iterrows():
            orig = editor_df.loc[idx]
            if row["status"] != orig["status"] or row["notes"] != orig["notes"]:
                db.update_job_status_and_notes(row["source_id"], row["status"], row["notes"])
                changes += 1
        if changes:
            st.success(f"Saved updates for {changes} job(s)!")
            st.rerun()
        else:
            st.info("No changes detected.")
else:
    st.caption("🔒 Enter your Admin Password in the sidebar to save status/notes changes or trigger a live fetch.")
