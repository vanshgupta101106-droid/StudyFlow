"""End-to-end StudyFlow workflow, shared by the Streamlit app and the experiment runner.

validate -> build planning context -> render prompt -> call LLM -> parse -> check constraints
"""
from __future__ import annotations

import json
from datetime import date

import llm
from checker import check_plan
from planner import build_context
from prompt_builder import load_prompt
from validation import validate


def run(data: dict, prompt_key: str, api_key: str, *, model: str = llm.DEFAULT_MODEL,
        today: date | None = None, previous_plan: dict | None = None, change_request: str = "") -> dict:
    result = {"prompt_key": prompt_key, "model": model, "status": "", "errors": [], "warnings": [],
              "system": "", "user": "", "raw": "", "plan": None, "check": None}

    v = validate(data, today=today)
    result["errors"], result["warnings"] = v.errors, list(v.warnings)
    if not v.ok:
        result["status"] = "rejected"
        return result

    ctx = build_context(data)
    result["warnings"] += ctx["_warnings"]
    result["calendar"] = ctx["_calendar"]
    result["targets"] = ctx["_targets"]

    prompt = load_prompt(prompt_key)
    values = dict(ctx)
    if prompt_key == "P2":
        values["previous_plan"] = json.dumps(previous_plan or {}, indent=1)
        values["change_request"] = change_request.strip() or "none"
    result["system"], result["user"] = prompt.system, prompt.render(values)
    result["temperature"] = prompt.temperature

    try:
        result["raw"] = llm.generate(result["system"], result["user"], temperature=prompt.temperature,
                                     json_output=prompt.json_output, api_key=api_key, model=model)
    except Exception as e:
        result["status"] = "llm_error"
        result["errors"] = [str(e)]
        return result

    if not prompt.json_output:
        result["status"] = "text"  # v1/v2 baselines: free text, cannot be checked automatically
        return result
    try:
        result["plan"] = llm.parse_json(result["raw"])
    except Exception as e:
        result["status"] = "invalid_json"
        result["errors"] = [f"Model output was not valid JSON: {e}"]
        return result
    result["check"] = check_plan(result["plan"], data, ctx["_calendar"])
    result["status"] = "ok"
    return result
