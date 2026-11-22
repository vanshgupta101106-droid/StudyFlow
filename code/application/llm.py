"""AI Study Plan Generator: the only place that talks to the LLM (Google Gemini)."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

DEFAULT_MODEL = "gemini-2.5-flash"


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


def generate(system: str, user: str, *, temperature: float, json_output: bool, api_key: str,
             model: str = DEFAULT_MODEL, retries: int = 3) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        temperature=temperature,
        system_instruction=system or None,
        response_mime_type="application/json" if json_output else "text/plain",
        max_output_tokens=32768,
    )
    last_error = None
    for attempt in range(retries):
        try:
            response = client.models.generate_content(model=model, contents=user, config=config)
            if not response.text:
                raise RuntimeError("Model returned an empty response.")
            return response.text
        except Exception as e:  # rate limits / transient errors
            last_error = e
            if attempt < retries - 1:
                time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")


def parse_json(text: str) -> dict:
    """Parse the model's JSON, tolerating accidental ```json fences."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    return json.loads(cleaned)
