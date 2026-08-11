from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List
from urllib.parse import urlparse

from .cache import FileCache
from .config import WorkflowConfig
from .llm import GeminiLLMClient, OpenAICompatibleLLMClient, StubLLMClient, build_llm_client
from .schemas import SourceDocument


@dataclass
class CandidateDecision:
    page_type: str
    keep_candidates: List[str]
    reject_candidates: List[str]
    reasoning: str


@dataclass
class UrlFactResult:
    retrieved_url: str
    page_type: str
    supports_candidate: bool
    extracted_product_name: str
    key_facts: List[str]
    limitations: List[str]
    evidence_snippets: List[str]
    confidence: float


def judge_document_candidates(
    document: SourceDocument,
    candidate_names: List[str],
    category: str,
    config: WorkflowConfig,
) -> CandidateDecision:
    if not candidate_names:
        return CandidateDecision(page_type="unknown", keep_candidates=[], reject_candidates=[], reasoning="No candidate names to judge.")

    page_type = _heuristic_page_type(document)
    heuristic_keep = _heuristic_keep_candidates(candidate_names)
    heuristic_reject = [name for name in candidate_names if name not in heuristic_keep]

    if config.llm_mode == "stub":
        return CandidateDecision(page_type=page_type, keep_candidates=heuristic_keep, reject_candidates=heuristic_reject, reasoning="Stub mode used heuristic candidate filtering.")

    cache = FileCache(config.cache_root, config.llm_cache_enabled)
    cache_key = cache.make_key("candidate_decision", document.url, document.title, category, json.dumps(candidate_names, ensure_ascii=True), document.raw_text[:2500])
    cached = cache.get("candidate_judgments", cache_key)
    if cached:
        return CandidateDecision(
            page_type=cached.get("page_type", page_type),
            keep_candidates=list(cached.get("keep_candidates", heuristic_keep)),
            reject_candidates=list(cached.get("reject_candidates", heuristic_reject)),
            reasoning=cached.get("reasoning", "Loaded from cache."),
        )

    client = build_llm_client(config)
    if isinstance(client, StubLLMClient):
        return CandidateDecision(page_type=page_type, keep_candidates=heuristic_keep, reject_candidates=heuristic_reject, reasoning="Stub LLM used heuristic candidate filtering.")

    schema = {
        "type": "object",
        "properties": {
            "page_type": {"type": "string"},
            "keep_candidates": {"type": "array", "items": {"type": "string"}},
            "reject_candidates": {"type": "array", "items": {"type": "string"}},
            "reasoning": {"type": "string"},
        },
        "required": ["page_type", "keep_candidates", "reject_candidates", "reasoning"],
    }
    prompt = (
        "You are validating whether candidate names extracted from a web page are real consumer-tech products worth keeping for a buying guide workflow.\n"
        "Return JSON only.\n"
        "Rules:\n"
        "- Favor keeping real product names, brand + model names, and product-family names.\n"
        "- Reject site labels, navigation labels, category names, review-platform names, blog labels, and marketing phrases.\n"
        "- page_type must be one of: product_page, comparison_page, listicle_page, brand_homepage, category_hub, generic_homepage, irrelevant.\n\n"
        f"Category: {category}\n"
        f"URL: {document.url}\n"
        f"Title: {document.title}\n"
        f"Source role: {document.source_role}\n"
        f"Candidate names: {json.dumps(candidate_names, ensure_ascii=True)}\n"
        f"Text excerpt: {document.raw_text[:3000]}\n"
    )
    payload = _generate_json(client, prompt, schema)
    keep = [item for item in payload.get("keep_candidates", []) if item in candidate_names]
    if not keep:
        keep = heuristic_keep
    reject = [item for item in candidate_names if item not in keep]
    result = CandidateDecision(
        page_type=payload.get("page_type", page_type),
        keep_candidates=keep,
        reject_candidates=reject,
        reasoning=payload.get("reasoning", "LLM filtered candidate names."),
    )
    cache.set(
        "candidate_judgments",
        cache_key,
        {
            "page_type": result.page_type,
            "keep_candidates": result.keep_candidates,
            "reject_candidates": result.reject_candidates,
            "reasoning": result.reasoning,
        },
    )
    return result


