from __future__ import annotations

from typing import List

from .schemas import CandidateProduct


def bind_candidate_evidence(candidates: List[CandidateProduct]) -> List[CandidateProduct]:
    for candidate in candidates:
        bindings = []
        evidence_id = 1
        for entry in candidate.pros_evidence[:2]:
            bindings.append({"evidence_id": f"{candidate.dedupe_key}-pro-{evidence_id}", "type": "pro", "text": entry})
            evidence_id += 1
        for entry in candidate.cons_evidence[:2]:
            bindings.append({"evidence_id": f"{candidate.dedupe_key}-con-{evidence_id}", "type": "con", "text": entry})
            evidence_id += 1
        if not bindings and candidate.positioning:
            bindings.append(
                {
                    "evidence_id": f"{candidate.dedupe_key}-source-{evidence_id}",
                    "type": "source_summary",
                    "text": candidate.positioning,
                }
            )
            evidence_id += 1
        if len(bindings) < 2 and candidate.origin_urls:
            bindings.append(
                {
                    "evidence_id": f"{candidate.dedupe_key}-origin-{evidence_id}",
                    "type": "origin_url",
                    "text": f"Primary source URL: {candidate.origin_urls[0]}",
                }
            )
            evidence_id += 1
        if len(bindings) < 2 and candidate.source_urls:
            bindings.append(
                {
                    "evidence_id": f"{candidate.dedupe_key}-reference-{evidence_id}",
                    "type": "reference_url",
                    "text": f"Reference source URL: {candidate.source_urls[0]}",
                }
            )
        candidate.evidence_bindings = bindings
    return candidates
