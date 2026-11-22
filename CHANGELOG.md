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

## 2026-11-22
- Switched the model to `gemini-3.6-flash`: `gemini-2.5-flash` is no longer available to new API keys, and 3.7/3.8 returned "high demand" (503) errors. Diagrams re-rendered with the new model name.
- Ran `run_experiments.py` with gemini-3.6-flash: **12/12 tests passed** (8 valid inputs with 0 violations, 3 invalid inputs rejected before any AI call, regeneration T12 passed). Outputs saved in `test-data/outputs/`.
- Prompt comparison (T01, T06 x 3 runs per version): 8 of the 18 calls failed with the free-tier daily quota error (HTTP 429). The runner now records API failures separately instead of counting them as prompt results, and `--recompute` rebuilds the counts from saved outputs without calling the API.
- Added automatic model fallback in `llm.py` (3.5 Flash-Lite, then 3.5 / 3.7 / 3.8 Flash) for quota and overload errors, plus a 150 s request timeout. The app shows which model produced each plan.
- Added a "Load a test case" control to the sidebar so the saved test inputs can be re-run in the app.
- Filled team details, the contribution table and the module statuses in the report.
