from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SourceDocument:
    url: str
    domain: str
    title: str
    published_at: str
    content_type: str
    raw_text: str
    outbound_links: List[str]
    evidence_snippets: List[str]
    fetch_status: str
    source_role: str = "reference_site"
    trust_level: float = 0.5
    evidence_map: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CandidateProduct:
    normalized_name: str
    display_name: str
    brand: str
    category: str
    source_urls: List[str]
    origin_urls: List[str]
    specs: Dict[str, str]
    positioning: str
    pros_evidence: List[str]
    cons_evidence: List[str]
    best_for_signals: List[str]
    confidence_score: float
    dedupe_key: str
    brand_origin_url: Optional[str] = None
    evidence_bindings: List[Dict[str, Any]] = field(default_factory=list)
    eligibility_status: str = "unknown"
    source_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DiscoverySignal:
    source: str
    query: str
    topic_key: str
    signal_type: str
    score: float
    evidence: Dict[str, Any]
    observed_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TopicCandidate:
    topic_key: str
    category: str
    intent_type: str
    article_type: str
    keyword: str
    title_hypotheses: List[str]
    signal_summary: str
    signal_scores: Dict[str, float]
    candidate_products: List[CandidateProduct]
    source_urls: List[str]
    brand_origin_coverage: float
    draftability_score: float
    risk_flags: List[str]
    status: str
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["candidate_products"] = [item.to_dict() for item in self.candidate_products]
        return payload


@dataclass
class ArticleBrief:
    topic_key: str
    article_type: str
    category: str
    keyword: str
    angle: str
    title_candidates: List[str]
    comparison_period: str
    selected_products: List[CandidateProduct]
    must_have_sections: List[str]
    disclosure_required: bool
    affiliate_mode: str

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["selected_products"] = [item.to_dict() for item in self.selected_products]
        return payload


@dataclass
class GeneratedArticle:
    topic_key: str
    article_type: str
    title: str
    slug: str
    excerpt: str
    seo_title: str
    seo_description: str
    intro: str
    sections: List[Dict[str, Any]]
    products: List[Dict[str, Any]]
    faq: List[Dict[str, str]]
    disclosure: str
    affiliate_slots: List[Dict[str, str]]
    source_manifest: List[Dict[str, Any]]
    risk_flags: List[str] = field(default_factory=list)
    claim_references: List[Dict[str, Any]] = field(default_factory=list)
    rank_rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RunReport:
    run_id: str
    started_at: str
    source_pages_count: int
    candidate_count: int
    selected_count: int
    article_type: str
    article_title: str
    validation_status: str
    shopify_status: str
    shopify_article_id: Optional[str]
    topic_key: str = ""
    topic_scores: Dict[str, float] = field(default_factory=dict)
    quality_score: float = 0.0
    blocking_reasons: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    artifact_paths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
