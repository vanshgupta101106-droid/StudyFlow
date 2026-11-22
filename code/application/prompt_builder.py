"""Prompt Engineering Module: loads saved prompt files from /prompts and fills their variables.

Each prompt is ONE .txt file:
    key: value lines (id, name, step, temperature, output, examples, notes)
    === SYSTEM PROMPT ===
    ...
    === USER PROMPT TEMPLATE ===
    ... with variables in curly brackets, e.g. {start_date}
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"

# Keys the app uses -> file under /prompts
PROMPTS = {
    "v1": "v1/P1_v1.txt",
    "v2": "v2/P1_v2.txt",
    "v3": "v3/P1_v3.txt",
    "P1": "final/P1_generate.txt",
    "P2": "final/P2_regenerate.txt",
}

_VAR = re.compile(r"\{(\w+)\}")  # JSON examples like {"date": ...} never match (quotes)
SYSTEM_MARK = "=== SYSTEM PROMPT ==="
USER_MARK = "=== USER PROMPT TEMPLATE ==="


@dataclass
class Prompt:
    key: str
    system: str
    user_template: str
    meta: dict

    @property
    def json_output(self) -> bool:
        return self.meta.get("output") == "json"

    @property
    def temperature(self) -> float:
        return float(self.meta.get("temperature", 0.3))

    @property
    def variables(self) -> list[str]:
        return sorted(set(_VAR.findall(self.user_template)))

    def render(self, values: dict) -> str:
        missing = [v for v in self.variables if v not in values]
        if missing:
            raise KeyError(f"Prompt {self.key} is missing variables: {', '.join(missing)}")
        return _VAR.sub(lambda m: str(values[m.group(1)]), self.user_template)


def parse_prompt_file(text: str) -> tuple[dict, str, str]:
    header, rest = text.split(SYSTEM_MARK, 1)
    system, user = rest.split(USER_MARK, 1)
    meta = {}
    for line in header.strip().splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    system = system.strip()
    return meta, ("" if system.lower() == "none" else system), user.strip()


def load_prompt(key: str) -> Prompt:
    meta, system, user = parse_prompt_file((PROMPTS_DIR / PROMPTS[key]).read_text(encoding="utf-8"))
    return Prompt(key=key, system=system, user_template=user, meta=meta)
