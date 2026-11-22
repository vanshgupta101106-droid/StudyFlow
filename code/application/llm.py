"""AI Study Plan Generator: the only place that talks to the LLM (Google Gemini)."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

DEFAULT_MODEL = "gemini-3.6-flash"


def get_api_key(secrets=None) -> str | None:
    """Read the key from Streamlit secrets (deployed) or environment variables (local)."""
    if secrets is not None:
        try:
            if "GEMINI_API_KEY" in secrets:
                return secrets["GEMINI_API_KEY"]
        except Exception:  # no secrets.toml present
            pass
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if key:
        return key
    # local fallback for scripts: the git-ignored .streamlit/secrets.toml at the repo root
    secrets_file = Path(__file__).resolve().parents[2] / ".streamlit" / "secrets.toml"
    if secrets_file.exists():
        m = re.search(r'^GEMINI_API_KEY\s*=\s*"([^"]+)"', secrets_file.read_text(encoding="utf-8"), re.M)
        if m and "paste-your-key" not in m.group(1):
            return m.group(1)
    return None


# Tried in order when the chosen model is out of free-tier quota (HTTP 429) or overloaded (HTTP 503).
# Each Gemini model has its own daily free quota, so a fallback keeps the app usable for evaluators.
FALLBACK_MODELS = ["gemini-3.5-flash-lite", "gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.8-flash"]


def _is_capacity_error(e: Exception) -> bool:
    s = str(e)
    return any(k in s for k in ("RESOURCE_EXHAUSTED", "UNAVAILABLE", "DEADLINE_EXCEEDED")) or s.startswith(("429", "503", "504"))


def generate(system: str, user: str, *, temperature: float, json_output: bool, api_key: str,
             model: str = DEFAULT_MODEL, retries: int = 3, info: dict | None = None) -> str:
    """Call Gemini and return the text. `info["model"]` is set to the model that actually answered."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=150_000))  # ms
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system or None,
        response_mime_type="application/json" if json_output else "text/plain",
        max_output_tokens=32768,
    )
    candidates = [model] + [m for m in FALLBACK_MODELS if m != model]
    last_error = None
    for current in candidates:
        for attempt in range(retries):
            try:
                response = client.models.generate_content(model=current, contents=user, config=config)
                if not response.text:
                    raise RuntimeError("Model returned an empty response.")
                if info is not None:
                    info["model"] = current
                return response.text
            except Exception as e:  # rate limits / transient errors
                last_error = e
                if "RESOURCE_EXHAUSTED" in str(e) and "PerDay" in str(e):
                    break  # daily quota used up: retrying this model is pointless
                if current != model and _is_capacity_error(e):
                    break  # busy fallback model: move on quickly instead of waiting
                if attempt < retries - 1:
                    time.sleep(5 * (attempt + 1))
        if not _is_capacity_error(last_error):
            break  # a real error (bad key, bad request): do not hide it behind other models
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")


def parse_json(text: str) -> dict:
    """Parse the model's JSON, tolerating accidental ```json fences."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(cleaned)
