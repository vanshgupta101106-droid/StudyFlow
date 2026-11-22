"""Run StudyFlow test cases and prompt-version experiments, and save every output.

Usage (from the repository root):
    set GEMINI_API_KEY=...            (Windows)   |   export GEMINI_API_KEY=...   (mac/Linux)
    python code/notebooks/run_experiments.py                 # all tests + v1/v2/v3 comparison
    python code/notebooks/run_experiments.py --tests T01 T06  # only some tests
    python code/notebooks/run_experiments.py --no-compare     # skip the prompt-version comparison

Writes:
    test-data/outputs/final/<TEST>.json      raw output + check result for each test (final prompt P1/P2)
    test-data/outputs/v1|v2|v3/<TEST>_runN.*  outputs of each prompt version (3 runs each) for the comparison
    test-data/outputs/comparison_summary.json counts used in the prompt iteration log
    test-data/outputs/results_table.md       Section 4 test table (paste into the report)
    test-data/outputs/prompt_comparison.md   Section 3 before/after evidence
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "application"))

import llm  # noqa: E402
import pipeline  # noqa: E402

INPUTS = ROOT / "test-data" / "inputs"
OUTPUTS = ROOT / "test-data" / "outputs"


def load_test(tid: str) -> dict:
    return json.loads((INPUTS / f"{tid}.json").read_text(encoding="utf-8"))


def input_summary(t: dict) -> str:
    """Short input description for the test table; the full input is in test-data/inputs/."""
    return f"{t['title']}; {t['weekday_hours']:g} h weekday / {t['weekend_hours']:g} h weekend"


def short_name(name: str) -> str:
    words = name.split()
    return "".join(w[0] for w in words).upper() if len(words) > 1 else name


def save(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(obj, str):
        path.write_text(obj, encoding="utf-8")
    else:
        path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")


def judge(t: dict, res: dict) -> tuple[str, str]:
    """Return (actual output summary, Pass/Fail) using objective rules only."""
    if t["type"] == "Invalid":
        if res["status"] == "rejected":
            return "Rejected before AI call: " + res["errors"][0], "Pass"
        return f"Not rejected (status {res['status']})", "Fail"
    if res["status"] != "ok":
        return f"{res['status']}: {' '.join(res['errors'])[:120]}", "Fail"
    check = res["check"]
    hours = ", ".join(f"{short_name(k)} {v:.1f}h" for k, v in check["subject_hours"].items())
    warn = f"; {len(res['warnings'])} warning(s) shown" if res["warnings"] else ""
    if not check["passed"]:
        return f"{len(check['violations'])} violation(s), e.g. {check['violations'][0]}", "Fail"
    # test-specific expectations from the "checks" field of the test input
    problems = []
    for more, less in t.get("checks", {}).get("more_hours", []):
        h = check["subject_hours"]
        if not h.get(more, 0) > h.get(less, 0):
            problems.append(f"{short_name(more)} {h.get(more, 0):.1f}h not more than {short_name(less)} {h.get(less, 0):.1f}h")
    for text in t.get("checks", {}).get("warning_contains", []):
        if not any(text.lower() in w.lower() for w in res["warnings"]):
            problems.append(f"expected warning '{text}' not shown")
    if problems:
        return f"0 violations but {'; '.join(problems)}", "Fail"
    return f"Valid JSON, 0 violations; {hours}{warn}", "Pass"


def run_tests(ids, api_key, model, pause):
    rows = []
    for tid in ids:
        t = load_test(tid)
        today = date.fromisoformat(t["today"])
        print(f"[{tid}] {t['title']} ...", flush=True)
        res = pipeline.run(t, "P1", api_key, model=model, today=today)
        extra = ""
        if t.get("change_request") and res["status"] == "ok":
            first_check = res["check"]
            regen_input = {**t, "blocked_dates": t.get("blocked_dates_after", [])}
            time.sleep(pause)
            res2 = pipeline.run(regen_input, "P2", api_key, model=model, today=today,
                                previous_plan=res["plan"], change_request=t["change_request"])
            save(OUTPUTS / "final" / f"{tid}_before_regeneration.json", res)
            res = res2
            extra = f" (first plan: {'0' if first_check['passed'] else len(first_check['violations'])} violation(s))"
        save(OUTPUTS / "final" / f"{tid}.json", res)
        actual, verdict = judge(t, res)
        rows.append((tid, input_summary(t), t["type"], t["expected"], actual + extra, verdict))
        print(f"    -> {verdict}: {actual[:120]}")
        if res["status"] != "rejected":
            time.sleep(pause)
    return rows


def text_metrics(text: str, t: dict) -> dict:
    low = text.lower()
    return {
        "subjects": all(s["name"].lower() in low for s in t["subjects"]),
        "revision": "revis" in low,
        "dates": t["start_date"] in text or t["start_date"][5:] in text,
    }


def run_comparison(ids, runs, api_key, model, pause):
    """Run v1, v2 and v3 `runs` times on each comparison test and count objective outcomes."""
    stats = {v: {"n": 0, "subjects": 0, "dates": 0, "revision": 0, "json": 0, "zero_viol": 0, "viol": []}
             for v in ("v1", "v2", "v3")}
    for tid in ids:
        t = load_test(tid)
        today = date.fromisoformat(t["today"])
        for key in ("v1", "v2", "v3"):
            for r in range(1, runs + 1):
                print(f"[compare {tid} {key} run {r}] ...", flush=True)
                res = pipeline.run(t, key, api_key, model=model, today=today)
                st = stats[key]
                if key == "v3":
                    save(OUTPUTS / key / f"{tid}_run{r}.json", res)
                else:
                    save(OUTPUTS / key / f"{tid}_run{r}.md", res["raw"] or "\n".join(res["errors"]))
                if res["status"] == "llm_error":
                    # API failure (quota / outage), not a prompt result: do not count it
                    st["api_errors"] = st.get("api_errors", 0) + 1
                    time.sleep(pause)
                    continue
                st["n"] += 1
                m = text_metrics(res["raw"] or "", t)
                for k in ("subjects", "dates", "revision"):
                    st[k] += m[k]
                if res["status"] == "ok":
                    st["json"] += 1
                    n_viol = len(res["check"]["violations"])
                    st["viol"].append(n_viol)
                    st["zero_viol"] += n_viol == 0
                time.sleep(pause)
    write_comparison(ids, runs, model, stats)


def recompute_from_saved(ids, runs, model):
    """Rebuild the comparison counts from the saved output files, without calling the API."""
    stats = {v: {"n": 0, "subjects": 0, "dates": 0, "revision": 0, "json": 0, "zero_viol": 0, "viol": []}
             for v in ("v1", "v2", "v3")}
    for tid in ids:
        t = load_test(tid)
        for key in ("v1", "v2", "v3"):
            for r in range(1, runs + 1):
                st = stats[key]
                if key == "v3":
                    res = json.loads((OUTPUTS / key / f"{tid}_run{r}.json").read_text(encoding="utf-8"))
                    raw, status = res.get("raw") or "", res["status"]
                else:
                    raw = (OUTPUTS / key / f"{tid}_run{r}.md").read_text(encoding="utf-8")
                    status = "llm_error" if raw.startswith("LLM call failed") else "text"
                if status == "llm_error":
                    st["api_errors"] = st.get("api_errors", 0) + 1
                    continue
                st["n"] += 1
                m = text_metrics(raw, t)
                for k in ("subjects", "dates", "revision"):
                    st[k] += m[k]
                if status == "ok":
                    st["json"] += 1
                    st["viol"].append(len(res["check"]["violations"]))
                    st["zero_viol"] += len(res["check"]["violations"]) == 0
    write_comparison(ids, runs, model, stats)


def write_comparison(ids, runs, model, stats):
    def result_text(v):
        st = stats[v]
        n = st["n"]
        base = (f"{n} runs ({', '.join(ids)} x {runs}): all subjects named {st['subjects']}/{n}, "
                f"real start date used {st['dates']}/{n}, revision mentioned {st['revision']}/{n}")
        if v == "v3":
            avg = sum(st["viol"]) / len(st["viol"]) if st["viol"] else 0
            return (base + f"; valid JSON {st['json']}/{n}; 0 constraint violations in {st['zero_viol']}/{n} "
                    f"(average {avg:.1f} violations per run)")
        return base + "; free text, so constraints could not be checked automatically (0/" + str(n) + " machine-checkable)"

    summary = {v: result_text(v) for v in stats}
    save(OUTPUTS / "comparison_summary.json", {"model": model, "tests": ids, "runs": runs, "stats": stats, "result": summary})
    lines = ["# Prompt version comparison", "",
             f"Model `{model}` · {datetime.now():%Y-%m-%d %H:%M} · same inputs ({', '.join(ids)}), {runs} runs per version", "",
             "| Version | All subjects named | Real start date used | Revision mentioned | Valid JSON | 0 constraint violations |",
             "|---|---|---|---|---|---|"]
    for v, st in stats.items():
        n = st["n"]
        js = f"{st['json']}/{n}" if v == "v3" else "n/a (free text)"
        zv = f"{st['zero_viol']}/{n}" if v == "v3" else "not checkable"
        lines.append(f"| {v} | {st['subjects']}/{n} | {st['dates']}/{n} | {st['revision']}/{n} | {js} | {zv} |")
    errs = {v: st.get("api_errors", 0) for v, st in stats.items() if st.get("api_errors")}
    if errs:
        lines += ["", "Runs that failed with an API error (for example the free-tier daily quota, HTTP 429) are "
                  "not prompt results, so they are excluded from the counts above: "
                  + ", ".join(f"{v}: {n}" for v, n in errs.items()) + "."]
    lines += ["", "Saved outputs: `test-data/outputs/v1/`, `v2/`, `v3/` (one file per run)."]
    save(OUTPUTS / "prompt_comparison.md", "\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", nargs="*", help="Test IDs, default: all in test-data/inputs")
    ap.add_argument("--compare", nargs="*", default=["T01", "T06"], help="Tests used for the v1/v2/v3 comparison")
    ap.add_argument("--runs", type=int, default=3, help="Runs per prompt version in the comparison")
    ap.add_argument("--no-compare", action="store_true")
    ap.add_argument("--model", default=llm.DEFAULT_MODEL)
    ap.add_argument("--pause", type=float, default=7.0, help="Seconds between calls (free-tier rate limits)")
    ap.add_argument("--recompute", action="store_true",
                    help="Only rebuild the comparison counts from saved outputs (no API calls)")
    args = ap.parse_args()

    if args.recompute:
        recompute_from_saved(args.compare, args.runs, args.model)
        print("Comparison rebuilt -> test-data/outputs/prompt_comparison.md")
        return

    api_key = llm.get_api_key()
    if not api_key:
        sys.exit("Set the GEMINI_API_KEY environment variable first.")
    ids = args.tests or sorted(p.stem for p in INPUTS.glob("T*.json"))

    rows = run_tests(ids, api_key, args.model, args.pause)
    passed = sum(r[5] == "Pass" for r in rows)
    md = ["# Test results (final prompt P1, P2 for regeneration)", "",
          f"Model: `{args.model}` · run on {datetime.now():%Y-%m-%d %H:%M} · **{passed}/{len(rows)} passed**", "",
          "| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail |", "|---|---|---|---|---|---|"]
    md += ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows]
    save(OUTPUTS / "results_table.md", "\n".join(md) + "\n")
    print(f"\n{passed}/{len(rows)} passed -> test-data/outputs/results_table.md")

    if not args.no_compare:
        run_comparison(args.compare, args.runs, api_key, args.model, args.pause)
        print("Comparison -> test-data/outputs/prompt_comparison.md")


if __name__ == "__main__":
    main()
