from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from .utils import ensure_dir, write_json


class FileCache:
    def __init__(self, root: Path, enabled: bool = True) -> None:
        self.root = ensure_dir(root)
        self.enabled = enabled

    def get(self, namespace: str, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        path = self._path(namespace, key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError:
            return None

    def set(self, namespace: str, key: str, value: Any) -> None:
        if not self.enabled:
            return
        path = self._path(namespace, key)
        write_json(path, value)

    def make_key(self, *parts: Any) -> str:
        joined = "||".join("" if item is None else str(item) for item in parts)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    def _path(self, namespace: str, key: str) -> Path:
        return ensure_dir(self.root / namespace) / f"{key}.json"
