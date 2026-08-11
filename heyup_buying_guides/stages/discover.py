from __future__ import annotations

from typing import Dict, List

from ..config import SourceConfig


def discover_sources(sources: List[SourceConfig]) -> List[Dict[str, str]]:
    discovered = []
    for source in sources:
        if not source.enabled or not source.seed_url:
            continue
        discovered.append(
            {
                "url": source.seed_url,
                "domain": source.domain,
                "source_role": source.source_role,
                "title": source.title or source.domain,
            }
        )
    return discovered
