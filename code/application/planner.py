"""Planning context (task decomposition step).

Before calling the LLM, StudyFlow computes the things an LLM is bad at doing reliably:
the exact list of study dates, the hours available on each date, which subjects are
still allowed on each date (exam not yet written), and a fair target number of hours
per subject. These are injected into the prompt as tables.
"""
from __future__ import annotations

from datetime import date, timedelta

from validation import DIFFICULTY_WEIGHTS, SLOT_START, parse_date

# Recommended minimum preparation hours by difficulty (used only for warnings).
MIN_HOURS = {"Easy": 3, "Medium": 5, "Hard": 8}


def _round_half(x: float) -> float:
    return round(x * 2) / 2


def build_calendar(data: dict) -> list[dict]:
    """One entry per date from start_date up to the day before the last exam."""
    start = parse_date(data["start_date"])
    subjects = [
        {**s, "name": s["name"].strip(), "exam": parse_date(s["exam_date"])} for s in data["subjects"]
    ]
    last_exam = max(s["exam"] for s in subjects)
    blocked = {parse_date(d) for d in data.get("blocked_dates") or []}
    exams_on: dict[date, list[str]] = {}
    for s in subjects:
        exams_on.setdefault(s["exam"], []).append(s["name"])

    calendar = []
    d = start
    while d < last_exam:
        hours = float(data["weekend_hours"] if d.weekday() >= 5 else data["weekday_hours"])
        notes = []
        if d in exams_on:
            hours = _round_half(hours / 2)
            notes.append("Exam today: " + ", ".join(exams_on[d]) + " (half day available)")
        if d in blocked:
            hours = 0.0
            notes.append("Blocked by student - no study")
        allowed = [s["name"] for s in subjects if s["exam"] > d]
        if not allowed:
            hours = 0.0
        calendar.append(
            {"date": d.isoformat(), "weekday": d.strftime("%a"), "hours": hours, "allowed": allowed, "note": "; ".join(notes)}
        )
        d += timedelta(days=1)
    return calendar


def target_hours(data: dict, calendar: list[dict]) -> dict[str, float]:
    """Share the total available hours by difficulty weight, capped by feasibility.

    Ideal share = total hours x weight / sum of weights. A subject can only use hours before
    its own exam, so for every exam (in date order) the subjects examined by then must fit
    into the hours available before it; any excess is trimmed proportionally and handed to
    later subjects. Repeating this a few times converges to a feasible, difficulty-weighted split.
    """
    subs = sorted(data["subjects"], key=lambda s: parse_date(s["exam_date"]))
    names = [s["name"].strip() for s in subs]
    weight = {s["name"].strip(): DIFFICULTY_WEIGHTS[s["difficulty"]] for s in subs}
    hours_before = {
        s["name"].strip(): sum(c["hours"] for c in calendar if c["date"] < parse_date(s["exam_date"]).isoformat())
        for s in subs
    }
    total = sum(c["hours"] for c in calendar)
    target = {n: 0.0 for n in names}
    for _ in range(50):
        left = total - sum(target.values())
        if left < 1e-6:
            break
        w_sum = sum(weight.values())
        for n in names:
            target[n] += left * weight[n] / w_sum
        for k, n in enumerate(names):  # enforce "exams so far fit in hours before this exam"
            prefix = names[: k + 1]
            excess = sum(target[p] for p in prefix) - hours_before[n]
            if excess > 1e-9:
                p_sum = sum(target[p] for p in prefix)
                for p in prefix:
                    target[p] -= excess * target[p] / p_sum
    return {n: _round_half(h) for n, h in target.items()}


def time_warnings(data: dict, targets: dict[str, float]) -> list[str]:
    warnings = []
    for s in data["subjects"]:
        name = s["name"].strip()
        need = MIN_HOURS[s["difficulty"]]
        if targets[name] < need:
            warnings.append(
                f"Insufficient time for {name} ({s['difficulty']}): about {targets[name]:g} h available before the exam, "
                f"recommended at least {need} h. The plan will be compressed."
            )
    return warnings


def build_context(data: dict) -> dict:
    """Everything the prompt templates need, as plain strings."""
    calendar = build_calendar(data)
    targets = target_hours(data, calendar)
    subjects_sorted = sorted(data["subjects"], key=lambda s: parse_date(s["exam_date"]))

    subjects_table = "\n".join(
        f"- {s['name'].strip()} | {s['exam_date']} | {s['difficulty']} | "
        f"{(s.get('topics') or '').strip() or 'not specified'} | ~{targets[s['name'].strip()]:g} h"
        for s in subjects_sorted
    )
    subjects_basic = "\n".join(
        f"- {s['name'].strip()} (exam on {s['exam_date']}, difficulty: {s['difficulty']})" for s in subjects_sorted
    )
    calendar_table = "\n".join(
        f"- {c['date']} | {c['weekday']} | {c['hours']:g} h | {', '.join(c['allowed']) or 'none'} | {c['note'] or '-'}"
        for c in calendar
    )
    return {
        "start_date": str(data["start_date"]),
        "weekday_hours": f"{float(data['weekday_hours']):g}",
        "weekend_hours": f"{float(data['weekend_hours']):g}",
        "preferred_slot": data["preferred_slot"],
        "slot_start": SLOT_START[data["preferred_slot"]],
        "notes": (data.get("notes") or "").strip() or "none",
        "subject_names": ", ".join(s["name"].strip() for s in subjects_sorted),
        "subjects_basic": subjects_basic,
        "subjects_table": subjects_table,
        "calendar_table": calendar_table,
        # structured copies for the app / checker
        "_calendar": calendar,
        "_targets": targets,
        "_warnings": time_warnings(data, targets),
    }
