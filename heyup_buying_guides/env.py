from __future__ import annotations

import os
from pathlib import Path
from typing import Dict


def load_dotenv(path: Path) -> Dict[str, str]:
    loaded: Dict[str, str] = {}
    if not path.exists():
        return loaded
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        loaded[key] = value
        os.environ.setdefault(key, value)
    return loaded
