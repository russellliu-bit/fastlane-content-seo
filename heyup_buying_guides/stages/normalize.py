from __future__ import annotations

from typing import Dict, List

from ..schemas import CandidateProduct


def normalize_and_dedupe(candidates: List[CandidateProduct]) -> List[CandidateProduct]:
    grouped: Dict[str, CandidateProduct] = {}
    for candidate in candidates:
        existing = grouped.get(candidate.dedupe_key)
        if not existing:
            grouped[candidate.dedupe_key] = candidate
            continue
        existing.source_urls = sorted(set(existing.source_urls + candidate.source_urls))
        existing.origin_urls = sorted(set(existing.origin_urls + candidate.origin_urls))
        existing.pros_evidence = _merge_unique(existing.pros_evidence, candidate.pros_evidence)
        existing.cons_evidence = _merge_unique(existing.cons_evidence, candidate.cons_evidence)
        existing.best_for_signals = _merge_unique(existing.best_for_signals, candidate.best_for_signals)
        existing.specs.update(candidate.specs)
        existing.confidence_score = max(existing.confidence_score, candidate.confidence_score)
    return list(grouped.values())


def _merge_unique(left: List[str], right: List[str]) -> List[str]:
    seen = set(left)
    merged = list(left)
    for item in right:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return merged
