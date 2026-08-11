from __future__ import annotations

from typing import List

from ..schemas import CandidateProduct


def score_and_select(candidates: List[CandidateProduct], max_products: int) -> List[CandidateProduct]:
    ranked = sorted(
        candidates,
        key=lambda item: (
            round(item.confidence_score, 3),
            len(item.origin_urls),
            len(item.source_urls),
            len(item.specs),
        ),
        reverse=True,
    )
    return ranked[:max_products]