def extract_url_facts(
    url: str,
    product_name: str,
    brand: str,
    category: str,
    config: WorkflowConfig,
) -> UrlFactResult:
    fallback = UrlFactResult(
        retrieved_url=url,
        page_type="unknown",
        supports_candidate=False,
        extracted_product_name="",
        key_facts=[],
        limitations=[],
        evidence_snippets=[],
        confidence=0.0,
    )
    if config.llm_mode == "stub" or config.llm_provider != "gemini":
        return fallback

    cache = FileCache(config.cache_root, config.llm_cache_enabled)
    cache_key = cache.make_key("url_facts", url, product_name, brand, category, config.llm_model)
    cached = cache.get("url_facts", cache_key)
    if cached:
        return UrlFactResult(
            retrieved_url=cached.get("retrieved_url", url),
            page_type=cached.get("page_type", "unknown"),
            supports_candidate=bool(cached.get("supports_candidate")),
            extracted_product_name=cached.get("extracted_product_name", ""),
            key_facts=list(cached.get("key_facts", [])),
            limitations=list(cached.get("limitations", [])),
            evidence_snippets=list(cached.get("evidence_snippets", [])),
            confidence=float(cached.get("confidence", 0.0) or 0.0),
        )

    client = build_llm_client(config)
    if not isinstance(client, GeminiLLMClient):
        return fallback

    schema = {
        "type": "object",
        "properties": {
            "retrieved_url": {"type": "string"},
            "page_type": {"type": "string"},
            "supports_candidate": {"type": "boolean"},
            "extracted_product_name": {"type": "string"},
            "key_facts": {"type": "array", "items": {"type": "string"}},
            "limitations": {"type": "array", "items": {"type": "string"}},
            "evidence_snippets": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"},
        },
        "required": [
            "retrieved_url",
            "page_type",
            "supports_candidate",
            "extracted_product_name",
            "key_facts",
            "limitations",
            "evidence_snippets",
            "confidence",
        ],
    }
    prompt = (
        "Use URL context to inspect the provided page and determine whether it is an official or credible page for the target product.\n"
        "Return JSON only.\n"
        "Rules:\n"
        "- Prefer extracting facts exactly from the page.\n"
        "- If the page does not clearly support the candidate, set supports_candidate to false.\n"
        "- page_type must be one of: product_page, category_page, support_page, brand_homepage, comparison_page, review_page, unknown.\n"
        "- evidence_snippets should quote or closely summarize short factual statements from the page.\n\n"
        f"Target category: {category}\n"
        f"Target brand: {brand}\n"
        f"Target product: {product_name}\n"
        f"Target URL: {url}\n"
    )
    payload = client.generate_json_object(
        prompt=prompt,
        response_schema=schema,
        tools=[{"url_context": {}}],
    )
    confidence = payload.get("confidence", 0.0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    result = UrlFactResult(
        retrieved_url=payload.get("retrieved_url", url),
        page_type=payload.get("page_type", "unknown"),
        supports_candidate=bool(payload.get("supports_candidate")),
        extracted_product_name=payload.get("extracted_product_name", ""),
        key_facts=list(payload.get("key_facts", [])),
        limitations=list(payload.get("limitations", [])),
        evidence_snippets=list(payload.get("evidence_snippets", [])),
        confidence=confidence,
    )
    cache.set(
        "url_facts",
        cache_key,
        {
            "retrieved_url": result.retrieved_url,
            "page_type": result.page_type,
            "supports_candidate": result.supports_candidate,
            "extracted_product_name": result.extracted_product_name,
            "key_facts": result.key_facts,
            "limitations": result.limitations,
            "evidence_snippets": result.evidence_snippets,
            "confidence": result.confidence,
        },
    )
    return result


def _heuristic_page_type(document: SourceDocument) -> str:
    lowered = f"{document.title} {document.url}".lower()
    path = urlparse(document.url).path.strip("/")
    if not path:
        return "generic_homepage"
    if any(token in lowered for token in ("comparison", "vs", "best ", "top ", "review")):
        return "comparison_page"
    if any(token in lowered for token in ("category", "shop/", "headphones", "earbuds", "audio")):
        return "category_hub"
    return "unknown"


def _heuristic_keep_candidates(candidate_names: List[str]) -> List[str]:
    bad_tokens = (
        "review",
        "shopping blog",
        "deals",
        "buying guide",
        "categories",
        "platform",
        "homepage",
    )
    kept = []
    for name in candidate_names:
        lowered = name.lower()
        if any(token in lowered for token in bad_tokens):
            continue
        kept.append(name)
    return kept


def _generate_json(client: Any, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(client, GeminiLLMClient):
        return client.generate_json_object(prompt=prompt, response_schema=schema)
    if isinstance(client, OpenAICompatibleLLMClient):
        return client.generate_json_object(prompt=prompt, response_schema=schema)
    return {}
