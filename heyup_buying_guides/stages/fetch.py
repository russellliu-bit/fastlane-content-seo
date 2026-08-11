from __future__ import annotations

import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from ..schemas import SourceDocument
from ..utils import read_json, utc_now_iso


def fetch_documents(discovered: List[Dict[str, str]], fixtures_path: Optional[Path] = None) -> List[SourceDocument]:
    if fixtures_path:
        return _load_fixture_documents(fixtures_path)

    documents = []
    for item in discovered:
        try:
            with urllib.request.urlopen(item["url"], timeout=20) as response:
                html = response.read().decode("utf-8", errors="ignore")
            text = _strip_html(html)
            documents.append(
                SourceDocument(
                    url=item["url"],
                    domain=item["domain"],
                    title=item["title"],
                    published_at=utc_now_iso(),
                    content_type="text/html",
                    raw_text=text,
                    outbound_links=[],
                    evidence_snippets=_sentence_snippets(text),
                    fetch_status="success",
                    source_role=item.get("source_role", "reference_site"),
                )
            )
        except Exception as exc:  # pragma: no cover - network path is not used in tests
            documents.append(
                SourceDocument(
                    url=item["url"],
                    domain=item["domain"],
                    title=item["title"],
                    published_at=utc_now_iso(),
                    content_type="text/html",
                    raw_text="",
                    outbound_links=[],
                    evidence_snippets=[],
                    fetch_status=f"error: {exc}",
                    source_role=item.get("source_role", "reference_site"),
                )
            )
    return documents


def _load_fixture_documents(fixtures_path: Path) -> List[SourceDocument]:
    payload = read_json(fixtures_path / "source_documents.json")
    return [SourceDocument(**item) for item in payload]


def _strip_html(html: str) -> str:
    no_script = re.sub(r"<script.*?</script>", " ", html, flags=re.S | re.I)
    no_style = re.sub(r"<style.*?</style>", " ", no_script, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", no_style)
    return " ".join(text.split())


def _sentence_snippets(text: str) -> List[str]:
    chunks = re.split(r"(?<=[.!?])\s+", text)
    return [chunk.strip() for chunk in chunks if chunk.strip()][:8]
