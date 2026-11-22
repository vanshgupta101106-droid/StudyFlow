# Milestone 2 – Submission Guide (team-internal, not part of the report)

- **Deadline:** Sunday 22 Nov 2026, 11:59 PM. Late submissions are not accepted.
- **Who submits:** Ronit only, one form for the whole team.
- **Fill the form in one sitting.** Keep everything below ready first, because a half-filled form may not be saved.
- **Questions for faculty:** ask before 20 November, for example about Q8 project-type options.
- **Links:** if an evaluator cannot open a link or file, that part gets **0**. Test every link in an incognito window.

## Step-by-step

| # | Task | Owner | Done |
|---|---|---|---|
| 1 | Get a free Gemini API key at aistudio.google.com/apikey. Never paste it into any file that gets committed | [FILL] | [ ] |
| 2 | Run `pip install -r requirements.txt pytest markdown`, then `python -m pytest code/application/tests` (expect 8 passed) | | [ ] |
| 3 | Run the app locally with `streamlit run code/application/app.py` and try test T01's inputs | | [ ] |
| 4 | Set `GEMINI_API_KEY` (PowerShell: `$env:GEMINI_API_KEY="…"`), then run `python code/notebooks/run_experiments.py`. This makes about 31 calls and takes about 6 minutes | | [ ] |
| 5 | Read `test-data/outputs/prompt_comparison.md` and a few v1/v2/v3 output files. Write 2–4 sentences of observations in `docs/report_template.md` (Section 3.2) | | [ ] |
| 6 | If some tests fail, **keep them as Fail**. The guidelines say an honest table with failures scores better than all passes. Optionally improve the prompt as v4, re-run, and add it to the log (then Q18 = 4) | | [ ] |
| 7 | Mark each module in Section 3.1 as Working / Partly working / Not started, based on the results | | [ ] |
| 8 | Create a **public** GitHub repository and push this folder. Check the repository contains no API key; a visible key means 0 for the repository part | | [ ] |
| 9 | Deploy on share.streamlit.io: main file `code/application/app.py`, under Advanced settings → Secrets add `GEMINI_API_KEY = "…"`. Open the app link in incognito | | [ ] |
| 10 | Take 2–3 screenshots of **real runs** of the deployed app: T01 plan, T09 rejected, T12 regenerated. Add them to Section 4.2 (see below), plus 1 screenshot of the repository for Section 5 | | [ ] |
| 11 | Record the reel (script below), upload it to Drive or YouTube (unlisted), set it to "Anyone with the link can view", and note its **exact length in seconds** | | [ ] |
| 12 | Replace every `[FILL]` in `docs/report_template.md`, `README.md` and `CHANGELOG.md`. Run `python docs/build_report.py` until it prints "No placeholders left." | | [ ] |
| 13 | Commit and push again so the repository has the final PDFs, outputs and dated commits | | [ ] |
| 14 | Check both PDFs are under 10 MB. All three members confirm the contribution table, then Ronit submits the form | | [ ] |

**Adding screenshots:** save them in `docs/screenshots/`, for example `t01.png`. In `docs/report_template.md`, replace the matching `[FILL: insert screenshot …]` line with `![Test T01](screenshots/t01.png)`. Keep the caption line under it, since every screenshot must be captioned with its test number.

## Reel script (target about 120 s; must be 90–150 s; it must show a real run, not slides)

| Part (guideline time) | Screen | Voice-over / captions |
|---|---|---|
| 1. Problem (~10 s) | App home page | "Students with several exams struggle to split limited time across subjects. Generic AI chats ignore their real hours and exam dates. StudyFlow builds a realistic plan and checks it." |
| 2. Prompt experiment (~35 s) | Sidebar → Prompt version **v1** → Generate; then **Final** → Generate on the same input. Tick "Show the prompt sent to the model" | "Our first prompt had only subject names. Its plan ignored the real dates and hours. The final prompt gives Gemini a computed calendar, hard rules and a JSON format. Now every constraint is checked: zero violations." |
| 3. Working demo (~50 s) | Enter T01's subjects → Generate → show the summary, the constraint-check panel, the hours chart and one day. Change one exam date to a past date → show the error. Restore it, block Sunday 29 Nov → Regenerate | Narrate what is on screen. |
| 4. Progress and next steps (~20 s) | GitHub repository / test table | "We built 8 modules, saved 3 prompt versions and ran 12 tests: [x] passed. In Milestone 3 we will add automatic repair of violations, calendar export and saved plans." |

## Microsoft Form answers

Every number must match the PDF.

| Q | Answer |
|---|---|
| 1 Team ID | PE-B13-15 |
| 2 Team name | CodeHead |
| 3 Project title | Timetable and Study Plan Generator (same as the cover page) |
| 4–5 Leader name, enrollment | Ronit Agrawal, S24CSEU1323 |
| 6 Group (batch) | B13-24 |
| 7 All enrollment numbers (one per line) | S24CSEU1323 / [FILL Vansh] / [FILL Mehul] |
| 8 Project type (max 2) | [FILL: choose from the form's options, e.g. the web-app / LLM-application ones] |
| 9 Main AI tool and model | Gemini 2.5 Flash via the Gemini API (Google AI Studio key), in a Streamlit web app |
| 10 Number of prompts | **2** (prompt sheets P1 and P2 in Section 2.3) |
| 11 Prototype link | [FILL streamlit.app link] |
| 12 Repository link | [FILL github link] |
| 13 Reel link | [FILL] |
| 14 Reel length | [FILL exact seconds, 90–150] |
| 15 Supporting document type | Technical report |
| 16 Upload | `docs/CodeHead_TechnicalReport.pdf` |
| 17 Number of test inputs | **12** (rows in the Section 4.1 table) |
| 18 Number of prompt versions | **3** (v1, v2, v3 in the Section 3.2 log; 4 if you add a v4) |
| 19 Prototype status | "All modules working" **only** if every row in Section 3.1 says Working; otherwise "Some modules working" |
| 20 Working modules | Only the rows marked Working, one per line, using the exact names: Student Input Module · Input Validation Module · Prompt Engineering Module · AI Study Plan Generator · Constraint Checker · Timetable Display Module · Revision and Break Management · Regeneration Module |
| 21 Upload Milestone 2 PDF | `docs/M2_PE-B13-15_TimetableAndStudyPlanGenerator.pdf` |
| 22 Main task per member | `S24CSEU1323 – Ronit Agrawal – [task]` and one line for each other member (must match Section 7) |
| 23 For the evaluator | "No login needed. Enter subjects and exam dates and click Generate. Use the sidebar to compare prompt versions v1/v2/final. The app uses the Gemini free tier; if you see a rate-limit error, wait one minute and retry." |
| 24 Confirmation | Tick only after all three members agree to Section 7 |
