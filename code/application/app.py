"""StudyFlow - AI timetable and study plan generator (Streamlit UI).

Run locally:  streamlit run code/application/app.py
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

import llm
import pipeline
from validation import DIFFICULTY_WEIGHTS, SLOT_START

st.set_page_config(page_title="StudyFlow", page_icon="📅", layout="wide")

PROMPT_LABELS = {
    "P1": "Final (P1 = v3, structured JSON)",
    "v2": "v2 - constraint-aware (markdown)",
    "v1": "v1 - baseline (markdown)",
}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Settings")
    api_key = llm.get_api_key(st.secrets)
    if not api_key:
        api_key = st.text_input("Gemini API key", type="password",
                                help="Not stored. Get a free key at aistudio.google.com/apikey")
    model = st.text_input("Model", value=llm.DEFAULT_MODEL)
    prompt_key = st.selectbox("Prompt version", list(PROMPT_LABELS), format_func=PROMPT_LABELS.get,
                              help="Use v1/v2 to compare older prompt versions with the final prompt.")
    show_prompt = st.checkbox("Show the prompt sent to the model", value=False)

    # Load one of the saved test cases (test-data/inputs) into the form, so evaluators can re-run them.
    st.divider()
    TEST_DIR = Path(__file__).resolve().parents[2] / "test-data" / "inputs"
    tests = {}
    for f in sorted(TEST_DIR.glob("T*.json")):
        t = json.loads(f.read_text(encoding="utf-8"))
        if min(t["weekday_hours"], t["weekend_hours"]) >= 0:  # T11 (negative hours) cannot be typed into the form
            tests[t["id"]] = t
    pick = st.selectbox("Load a test case", ["(none)"] + list(tests),
                        format_func=lambda k: k if k == "(none)" else f"{k} – {tests[k]['title']}")
    if st.button("Load into form", disabled=pick == "(none)"):
        t = tests[pick]
        st.session_state.start_date = max(date.fromisoformat(t["start_date"]), date.today())
        st.session_state.weekday_hours = float(t["weekday_hours"])
        st.session_state.weekend_hours = float(t["weekend_hours"])
        st.session_state.slot = t["preferred_slot"]
        st.session_state.notes = t.get("notes", "")
        st.session_state.subjects_df = pd.DataFrame(
            [{"Subject": x["name"], "Exam date": date.fromisoformat(x["exam_date"]),
              "Difficulty": x["difficulty"], "Topics": x.get("topics", "")} for x in t["subjects"]],
            columns=["Subject", "Exam date", "Difficulty", "Topics"])
        st.session_state.pop("subjects_editor", None)
        st.session_state.pop("result", None)
        st.session_state.loaded_test = pick
        st.rerun()
    if st.session_state.get("loaded_test"):
        st.caption(f"Loaded test case {st.session_state.loaded_test}.")

st.title("📅 StudyFlow")
st.caption("Personalised, constraint-aware study timetables from your subjects, exam dates, difficulty and free hours.")

# ---------------------------------------------------------------- input module
today = date.today()
st.session_state.setdefault("start_date", today)
st.session_state.setdefault("weekday_hours", 4.0)
st.session_state.setdefault("weekend_hours", 6.0)
st.session_state.setdefault("slot", "Evening")
c1, c2, c3, c4 = st.columns(4)
start_date = c1.date_input("Start date", min_value=today, key="start_date")
weekday_hours = c2.number_input("Study hours on weekdays", min_value=0.0, max_value=14.0, step=0.5, key="weekday_hours")
weekend_hours = c3.number_input("Study hours on weekends", min_value=0.0, max_value=14.0, step=0.5, key="weekend_hours")
slot = c4.selectbox("Preferred study time", list(SLOT_START), key="slot")

st.subheader("Subjects")
if "subjects_df" not in st.session_state:
    st.session_state.subjects_df = pd.DataFrame([
        {"Subject": "Data Structures", "Exam date": today + timedelta(days=10), "Difficulty": "Hard",
         "Topics": "Trees, Graphs, Dynamic Programming"},
        {"Subject": "Operating Systems", "Exam date": today + timedelta(days=13), "Difficulty": "Medium",
         "Topics": "Scheduling, Deadlocks, Memory Management"},
        {"Subject": "Communication Skills", "Exam date": today + timedelta(days=15), "Difficulty": "Easy", "Topics": ""},
    ])
subjects_df = st.data_editor(
    st.session_state.subjects_df,
    num_rows="dynamic",
    width="stretch",
    column_config={
        "Subject": st.column_config.TextColumn(required=True),
        "Exam date": st.column_config.DateColumn(format="YYYY-MM-DD", required=True),
        "Difficulty": st.column_config.SelectboxColumn(options=list(DIFFICULTY_WEIGHTS), required=True),
        "Topics": st.column_config.TextColumn(help="Optional, comma separated"),
    },
    key="subjects_editor",
)
notes = st.text_input("Extra preferences (optional)", placeholder="e.g. I prefer Maths practice on weekends", key="notes")


def collect_inputs(blocked_dates=None) -> dict:
    subjects = []
    for _, row in subjects_df.iterrows():
        if pd.isna(row.get("Subject")) and pd.isna(row.get("Exam date")):
            continue  # fully empty row added by the editor
        exam = row.get("Exam date")
        subjects.append({
            "name": "" if pd.isna(row.get("Subject")) else str(row["Subject"]),
            "exam_date": "" if pd.isna(exam) else pd.Timestamp(exam).date().isoformat(),
            "difficulty": row.get("Difficulty"),
            "topics": "" if pd.isna(row.get("Topics")) else str(row["Topics"]),
        })
    return {"start_date": start_date.isoformat(), "weekday_hours": weekday_hours, "weekend_hours": weekend_hours,
            "preferred_slot": slot, "subjects": subjects, "notes": notes,
            "blocked_dates": blocked_dates or []}


# ---------------------------------------------------------------- display module
def plan_to_rows(plan: dict) -> list[dict]:
    rows = []
    for day in plan.get("days", []):
        for s in day.get("sessions") or []:
            rows.append({"Date": day.get("date"), "Start": s.get("start"), "End": s.get("end"),
                         "Subject": s.get("subject"), "Activity": s.get("activity"), "Topic": s.get("topic")})
    return rows


def show_result(res: dict):
    for e in res["errors"]:
        st.error(e)
    if res["status"] == "rejected":
        st.info("Fix the inputs above and generate again. No AI call was made.")
        return
    for w in res["warnings"]:
        st.warning(w)
    if show_prompt and res.get("user"):
        with st.expander("Prompt sent to the model", expanded=True):
            st.markdown(f"**Prompt:** `{res['prompt_key']}` · **Model:** `{res['model']}` · "
                        f"**Temperature:** {res.get('temperature')}")
            st.text_area("System prompt", res["system"] or "(none)", height=200)
            st.text_area("User prompt", res["user"], height=300)
    if res["status"] == "text":
        st.info("This older prompt version returns free text, so it cannot be checked automatically.")
        st.markdown(res["raw"])
        return
    if res["status"] != "ok":
        with st.expander("Raw model output"):
            st.code(res["raw"] or "(empty)")
        return

    plan, check = res["plan"], res["check"]
    st.success(plan.get("summary", "Plan generated."))
    if res.get("model") and res["model"] != model:
        st.caption(f"Generated with fallback model `{res['model']}` because `{model}` was out of quota or busy.")
    else:
        st.caption(f"Generated with `{res.get('model', model)}`.")
    for w in plan.get("warnings") or []:
        st.warning(f"AI note: {w}")

    left, right = st.columns([3, 2])
    with right:
        st.markdown("#### Constraint check")
        if check["passed"]:
            st.success("All hard constraints satisfied ✅")
        else:
            st.error(f"{len(check['violations'])} problem(s) found")
            for v in check["violations"]:
                st.markdown(f"- {v}")
        st.markdown("#### Hours per subject")
        totals = pd.DataFrame({"Planned (checked)": check["subject_hours"], "Target": res["targets"]})
        st.bar_chart(totals, stack=False)
        if plan.get("tips"):
            st.markdown("#### Tips")
            for t in plan["tips"]:
                st.markdown(f"- {t}")
    with left:
        st.markdown("#### Your timetable")
        for day in plan.get("days", []):
            sessions = day.get("sessions") or []
            d = day.get("date", "")
            try:
                label = date.fromisoformat(d).strftime("%a %d %b %Y")
            except ValueError:
                label = d
            with st.expander(f"{label} · {len([s for s in sessions if s.get('activity') != 'Break'])} sessions",
                             expanded=False):
                if sessions:
                    st.dataframe(pd.DataFrame(sessions)[["start", "end", "subject", "activity", "topic"]],
                                 hide_index=True, width="stretch")
                else:
                    st.caption("No study planned.")
    rows = plan_to_rows(plan)
    d1, d2 = st.columns(2)
    d1.download_button("Download CSV", pd.DataFrame(rows).to_csv(index=False), "studyflow_plan.csv", "text/csv")
    d2.download_button("Download JSON", json.dumps(plan, indent=2), "studyflow_plan.json", "application/json")


# ---------------------------------------------------------------- actions
if st.button("Generate study plan", type="primary"):
    if not api_key:
        st.error("Add a Gemini API key in the sidebar first.")
    else:
        data = collect_inputs()
        with st.spinner("Building your plan..."):
            st.session_state.result = pipeline.run(data, prompt_key, api_key, model=model)
        st.session_state.data = data

if "result" in st.session_state:
    show_result(st.session_state.result)

    # ------------------------------------------------------------ regeneration module
    res = st.session_state.result
    if res["status"] == "ok":
        st.divider()
        st.subheader("🔁 Something changed? Regenerate the plan")
        calendar_dates = [c["date"] for c in res["calendar"]]
        blocked = st.multiselect("Dates you can no longer study", calendar_dates)
        change = st.text_area("Describe the change", placeholder="e.g. I have a family function on Sunday; "
                              "also give more time to Operating Systems")
        if st.button("Regenerate plan"):
            data = collect_inputs(blocked_dates=blocked)
            with st.spinner("Revising your plan..."):
                new = pipeline.run(data, "P2", api_key, model=model, previous_plan=res["plan"],
                                   change_request=change or f"Cannot study on: {', '.join(blocked)}")
            st.session_state.result, st.session_state.data = new, data
            st.rerun()
