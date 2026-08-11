from __future__ import annotations

from typing import List

from ..schemas import CandidateProduct


def enrich_candidates(candidates: List[CandidateProduct]) -> List[CandidateProduct]:
    enriched = []
    for candidate in candidates:
        origin_urls = list(candidate.origin_urls)
        primary_source = candidate.source_urls[0] if candidate.source_urls else None
        if not origin_urls and primary_source:
            origin_urls.append(primary_source)
        if not origin_urls:
            candidate.eligibility_status = "needs_origin"
            enriched.append(candidate)
            continue
        if not candidate.source_urls:
            candidate.source_urls = [origin_urls[0]]
        if not primary_source:
            primary_source = candidate.source_urls[0]
        confidence = candidate.confidence_score + 0.2
        if primary_source != origin_urls[0]:
            confidence += 0.1
        candidate.origin_urls = origin_urls
        candidate.confidence_score = min(confidence, 0.95)
        enriched.append(candidate)
    return enriched
