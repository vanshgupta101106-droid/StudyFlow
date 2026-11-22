# StudyFlow – Technical Report
**Team CodeHead (PE-B13-15) · SCSE4041 Prompt Engineering · Problem C20: Timetable and Study Plan Generator**

**1. Purpose.** StudyFlow generates a personalised, day-wise study timetable from a student's subjects, exam dates, difficulty levels and available hours. It then verifies automatically that the timetable respects those constraints.

**2. Architecture.** StudyFlow is a single Python application built with Streamlit and deployed on Streamlit Community Cloud. One request runs through six components:

- `validation.py` checks the inputs.
- `planner.py` builds the availability calendar and the target hours.
- `prompt_builder.py` loads the versioned prompt files and fills them in.
- `llm.py` calls Gemini.
- `checker.py` verifies the plan.
- `app.py` handles input, display and regeneration.

The same `pipeline.py` is used by the web app and by the experiment runner (`code/notebooks/run_experiments.py`), so the tests exercise exactly the code that users run.

**3. Tools and models.**

- **Model and API:** Google Gemini `gemini-2.5-flash` via the `google-genai` SDK, in JSON response mode.
- **Settings:** temperature 0.3 for the final prompts, with up to 3 retries on transient errors.
- **App stack:** Python 3, Streamlit, pandas, and Mermaid for the diagrams.
- **Secrets:** the API key is kept in Streamlit secrets and is never committed.

**4. Prompt design.** Two final prompts are used.

- **P1 (generate):** an expert-planner role, plus four hard constraints that must never be broken: allowed dates and subjects, daily hour limits, no overlaps, and revision for every subject. It also has five soft goals: target hours, the preferred slot, 45–90-minute sessions with breaks, topic ordering, and practice for harder subjects. It ends with a strict JSON schema and a one-day format example (one-shot).
- **P2 (regenerate):** the same rules plus a revision-mode instruction, the previous plan and the student's change request.

The key design decision was **task decomposition**. Date arithmetic and hour budgeting are computed in code and given to the model as tables, so the model only does the creative scheduling. The prompt went through three saved versions:

| Version | Approach | Output |
|---|---|---|
| v1 | Subject names only | Free text |
| v2 | Constraints and a role | Markdown table |
| v3 | Structured calendar, hard/soft rules and a schema | JSON |

Only v3 output can be checked by a program.

**5. Testing.** {{TEST_SUMMARY}} The test set has three parts:

- 5 normal cases
- 4 edge cases: 1 hour per day, two exams on the same day, an exam tomorrow, and regeneration
- 3 invalid cases: a past exam date, no subjects, and negative hours

A test passes only when three things hold:

- the output parses as JSON;
- the constraint checker reports 0 violations;
- the test's own expectations are met, for example a Hard subject receiving more hours than an Easy one, or a same-day-exam warning being shown.

Invalid inputs must be rejected before any AI call. Each prompt version was also run 3 times on the same two inputs to compare v1, v2 and v3 with counts. Besides the AI tests, 8 offline unit tests cover validation, calendar building, target hours, prompt rendering and the checker.

**6. Limitations and next steps.** The checker detects violations but does not yet repair them. In Milestone 3 we plan to add an automatic "repair" call that sends the violations back to the model. Other limitations:

- The free API tier is rate-limited.
- Plans are not stored between sessions.
- Topics are generic when the student gives none.

Further plans for Milestone 3 are calendar (.ics) export, saved plans and progress tracking.
