"""Offline tests (no API key needed): python -m pytest code/application/tests"""
import json
import sys
from datetime import date
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parents[1]
sys.path.insert(0, str(APP))

from checker import check_plan  # noqa: E402
from planner import build_calendar, build_context, target_hours  # noqa: E402
from prompt_builder import PROMPTS, load_prompt  # noqa: E402
from validation import validate  # noqa: E402

TODAY = date(2026, 11, 23)


def load(tid):
    return json.loads((ROOT / "test-data" / "inputs" / f"{tid}.json").read_text(encoding="utf-8"))


def test_invalid_inputs_rejected():
    assert any("already passed" in e for e in validate(load("T09"), TODAY).errors)
    assert any("No subjects" in e for e in validate(load("T10"), TODAY).errors)
    assert any("negative" in e for e in validate(load("T11"), TODAY).errors)


def test_valid_and_edge_inputs_accepted():
    for tid in ["T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T12"]:
        assert validate(load(tid), TODAY).ok, tid


def test_edge_warnings():
    assert any("same day" in w for w in validate(load("T07"), TODAY).warnings)
    assert any("Very little" in w for w in validate(load("T06"), TODAY).warnings)
    assert build_context(load("T06"))["_warnings"]  # insufficient time


def test_calendar_rules():
    t = load("T04")
    cal = {c["date"]: c for c in build_calendar(t)}
    assert "2026-12-03" not in cal  # last exam day not planned
    assert "Computer Networks" not in cal["2026-12-01"]["allowed"]  # exam that day
    assert cal["2026-12-01"]["hours"] == 2.0  # half day on exam day (weekday 4h)
    assert cal["2026-11-28"]["hours"] == 6  # Saturday = weekend hours


def test_blocked_dates_and_targets():
    t = {**load("T01"), "blocked_dates": ["2026-11-29"]}
    cal = build_calendar(t)
    assert next(c for c in cal if c["date"] == "2026-11-29")["hours"] == 0
    targets = target_hours(t, cal)
    assert targets["DBMS"] > targets["Discrete Maths"]
    assert abs(sum(targets.values()) - sum(c["hours"] for c in cal)) <= 1.5


def test_all_prompts_render():
    t = load("T01")
    ctx = build_context(t)
    ctx.update(previous_plan="{}", change_request="none")
    for key in PROMPTS:
        p = load_prompt(key)
        text = p.render(ctx)
        assert p.variables, key
        assert not any("{" + v + "}" in text for v in p.variables), key
    assert load_prompt("P1").json_output and not load_prompt("v1").json_output
    assert load_prompt("v1").system == "" and load_prompt("P1").temperature == 0.3
    # final P1 must be identical to v3 (the version it was promoted from)
    assert load_prompt("P1").system == load_prompt("v3").system
    assert load_prompt("P1").user_template == load_prompt("v3").user_template


def _good_plan():
    return {"days": [
        {"date": "2026-11-23", "sessions": [
            {"start": "17:00", "end": "18:30", "subject": "DBMS", "activity": "Study", "topic": "ER"},
            {"start": "18:30", "end": "18:45", "subject": "Break", "activity": "Break", "topic": ""},
            {"start": "18:45", "end": "19:45", "subject": "Operating Systems", "activity": "Revision", "topic": ""},
        ]},
        {"date": "2026-11-24", "sessions": [
            {"start": "17:00", "end": "18:00", "subject": "DBMS", "activity": "Revision", "topic": ""},
            {"start": "18:15", "end": "19:15", "subject": "Discrete Maths", "activity": "Revision", "topic": ""},
        ]},
    ]}


def test_checker_passes_good_plan():
    t = load("T01")
    r = check_plan(_good_plan(), t, build_calendar(t))
    assert r["passed"], r["violations"]
    assert r["subject_hours"]["DBMS"] == 2.5


def test_checker_catches_violations():
    t = load("T01")
    plan = _good_plan()
    plan["days"][0]["sessions"].append(
        {"start": "19:00", "end": "22:00", "subject": "DBMS", "activity": "Study", "topic": ""})  # overlap + too many hours
    plan["days"].append({"date": "2026-12-05", "sessions": [
        {"start": "09:00", "end": "10:00", "subject": "DBMS", "activity": "Study", "topic": ""}]})  # exam day
    v = " ".join(check_plan(plan, t, build_calendar(t))["violations"])
    assert "overlap" in v and "available" in v and "exam" in v
