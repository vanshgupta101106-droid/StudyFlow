"""Output constraint checker.

Verifies a generated JSON plan against the hard constraints, so that test results are
measured, not assumed. Used by the app (shown to the student) and by the experiment runner.
"""
from __future__ import annotations

from datetime import datetime

from validation import parse_date

ACTIVITIES = {"Study", "Practice", "Revision", "Break"}
TOLERANCE_H = 0.25  # allow 15 minutes of rounding per day


def _minutes(hhmm: str) -> int:
    t = datetime.strptime(hhmm.strip(), "%H:%M")
    return t.hour * 60 + t.minute


def check_plan(plan: dict, data: dict, calendar: list[dict]) -> dict:
    violations: list[str] = []
    exam = {s["name"].strip().lower(): parse_date(s["exam_date"]) for s in data["subjects"]}
    display = {s["name"].strip().lower(): s["name"].strip() for s in data["subjects"]}
    hours_on = {c["date"]: c["hours"] for c in calendar}
    subject_hours = {name: 0.0 for name in display.values()}
    revised: set[str] = set()

    days = plan.get("days")
    if not isinstance(days, list):
        return {"passed": False, "violations": ["Output has no 'days' list."], "subject_hours": subject_hours}

    for day in days:
        d = str(day.get("date", ""))
        if d not in hours_on:
            if day.get("sessions"):
                violations.append(f"{d}: date is outside the planning calendar.")
            continue
        intervals = []
        study_min = 0
        for s in day.get("sessions") or []:
            try:
                a, b = _minutes(s["start"]), _minutes(s["end"])
            except (KeyError, ValueError, AttributeError):
                violations.append(f"{d}: session has invalid start/end time: {s}")
                continue
            if b <= a:
                violations.append(f"{d}: session {s['start']}-{s['end']} ends before it starts.")
                continue
            intervals.append((a, b, s))
            activity = s.get("activity")
            if activity not in ACTIVITIES:
                violations.append(f"{d}: unknown activity '{activity}'.")
            if activity == "Break":
                continue
            key = str(s.get("subject", "")).strip().lower()
            if key not in exam:
                violations.append(f"{d}: unknown subject '{s.get('subject')}'.")
                continue
            if parse_date(d) >= exam[key]:
                violations.append(f"{d}: {display[key]} scheduled on/after its exam date ({exam[key]}).")
            study_min += b - a
            subject_hours[display[key]] += (b - a) / 60
            if activity == "Revision":
                revised.add(key)

        intervals.sort(key=lambda x: x[0])
        for (a1, b1, s1), (a2, _, s2) in zip(intervals, intervals[1:]):
            if a2 < b1:
                violations.append(f"{d}: sessions {s1['start']}-{s1['end']} and {s2['start']}-{s2['end']} overlap.")
        if study_min / 60 > hours_on[d] + TOLERANCE_H:
            violations.append(f"{d}: {study_min / 60:.2f} h of study planned but only {hours_on[d]:g} h available.")

    for key, name in display.items():
        if subject_hours[name] == 0:
            violations.append(f"{name} never appears in the plan.")
        elif key not in revised:
            violations.append(f"{name} has no Revision session.")

    return {
        "passed": not violations,
        "violations": violations,
        "subject_hours": {k: round(v, 2) for k, v in subject_hours.items()},
    }
