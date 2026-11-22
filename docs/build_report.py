"""Build the Milestone 2 report and the supporting Technical Report (Markdown -> HTML -> PDF).

    pip install markdown
    python docs/build_report.py

Fills docs/report_template.md and docs/technical_report_template.md with the real prompt
files and the saved experiment outputs, then prints PDFs with headless Chrome/Edge.
Intermediate files go to docs/build/; the two PDFs go to docs/.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "application"))
from prompt_builder import PROMPTS, load_prompt  # noqa: E402

DOCS = ROOT / "docs"
BUILD = DOCS / "build"
OUT = ROOT / "test-data" / "outputs"
REPORT_PDF = DOCS / "M2_PE-B13-15_TimetableAndStudyPlanGenerator.pdf"  # M2_TeamID_ProjectTitle.pdf
TECH_PDF = DOCS / "CodeHead_TechnicalReport.pdf"                      # TeamName_DocumentType.pdf
MISSING = "**[FILL – run `python code/notebooks/run_experiments.py` first]**"

VARIABLES = {
    "subject_names": "Comma-separated subject names (v1 only)",
    "subjects_basic": "One line per subject: name, exam date, difficulty (v2)",
    "subjects_table": "One line per subject: name / exam date / difficulty / topics / target hours (computed by planner.py)",
    "calendar_table": "One line per date: date / weekday / available hours / subjects still allowed / note (exam day, blocked)",
    "start_date": "First day of the plan (YYYY-MM-DD)",
    "weekday_hours": "Study hours available Monday to Friday",
    "weekend_hours": "Study hours available Saturday and Sunday",
    "preferred_slot": "Morning / Afternoon / Evening / Night",
    "slot_start": "Start time of the preferred slot (07:00 / 13:00 / 17:00 / 20:00)",
    "notes": "The student's extra preferences, or 'none'",
    "previous_plan": "The JSON plan being revised (P2 only)",
    "change_request": "The student's description of what changed (P2 only)",
}
SHEETS = {
    "P1": ("Create the full day-wise study plan from the validated inputs and the computed planning context.", "T01"),
    "P2": ("Revise an existing plan when the student's availability or needs change.", "T12"),
}


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip()


def fence(text: str, lang: str = "text") -> str:
    return f"```{lang}\n{text}\n```"


def sample_io(test_id: str) -> str:
    f = OUT / "final" / f"{test_id}.json"
    if not f.exists():
        return MISSING
    res = json.loads(f.read_text(encoding="utf-8"))
    plan = res.get("plan") or {}
    excerpt = {"summary": plan.get("summary"), "warnings": plan.get("warnings"),
               "days": (plan.get("days") or [])[:2], "subject_totals": plan.get("subject_totals")}
    total_days = len(plan.get("days") or [])
    check = res.get("check") or {}
    user = res.get("user", "")
    if test_id == "T12":  # do not print the whole previous plan again
        user = re.sub(r"PREVIOUS PLAN \(JSON\)\n.*?\n\nReturn",
                      "PREVIOUS PLAN (JSON)\n<previous plan from the first run - omitted>\n\nReturn", user, flags=re.S)
    return (f"**One sample run – real input (test {test_id}, filled user prompt):**\n\n{fence(user)}\n\n"
            f"**Actual output** (first 2 of {total_days} days shown; full output in "
            f"`test-data/outputs/final/{test_id}.json`):\n\n"
            f"{fence(json.dumps(excerpt, indent=1, ensure_ascii=False), 'json')}\n\n"
            f"Constraint check: **{'passed' if check.get('passed') else 'failed'}**, "
            f"{len(check.get('violations', []))} violation(s). Model: `{res.get('model')}`.")


def prompt_sheets() -> str:
    parts = []
    for pid, (purpose, test_id) in SHEETS.items():
        p = load_prompt(pid)
        var_rows = "\n".join(f"| `{{{v}}}` | {VARIABLES.get(v, '')} |" for v in p.variables)
        parts.append(f"""#### Prompt sheet {pid} – {p.meta['name']}

| Field | Value |
|---|---|
| Prompt ID and name | {pid} – {p.meta['name']} (file `prompts/{PROMPTS[pid]}`) |
| Step in the workflow | {p.meta['step']} |
| Purpose | {purpose} |
| Tool and model | Gemini 3.6 Flash (`gemini-3.6-flash`) via the Gemini API, google-genai Python SDK |
| Settings | temperature {p.meta['temperature']}; response_mime_type application/json; max_output_tokens 32768; others default |
| Number of examples included | {p.meta['examples']} |
| Output format | JSON object: summary, warnings[], days[ {{date, sessions[ {{start, end, subject, activity, topic}} ]}} ], subject_totals[], tips[] |

**Full system prompt:**

{fence(p.system or "none")}

**Full user prompt template:**

{fence(p.user_template)}

**What each variable holds:**

| Variable | Holds |
|---|---|
{var_rows}

