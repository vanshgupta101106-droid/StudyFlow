# Changelog

All progress after Milestone 1. Dates are YYYY-MM-DD.

## 2026-11-18
- Created the repository structure (`prompts/`, `code/`, `test-data/`, `docs/`).
- Prompt v1 (baseline): subject names only, no role, no constraints.
- Prompt v2: added a role, exam dates, difficulty, weekday/weekend hours, preferred slot and 3 scheduling rules; markdown output.
- Prompt v3: hard constraints separated from soft goals, a pre-computed availability calendar and target hours, mandatory revision and breaks, a one-day format example and a strict JSON schema. Promoted to final prompt P1.
- Prompt P2 (regeneration) added for the Regeneration module.
- Implemented the input validation, planning context (calendar + difficulty-weighted target hours), prompt builder, Gemini client, constraint checker and shared pipeline.
- Fixed the target-hours allocation: a day-by-day split gave an Easy subject with the last exam more hours than a Hard one. It was replaced by a weighted share of the total hours, capped by the hours available before each exam.
- Built the Streamlit app: input form, validation messages, day-wise timetable, hours chart, constraint-check panel, CSV/JSON download, prompt-version switcher and regeneration.
- Added 12 test inputs (T01–T12), the experiment runner and 8 offline unit tests (all passing).
- Added 4 diagrams (prompt workflow, task decomposition, input-output flow, system architecture).
- Added report templates and `docs/build_report.py` for the Milestone 2 PDFs.

## 2026-11-19
- Aligned the project with the Milestone 2 guidelines. Each prompt is now one `.txt` file; template variables use `{name}`.
- The experiment runner now runs each prompt version 3 times on the same inputs and reports counts for the iteration log.
- Test pass criteria now include the test-specific expectations (hour ordering by difficulty, expected warnings), so a pass means the Expected column was met.
- Report restructured to the 7 required sections and headings; module table uses the Working / Partly working / Not started statuses.

## [FILL date]
- Ran `run_experiments.py` with gemini-3.6-flash: [FILL x/12 passed]. Saved outputs in `test-data/outputs/`.
- Deployed to Streamlit Community Cloud: [FILL link].
- [FILL any prompt or code changes made after seeing the test results]
