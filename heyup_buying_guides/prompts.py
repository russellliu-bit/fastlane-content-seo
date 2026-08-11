from __future__ import annotations

from pathlib import Path
from typing import Dict


PROMPT_DIR = Path(__file__).resolve().parent / "prompt_templates"


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text()


def render_prompt(name: str, values: Dict[str, str]) -> str:
    template = load_prompt(name)
    return template.format(**values)
