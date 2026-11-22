# StudyFlow – Timetable and Study Plan Generator

**SCSE4041 Prompt Engineering Mini Project · Team CodeHead (PE-B13-15) · Problem C20**

StudyFlow turns a student's subjects, exam dates, difficulty levels and free hours into a realistic, day-wise study timetable. It uses Google Gemini, and every generated plan is **checked automatically** against the student's constraints: daily hour limits, no study on or after a subject's exam, no overlapping sessions, and a revision session for every subject.

- **Live app:** [FILL https://….streamlit.app]
- **Demo reel:** [FILL link]

## How it works

```
inputs -> validation -> planning context (calendar + target hours) -> prompt P1 -> Gemini (JSON) -> constraint checker -> timetable
                                                                         ^
                       change request + previous plan -> prompt P2 ------+   (regeneration)
```

Date arithmetic and hour budgeting are done in code and passed to the model as tables. The LLM only does the scheduling, so the output stays consistent and can be checked. The diagrams are in [`docs/diagrams/`](docs/diagrams).

## Repository structure

| Path | Contents |
|---|---|
| `prompts/v1`, `v2`, `v3` | The three saved versions of prompt P1, one `.txt` file each (settings, system prompt, user template) |
| `prompts/final/` | Final prompts used by the app, one file per prompt: `P1_generate.txt` (= v3) and `P2_regenerate.txt` |
| `code/application/` | Streamlit app and modules: `validation`, `planner`, `prompt_builder`, `llm`, `checker`, `pipeline`, `app` |
| `code/application/tests/` | Offline unit tests (no API key needed) |
| `code/notebooks/run_experiments.py` | Runs all test cases and the v1/v2/v3 comparison, and saves the outputs |
| `test-data/inputs/` | 12 test cases (T01–T12: normal, edge and invalid) |
| `test-data/outputs/` | Saved model outputs, `results_table.md`, `prompt_comparison.md` |
| `docs/` | Diagrams, report templates, `build_report.py`, final PDFs |
| `CHANGELOG.md` | Dated progress log |

## Run locally

```bash
pip install -r requirements.txt
# get a free key at https://aistudio.google.com/apikey
copy .streamlit\secrets.toml.example .streamlit\secrets.toml   # then paste your key into it
streamlit run code/application/app.py
```

The app also asks for the key in its sidebar if no secret is set.

## Tests and experiments

```bash
pip install pytest
python -m pytest code/application/tests          # offline unit tests

set GEMINI_API_KEY=your-key                      # PowerShell: $env:GEMINI_API_KEY="your-key"
python code/notebooks/run_experiments.py         # 12 tests + prompt comparison (about 5 minutes on the free tier)
```

## Build the report PDFs

```bash
pip install markdown
python docs/build_report.py
```

This fills `docs/report_template.md` and `docs/technical_report_template.md` with the prompt files and the saved results, then prints both PDFs with Chrome or Edge.

## Deploy on Streamlit Community Cloud

1. Push this folder to a **public** GitHub repository.
2. Go to share.streamlit.io, choose **Create app**, select the repository and set the main file to `code/application/app.py`.
3. Under **Advanced settings → Secrets**, paste `GEMINI_API_KEY = "your-key"`.
4. Deploy, then open the link in an incognito window to confirm it works without logging in.

> Never commit `.streamlit/secrets.toml` or any API key. It is already listed in `.gitignore`.

## Team

| Member | Role |
|---|---|
| Ronit Agrawal (leader), S24CSEU1323 | Prompt design (P1, P2), prompt builder, pipeline, report |
| Vansh Gupta, S24CSEU1338 | Validation, planner, constraint checker, tests |
| Mehul Choubey, S24CSEU1324 | Streamlit UI, Gemini client, deployment, diagrams, technical report, reel |