{sample_io(test_id)}
""")
    return "\n".join(parts)


def prompt_versions() -> str:
    parts = []
    for v in ("v1", "v2", "v3"):
        p = load_prompt(v)
        parts.append(f"#### {v} – {p.meta['name']} (file `prompts/{PROMPTS[v]}`, temperature {p.meta['temperature']}, "
                     f"output {p.meta['output']})\n\nSystem prompt:\n\n{fence(p.system or 'none')}\n\n"
                     f"User prompt template:\n\n{fence(p.user_template)}\n")
    return "\n".join(parts)


def iteration_results() -> dict:
    f = OUT / "comparison_summary.json"
    if not f.exists():
        return {f"ITER_{v}": "[FILL – run run_experiments.py]" for v in ("v1", "v2", "v3")}
    res = json.loads(f.read_text(encoding="utf-8"))["result"]
    return {f"ITER_{v}": res[v] for v in ("v1", "v2", "v3")}


def strip_h1(text: str) -> str:
    return re.sub(r"^# .*\n", "", text, count=1).strip()


def optional(path: Path) -> str:
    return strip_h1(read(path)) if path.exists() else MISSING


def test_summary() -> str:
    f = OUT / "results_table.md"
    if not f.exists():
        return MISSING
    m = re.search(r"\*\*(\d+)/(\d+) passed\*\*", read(f))
    return f"{m.group(1)} of {m.group(2)} test cases passed." if m else ""


CSS = """
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 22pt; margin: 6px 0; } h2 { font-size: 15pt; border-bottom: 2px solid #3949ab; padding-bottom: 3px; margin-top: 22px; page-break-after: avoid; }
h3 { font-size: 12pt; page-break-after: avoid; } h4 { font-size: 11pt; page-break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 9pt; }
th, td { border: 1px solid #bbb; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #e8eaf6; } tr { page-break-inside: avoid; }
pre { background: #f5f5f5; border: 1px solid #ddd; padding: 8px; font-size: 7.8pt; white-space: pre-wrap; word-break: break-word; }
code { font-family: Consolas, monospace; font-size: 8.5pt; }
img { max-width: 100%; max-height: 900px; display: block; margin: 10px auto 2px; page-break-inside: avoid; }
p > em:only-child { display: block; text-align: center; color: #555; font-size: 9pt; }
.cover { text-align: center; page-break-after: always; padding-top: 10px; }
.cover h2 { border: none; text-align: left; }
.cover table { width: 85%; margin: 14px auto; font-size: 10.5pt; }
@page { size: A4; margin: 16mm 14mm; }
"""


def to_html(md_text: str, title: str) -> str:
    body = markdown.markdown(md_text, extensions=["tables", "fenced_code", "md_in_html"])
    body = body.replace('src="diagrams/', 'src="../diagrams/').replace('src="screenshots/', 'src="../screenshots/')
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>"
            f"<style>{CSS}</style></head><body>{body}</body></html>")


def find_browser() -> str | None:
    for c in [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "google-chrome", "chromium", "chrome", "msedge"]:
        if Path(c).exists() or shutil.which(c):
            return c
    return None


def print_pdf(html: Path, pdf: Path) -> bool:
    browser = find_browser()
    if not browser:
        print(f"No Chrome/Edge found - open {html} in a browser and Print -> Save as PDF.")
        return False
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", html.resolve().as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return pdf.exists()


def main():
    BUILD.mkdir(exist_ok=True)
    tech_md = read(DOCS / "technical_report_template.md").replace("{{TEST_SUMMARY}}", test_summary())
    report_md = read(DOCS / "report_template.md")
    fills = {
        "PROMPT_SHEETS": prompt_sheets(),
        "PROMPT_VERSIONS": prompt_versions(),
        "RESULTS_TABLE": optional(OUT / "results_table.md"),
        "PROMPT_COMPARISON": optional(OUT / "prompt_comparison.md"),
        "TECH_REPORT": strip_h1(tech_md),  # Section 6 = the same document uploaded at Q16
        **iteration_results(),
    }
    for k, v in fills.items():
        report_md = report_md.replace("{{" + k + "}}", v)

    for md_text, name, pdf, title in [(report_md, "Milestone2_Report", REPORT_PDF, "StudyFlow Milestone 2"),
                                       (tech_md, "Technical_Report", TECH_PDF, "StudyFlow Technical Report")]:
        (BUILD / f"{name}.md").write_text(md_text, encoding="utf-8")
        html = BUILD / f"{name}.html"
        html.write_text(to_html(md_text, title), encoding="utf-8")
        ok = print_pdf(html, pdf)
        size = f"{pdf.stat().st_size / 1e6:.2f} MB" if ok else "not created"
        print(f"{name}: {html.relative_to(ROOT)} -> {pdf.name} ({size})")

    remaining = len(re.findall(r"\[FILL", report_md)) + len(re.findall(r"\[FILL", tech_md))
    print(f"\n{remaining} [FILL] placeholder(s) still to complete." if remaining else "\nNo placeholders left.")


if __name__ == "__main__":
    sys.exit(main())
