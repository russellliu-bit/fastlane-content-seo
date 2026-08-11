from __future__ import annotations

import json
from typing import Optional
from urllib.parse import urlparse

from .cache import FileCache
from .config import WorkflowConfig
from typing import List

from .brand_registry import find_brand_record
from .discovery.serper import SerperClient
from .intelligence import extract_url_facts
from .schemas import CandidateProduct


def resolve_brand_origins(candidates: List[CandidateProduct], config: Optional[WorkflowConfig] = None) -> List[CandidateProduct]:
    resolved = []
    serper = SerperClient(config.serper_api_key) if config and config.serper_api_key else None
    cache = FileCache(config.cache_root, config.llm_cache_enabled) if config else None
    remaining_budget = config.origin_url_context_budget if config else 0
    for candidate in candidates:
        brand_record = find_brand_record(candidate.brand) or find_brand_record(candidate.display_name)
        if not candidate.brand_origin_url and brand_record:
            candidate.brand = brand_record.canonical_name
            candidate.brand_origin_url = brand_record.official_website
            if brand_record.official_website not in candidate.origin_urls:
                candidate.origin_urls.append(brand_record.official_website)
            if not candidate.specs:
                candidate.specs = {"official_domain": brand_record.domain}
            candidate.positioning = (
                f"{candidate.display_name} is mapped to the official {candidate.brand} website "
                f"for primary-source verification."
            )
        if candidate.brand_origin_url and serper:
            specific_url = _find_official_product_url(candidate, serper, config, cache)
            if specific_url:
                candidate.brand_origin_url = specific_url
                candidate.origin_urls = [specific_url]
                if config and remaining_budget > 0:
                    fact_result = extract_url_facts(specific_url, candidate.display_name, candidate.brand, candidate.category, config)
                    remaining_budget -= 1
                    if fact_result.supports_candidate:
                        candidate.source_confidence = max(candidate.source_confidence, fact_result.confidence or 0.85)
                        candidate.confidence_score = max(candidate.confidence_score, fact_result.confidence or 0.85)
                        if fact_result.evidence_snippets:
                            candidate.pros_evidence = (candidate.pros_evidence + fact_result.evidence_snippets[:2])[:3]
                        if fact_result.limitations:
                            candidate.cons_evidence = (candidate.cons_evidence + fact_result.limitations[:2])[:3]
                        if fact_result.key_facts:
                            candidate.specs = _merge_fact_specs(candidate.specs, fact_result.key_facts)
        if candidate.brand_origin_url:
            candidate.origin_urls = [candidate.brand_origin_url]
            candidate.source_confidence = max(candidate.source_confidence, 0.8)
            candidate.confidence_score = max(candidate.confidence_score, 0.8)
            candidate.eligibility_status = "ready"
        else:
            candidate.eligibility_status = "needs_origin"
        resolved.append(candidate)
    return resolved


def _find_official_product_url(
    candidate: CandidateProduct,
    serper: SerperClient,
    config: Optional[WorkflowConfig],
    cache: Optional[FileCache],
) -> str:
    current = candidate.brand_origin_url or ""
    domain = urlparse(current).netloc.lower()
    if domain and urlparse(current).path.strip("/"):
        return current
    if not domain:
        return current
    query = f'site:{domain} "{candidate.display_name}"'
    cache_key = cache.make_key("origin_serper", domain, candidate.display_name) if cache else ""
    try:
        organic = cache.get("origin_serper", cache_key) if cache else None
        if organic is None:
            organic = serper.search(query, num=max(1, config.origin_candidate_url_limit if config else 2))
            if cache:
                cache.set("origin_serper", cache_key, organic)
    except Exception:
        return current
    checked = 0
    for item in organic:
        if config and checked >= config.origin_candidate_url_limit:
            break
        link = item.get("link") or ""
        if not link:
            continue
        parsed = urlparse(link)
        if parsed.netloc.lower() != domain:
            continue
        checked += 1
        path = parsed.path.lower()
        if any(token in path for token in ("product", "products", "shop", "buy", "headphones", "earbuds", "audio", "support")):
            return link
    return current


def _merge_fact_specs(existing: dict, facts: List[str]) -> dict:
    merged = dict(existing)
    for index, fact in enumerate(facts[:3], start=1):
        merged.setdefault(f"fact_{index}", fact)
    return merged
