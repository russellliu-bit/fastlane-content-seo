from __future__ import annotations

from pathlib import Path
from typing import Any

from .utils import ensure_dir, write_json


class ArtifactStore:
    def __init__(self, root: Path, run_id: str) -> None:
        self.run_dir = ensure_dir(root / run_id)
        self.paths = []

    def write_json(self, filename: str, payload: Any) -> Path:
        path = self.run_dir / filename
        write_json(path, payload)
        self.paths.append(str(path))
        return path

    def write_text(self, filename: str, content: str) -> Path:
        path = self.run_dir / filename
        path.write_text(content)
        self.paths.append(str(path))
        return path
