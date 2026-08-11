from __future__ import annotations

import re
from typing import Dict, List, Optional

from ..brand_registry import find_brand_record, known_brand_names
from ..config import WorkflowConfig
from ..intelligence import judge_document_candidates
from ..schemas import CandidateProduct, SourceDocument
from ..utils import slugify


PRODUCT_RE = re.compile(r"\b([A-Z][A-Za-z0-9]+(?:\s+[A-Z0-9][A-Za-z0-9()+-]+){0,4})\b")
MODEL_TOKEN_RE = re.compile(r"(\d|[A-Z]{2,}|-|(?:pro|max|ultra|plus|mini|buds|earbuds|headphones|tablet|watch|ring|gen)\b)", re.I)
GENERIC_NAME_PATTERNS = (
    "expert reviews",
    "shopping blog",
    "today's deals",
    "todays deals",
    "deals america",
    "top review platform",
    "product reviews",
    "shopping categories",
    "buying guide",
)


def extract_candidates(documents: List[SourceDocument], target_category: str, config: Optional[WorkflowConfig] = None) -> List[CandidateProduct]:
    candidates: List[CandidateProduct] = []
    for document in documents:
        if document.fetch_status != "success":
            continue
        if _should_skip_document(document):
            continue
        names = _extract_product_names(document.raw_text)
        if config:
            decision = judge_document_candidates(document, names, target_category, config)
            names = decision.keep_candidates
        for name in names:
            brand_record = find_brand_record(name) or find_brand_record(name.split()[0])
            brand = brand_record.canonical_name if brand_record else name.split()[0]
            lower = document.raw_text.lower()
            pros = []
            cons = []
            if "battery" in lower:
                pros.append("Battery life is discussed in the source coverage.")
            if "noise cancellation" in lower or "noise canceling" in lower:
                pros.append("Noise cancellation is explicitly mentioned in the source coverage.")
            if "expensive" in lower or "premium" in lower:
                cons.append("Pricing may sit at the premium end of the category.")
            if "availability" in lower:
                cons.append("Availability may vary by region and channel.")
            candidates.append(
                CandidateProduct(
                    normalized_name=name.lower(),
                    display_name=name,
                    brand=brand,
                    category=target_category,
                    source_urls=[document.url],
                    origin_urls=[brand_record.official_website] if brand_record else [],
                    specs=_extract_specs(document.raw_text),
                    positioning=_build_positioning(name, target_category),
                    pros_evidence=pros or document.evidence_snippets[:1],
                    cons_evidence=cons or document.evidence_snippets[1:2],
                    best_for_signals=[f"{target_category.lower()} buyers who want a focused shortlist"],
                    confidence_score=0.6 if brand_record else 0.4,
                    dedupe_key=slugify(name),
                    brand_origin_url=brand_record.official_website if brand_record else None,
                    source_confidence=0.7 if brand_record else 0.0,
                )
            )
    return candidates


def _extract_product_names(text: str) -> List[str]:
    brands = known_brand_names()
    seen = set()
    names = []
    for brand in brands:
        pattern = re.compile(rf"\b({re.escape(brand)}(?:\s+[A-Za-z0-9][A-Za-z0-9()+-]{{1,20}}){{0,4}})\b")
        for match in pattern.findall(text):
            cleaned = _normalize_candidate_name(match)
            if _is_valid_product_name(cleaned, brand) and cleaned not in seen:
                seen.add(cleaned)
                names.append(cleaned)

    for match in PRODUCT_RE.findall(text):
        cleaned = _normalize_candidate_name(match)
        if not _is_valid_product_name(cleaned):
            continue
        if cleaned in seen:
            continue
        seen.add(cleaned)
        names.append(cleaned)
    return names[:10]


def _should_skip_document(document: SourceDocument) -> bool:
    if document.source_role != "reference_site":
        return False
    normalized_url = document.url.rstrip("/")
    path = normalized_url.split("://", 1)[-1].split("/", 1)
    if len(path) == 1:
        return True
    trailing_path = path[1].strip().lower()
    if trailing_path in {"", "home", "homepage"}:
        return True
    return False


def _normalize_candidate_name(value: str) -> str:
    return " ".join(value.strip().split())


def _is_valid_product_name(value: str, brand_hint: str = "") -> bool:
    lowered = value.lower()
    if len(value.split()) < 2:
        return False
    if any(pattern in lowered for pattern in GENERIC_NAME_PATTERNS):
        return False
    if lowered.startswith(("how to", "best products", "top products", "buying guide")):
        return False
    if not MODEL_TOKEN_RE.search(value):
        return False
    if brand_hint and normalize_space(brand_hint.lower()) not in normalize_space(lowered):
        return False
    return True


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def _extract_specs(text: str) -> Dict[str, str]:
    specs: Dict[str, str] = {}
    lower = text.lower()
    if "bluetooth" in lower:
        specs["connectivity"] = "Bluetooth"
    if "usb-c" in lower:
        specs["port"] = "USB-C"
    if "wireless" in lower:
        specs["type"] = "Wireless"
    return specs


def _build_positioning(name: str, category: str) -> str:
    return f"{name} stands out in the {category.lower()} shortlist because source coverage surfaces a clear use case and enough evidence to justify inclusion."
