from __future__ import annotations

from typing import Dict, List

from .brand_registry import find_brand_record
from .schemas import CandidateProduct, TopicCandidate
from .utils import slugify


def build_topic_candidates(
    category: str,
    discovered_topics: List[Dict],
    trends_score_by_keyword: Dict[str, float],
    reddit_score_by_keyword: Dict[str, float],
    max_topics: int,
    quality_threshold: float,
) -> List[TopicCandidate]:
    topics: List[TopicCandidate] = []
    for payload in discovered_topics:
        keyword = payload.get("keyword") or payload.get("query") or category.lower()
        products = [_candidate_from_payload(item, category) for item in payload.get("candidate_products", [])]
        origin_coverage = _origin_coverage(products)
        content_fit_score = _content_fit(payload.get("article_type", ""), payload.get("intent_type", ""))
        signal_scores = {
            "search_discovery_score": 0.9 if payload.get("source_urls") else 0.4,
            "trend_score": trends_score_by_keyword.get(keyword, 0.0),
            "reddit_validation_score": reddit_score_by_keyword.get(keyword, 0.0),
            "origin_evidence_score": origin_coverage,
            "content_fit_score": content_fit_score,
        }
        risk_flags = []
        if origin_coverage < 0.5:
            risk_flags.append("weak_brand_origin_coverage")
        if signal_scores["reddit_validation_score"] > 0.5 and origin_coverage < 0.5:
            risk_flags.append("reddit_hot_but_origin_weak")
        if len(products) < 3:
            risk_flags.append("insufficient_candidate_products")
        draftability = _draftability(signal_scores)
        status = "ready" if _passes_threshold(signal_scores, draftability, quality_threshold) else "blocked"
        topics.append(
            TopicCandidate(
                topic_key=slugify(payload.get("keyword", category)),
                category=category,
                intent_type=payload.get("intent_type", "comparison"),
                article_type=payload.get("article_type", "comparison_roundup"),
                keyword=keyword,
                title_hypotheses=payload.get("title_hypotheses", []),
                signal_summary=payload.get("signal_summary", ""),
                signal_scores=signal_scores,
                candidate_products=products,
                source_urls=payload.get("source_urls", []),
                brand_origin_coverage=origin_coverage,
                draftability_score=draftability,
                risk_flags=risk_flags,
                status=status,
                rationale=payload.get("rationale", ""),
            )
        )
    topics.sort(key=lambda item: item.draftability_score, reverse=True)
    return topics[:max_topics]


def _candidate_from_payload(payload: Dict, category: str) -> CandidateProduct:
    if isinstance(payload, str):
        payload = {"name": payload}
    name = payload.get("name") or payload.get("product_name") or "Unknown Product"
    brand_record = find_brand_record(payload.get("brand") or name.split()[0]) or find_brand_record(name)
    brand = brand_record.canonical_name if brand_record else (payload.get("brand") or name.split()[0])
    origin_url = payload.get("brand_origin_url") or payload.get("origin_url") or (brand_record.official_website if brand_record else None)
    source_urls = payload.get("source_urls") or ([payload.get("source_url")] if payload.get("source_url") else [])
    if isinstance(source_urls, str):
        source_urls = [source_urls]
    origin_urls = [origin_url] if origin_url else []
    confidence = 0.75 if origin_url else 0.35
    return CandidateProduct(
        normalized_name=name.lower(),
        display_name=name,
        brand=brand,
        category=category,
        source_urls=source_urls,
        origin_urls=origin_urls,
        specs=payload.get("specs", {}),
        positioning=payload.get("positioning", f"{name} is relevant for current {category.lower()} buying intent."),
        pros_evidence=payload.get("pros_evidence", []),
        cons_evidence=payload.get("cons_evidence", []),
        best_for_signals=payload.get("best_for_signals", []),
        confidence_score=confidence,
        dedupe_key=slugify(name),
        brand_origin_url=origin_url,
        evidence_bindings=payload.get("evidence_bindings", []),
        eligibility_status="ready" if origin_url else "needs_origin",
        source_confidence=confidence,
    )


def _origin_coverage(products: List[CandidateProduct]) -> float:
    if not products:
        return 0.0
    covered = sum(1 for item in products if item.brand_origin_url)
    return round(covered / len(products), 3)


def _content_fit(article_type: str, intent_type: str) -> float:
    if article_type in {"comparison_roundup", "buying_guide"}:
        return 0.9
    if intent_type in {"comparison", "guide"}:
        return 0.75
    return 0.3


def _draftability(signal_scores: Dict[str, float]) -> float:
    return round(
        (
            signal_scores["search_discovery_score"] * 0.25
            + signal_scores["trend_score"] * 0.15
            + signal_scores["reddit_validation_score"] * 0.15
            + signal_scores["origin_evidence_score"] * 0.3
            + signal_scores["content_fit_score"] * 0.15
        ),
        3,
    )


def _passes_threshold(signal_scores: Dict[str, float], draftability: float, quality_threshold: float) -> bool:
    if signal_scores["search_discovery_score"] <= 0:
        return False
    if signal_scores["origin_evidence_score"] <= 0:
        return False
    if max(signal_scores["trend_score"], signal_scores["reddit_validation_score"]) <= 0:
        return False
    return draftability >= quality_threshold
