"""Input Validation Module.

Checks the student's inputs before any prompt is built or any LLM call is made.
Errors block generation; warnings are shown to the student and passed to the model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

DIFFICULTY_WEIGHTS = {"Easy": 1.0, "Medium": 1.5, "Hard": 2.0}
SLOT_START = {"Morning": "07:00", "Afternoon": "13:00", "Evening": "17:00", "Night": "20:00"}
MAX_DAILY_HOURS = 14
MAX_PLAN_DAYS = 60


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _hours(value, label: str, result: ValidationResult) -> float | None:
    try:
        h = float(value)
    except (TypeError, ValueError):
        result.errors.append(f"{label} must be a number.")
        return None
    if h < 0:
        result.errors.append(f"{label} cannot be negative (got {h:g}).")
        return None
    if h > MAX_DAILY_HOURS:
        result.errors.append(f"{label} cannot be more than {MAX_DAILY_HOURS} hours (got {h:g}).")
        return None
    return h


def validate(data: dict, today: date | None = None) -> ValidationResult:
    """Validate a StudyFlow input dict. `today` is injectable for reproducible tests."""
    today = today or date.today()
    r = ValidationResult()

    start = parse_date(data.get("start_date"))
    if start is None:
        r.errors.append("Start date is missing or not in YYYY-MM-DD format.")
    elif start < today:
        r.errors.append(f"Start date {start} is in the past.")

    wd = _hours(data.get("weekday_hours"), "Weekday study hours", r)
    we = _hours(data.get("weekend_hours"), "Weekend study hours", r)
    if wd is not None and we is not None:
        if wd == 0 and we == 0:
            r.errors.append("You have 0 study hours on every day, so no plan can be made.")
        elif 0 < wd <= 1 or 0 < we <= 1:
            r.warnings.append("Very little daily study time (1 hour or less). The plan will be compressed.")

    if data.get("preferred_slot") not in SLOT_START:
        r.errors.append(f"Preferred slot must be one of: {', '.join(SLOT_START)}.")

    subjects = data.get("subjects") or []
    if not subjects:
        r.errors.append("No subjects entered. Add at least one subject with an exam date.")
        return r

    seen: set[str] = set()
    exam_dates: dict[date, list[str]] = {}
    for i, s in enumerate(subjects, start=1):
        name = str(s.get("name") or "").strip()
        label = name or f"Subject #{i}"
        if not name:
            r.errors.append(f"Subject #{i} has no name.")
        elif name.lower() in seen:
            r.errors.append(f"Subject '{name}' is entered more than once.")
        elif name.lower() == "break":
            r.errors.append("'Break' cannot be used as a subject name.")
        seen.add(name.lower())

        if s.get("difficulty") not in DIFFICULTY_WEIGHTS:
            r.errors.append(f"{label}: difficulty must be Easy, Medium or Hard.")

        exam = parse_date(s.get("exam_date"))
        if exam is None:
            r.errors.append(f"{label}: exam date is missing or not in YYYY-MM-DD format.")
            continue
        if exam < today:
            r.errors.append(f"{label}: exam date {exam} has already passed.")
            continue
        if start is not None:
            if exam <= start:
                r.errors.append(f"{label}: exam date {exam} is on or before the start date, so there are no days to prepare.")
                continue
            if (exam - start).days > MAX_PLAN_DAYS:
                r.errors.append(f"{label}: exam is more than {MAX_PLAN_DAYS} days away. Choose a later start date.")
                continue
        exam_dates.setdefault(exam, []).append(label)

    for d, names in sorted(exam_dates.items()):
        if len(names) > 1:
            r.warnings.append(f"{len(names)} exams on the same day ({d}): {', '.join(names)}.")
    return r
