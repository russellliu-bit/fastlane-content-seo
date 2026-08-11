from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import WorkflowConfig
from .schemas import ArticleBrief, GeneratedArticle
from .utils import short_excerpt, slugify


@dataclass
class StubLLMClient:
    """Deterministic generator for local development and tests."""

    def generate_article(self, brief: ArticleBrief) -> GeneratedArticle:
        if brief.article_type == "comparison_roundup":
            return _build_comparison_article(brief)
        return _build_buying_guide_article(brief)


@dataclass
class OpenAICompatibleLLMClient:
    base_url: str
    model: str
    api_key: str
    timeout_seconds: int = 60

    def generate_article(self, brief: ArticleBrief, prompt: str) -> GeneratedArticle:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate structured JSON only. "
                        "Do not wrap JSON in markdown. "
                        "All article claims must be grounded in provided evidence. "
                        "Keep the tone aligned with Heyup: friendly, transparent, community-first, practical."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_user_message(brief, prompt),
                },
            ],
        }
        raw = self._post_json("/chat/completions", payload)
        content = self._extract_content(raw)
        parsed = json.loads(content)
        article = _coerce_generated_article(parsed, brief)
        return article

    def generate_json_object(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": "Return JSON only. Follow the requested shape as closely as possible.",
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\nJSON schema hint:\n{json.dumps(response_schema, ensure_ascii=True)}",
                },
            ],
        }
        raw = self._post_json("/chat/completions", payload)
        return json.loads(self._extract_content(raw))

    def _build_user_message(self, brief: ArticleBrief, prompt: str) -> str:
        brief_payload = brief.to_dict()
        schema_hint = _json_schema_hint(brief.article_type)
        return (
            f"{prompt}\n\n"
            "Return exactly one JSON object with the required fields.\n"
            "Rules:\n"
            "- English only\n"
            "- Facts only from evidence\n"
            "- Include disclosure near the top of the article\n"
            "- Every affiliate slot must be a placeholder, not a live link\n"
            "- Do not invent rankings or specs\n"
            "- Every recommendation must include a downside\n\n"
            f"Article brief JSON:\n{json.dumps(brief_payload, ensure_ascii=True)}\n\n"
            f"Expected JSON shape:\n{schema_hint}\n"
        )

    def _post_json(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def _extract_content(self, response_payload: Dict[str, Any]) -> str:
        choices = response_payload.get("choices") or []
        if not choices:
            raise ValueError("LLM response did not contain choices.")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if item.get("type") == "text" and item.get("text"):
                    text_parts.append(item["text"])
            if text_parts:
                return "".join(text_parts)
        raise ValueError("LLM response did not contain JSON content.")


@dataclass
class GeminiLLMClient:
    base_url: str
    model: str
    api_key: str
    timeout_seconds: int = 60

    def generate_article(self, brief: ArticleBrief, prompt: str) -> GeneratedArticle:
        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You generate structured JSON only. "
                            "Do not wrap JSON in markdown. "
                            "All article claims must be grounded in provided evidence. "
                            "Keep the tone aligned with Heyup: friendly, transparent, community-first, practical."
                        )
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": self._build_user_message(brief, prompt)
                        }
                    ],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": _response_json_schema(brief.article_type),
            },
        }
        raw = self._post_json(payload)
        content = self._extract_content(raw)
        parsed = json.loads(content)
        return _coerce_generated_article(parsed, brief)

    def generate_json_object(
        self,
        prompt: str,
        response_schema: Dict[str, Any],
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "systemInstruction": {
                "parts": [
                    {
                        "text": "Return structured JSON only. Do not wrap JSON in markdown or prose."
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseJsonSchema": response_schema,
            },
        }
        if tools:
            payload["tools"] = tools
        raw = self._post_json(payload)
        content = self._extract_content(raw)
        return json.loads(content)

    def _build_user_message(self, brief: ArticleBrief, prompt: str) -> str:
        brief_payload = brief.to_dict()
        return (
            f"{prompt}\n\n"
            "Return exactly one JSON object that follows the provided schema.\n"
            "Rules:\n"
            "- English only\n"
            "- Facts only from evidence\n"
            "- Include disclosure near the top of the article\n"
            "- Every affiliate slot must be a placeholder, not a live link\n"
            "- Do not invent rankings or specs\n"
            "- Every recommendation must include a downside\n\n"
            "Section rules:\n"
            "- Use only the section types allowed by the schema\n"
            "- Do not add extra section types like text or summary unless explicitly allowed\n"
            "- Put ranked product details in products, not in sections\n"
            "- For comparison_roundup, sections must cover last_updated, how_we_picked, quick_picks_summary, and who_should_buy_what\n"
            "- For buying_guide, sections must cover last_updated, what_to_consider, how_to_compare_options, and common_mistakes\n\n"
            f"Article brief JSON:\n{json.dumps(brief_payload, ensure_ascii=True)}\n"
        )

    def _post_json(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        request = urllib.request.Request(
            url=f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def _extract_content(self, response_payload: Dict[str, Any]) -> str:
        candidates = response_payload.get("candidates") or []
        if not candidates:
            raise ValueError("Gemini response did not contain candidates.")
        content = candidates[0].get("content") or {}
        parts = content.get("parts") or []
        text_parts = [part.get("text") for part in parts if part.get("text")]
        if not text_parts:
            raise ValueError("Gemini response did not contain JSON text.")
        return "".join(text_parts)


def build_llm_client(config: WorkflowConfig) -> Any:
    if config.llm_mode == "stub":
        return StubLLMClient()
    if config.llm_provider == "openai_compatible":
        if not config.llm_model:
            raise ValueError("llm_model is required when llm_mode is not stub.")
        if not config.llm_api_key:
            raise ValueError(
                "LLM API key is required when llm_mode is not stub. "
                f"Set llm_api_key in config or export {config.llm_api_key_env}."
            )
        return OpenAICompatibleLLMClient(
            base_url=config.llm_base_url,
            model=config.llm_model,
            api_key=config.llm_api_key,
            timeout_seconds=config.llm_timeout_seconds,
        )
    if config.llm_provider == "gemini":
        if not config.llm_model:
            raise ValueError("llm_model is required when llm_mode is not stub.")
        if not config.llm_api_key:
            raise ValueError(
                "Gemini API key is required when llm_mode is not stub. "
                f"Set llm_api_key in config or export {config.llm_api_key_env}."
            )
        return GeminiLLMClient(
            base_url=config.llm_base_url,
            model=config.llm_model,
            api_key=config.llm_api_key,
            timeout_seconds=config.llm_timeout_seconds,
        )
    raise ValueError(f"Unsupported llm_provider: {config.llm_provider}")


def _build_comparison_article(brief: ArticleBrief) -> GeneratedArticle:
    title = brief.title_candidates[0]
    products = []
    affiliate_slots = []
    source_manifest = []
    quick_picks = []
    for index, product in enumerate(brief.selected_products, start=1):
        slot_id = f"affiliate-slot-{slugify(product.display_name)}"
        products.append(
            {
                "rank": index,
                "product_name": product.display_name,
                "best_for": product.best_for_signals[0] if product.best_for_signals else "buyers who want balanced value",
                "why_it_made_the_list": product.positioning,
                "pros": product.pros_evidence[:2] or ["Evidence-backed product strengths were identified from source material."],
                "cons": product.cons_evidence[:2] or ["Source coverage is limited, so buyers should verify current pricing and availability."],
                "key_specs": [f"{key}: {value}" for key, value in product.specs.items()] or ["Specs should be verified on the brand product page."],
                "evidence_summary": "; ".join((product.pros_evidence + product.cons_evidence)[:3]) or "Based on multiple source snippets.",
                "affiliate_slot": slot_id,
                "evidence_ids": [binding["evidence_id"] for binding in product.evidence_bindings],
                "source_confidence": product.source_confidence,
            }
        )
        quick_picks.append(
            {
                "product_name": product.display_name,
                "best_for": products[-1]["best_for"],
            }
        )
        affiliate_slots.append(
            {
                "slot_id": slot_id,
                "product_name": product.display_name,
                "placeholder_text": f"[Affiliate link placeholder for {product.display_name}]",
            }
        )
        source_manifest.append(
            {
                "product_name": product.display_name,
                "source_urls": product.source_urls,
                "origin_urls": product.origin_urls,
            }
        )

    sections = [
        {
            "type": "last_updated",
            "content": brief.comparison_period,
        },
        {
            "type": "how_we_picked",
            "content": "We compared evidence-backed product pages, shortlist coverage, positioning signals, and source completeness. Products with stronger original-source evidence were prioritized.",
        },
        {
            "type": "quick_picks_summary",
            "items": quick_picks,
        },
        {
            "type": "ranked_product_sections",
            "items": products,
        },
        {
            "type": "who_should_buy_what",
            "content": "Choose based on your budget, the specific use case named in each recommendation, and whether the original-source specs align with your needs.",
        },
    ]
    intro = f"These {brief.category.lower()} picks were selected from a whitelist-based research workflow. We only included claims that could be traced back to source evidence."
    excerpt = short_excerpt(intro)
    return GeneratedArticle(
        topic_key=brief.topic_key,
        article_type=brief.article_type,
        title=title,
        slug=slugify(title),
        excerpt=excerpt,
        seo_title=title,
        seo_description=short_excerpt(f"A practical comparison of {brief.category.lower()} options based on source-backed product evidence.", 150),
        intro=intro,
        sections=sections,
        products=products,
        faq=[
            {
                "question": f"How often should this {brief.category.lower()} comparison be refreshed?",
                "answer": "Refresh whenever key models, pricing, or availability change.",
                "evidence_ids": products[0].get("evidence_ids", [])[:1] if products else [],
            },
            {
                "question": "Are the buying links final?",
                "answer": "No. Affiliate links are inserted later during editorial review.",
                "evidence_ids": products[0].get("evidence_ids", [])[:1] if products else [],
            },
        ],
        disclosure="Disclosure: This article may include affiliate link placeholders that editors replace during review. Recommendations are based on source-backed research, not paid placement promises.",
        affiliate_slots=affiliate_slots,
        source_manifest=source_manifest,
        risk_flags=[],
        claim_references=_build_claim_references(products),
        rank_rationale="Products with stronger original-source evidence and more complete specs ranked higher.",
    )


def _build_buying_guide_article(brief: ArticleBrief) -> GeneratedArticle:
    title = brief.title_candidates[0]
    recommended = []
    affiliate_slots = []
    source_manifest = []
    for product in brief.selected_products:
        slot_id = f"affiliate-slot-{slugify(product.display_name)}"
        recommended.append(
            {
                "product_name": product.display_name,
                "who_it_is_for": product.best_for_signals[0] if product.best_for_signals else "buyers comparing practical day-to-day options",
                "why_consider_it": product.positioning,
                "watch_out_for": product.cons_evidence[0] if product.cons_evidence else "Check the official product page for the latest limitations and availability.",
                "affiliate_slot": slot_id,
                "evidence_ids": [binding["evidence_id"] for binding in product.evidence_bindings],
                "source_confidence": product.source_confidence,
            }
        )
        affiliate_slots.append(
            {
                "slot_id": slot_id,
                "product_name": product.display_name,
                "placeholder_text": f"[Affiliate link placeholder for {product.display_name}]",
            }
        )
        source_manifest.append(
            {
                "product_name": product.display_name,
                "source_urls": product.source_urls,
                "origin_urls": product.origin_urls,
            }
        )
    intro = f"This buying guide explains how to evaluate {brief.category.lower()} options using source-backed evidence and practical tradeoffs."
    sections = [
        {"type": "last_updated", "content": brief.comparison_period},
        {
            "type": "what_to_consider",
            "items": [
                "Match the product to the use case before comparing specs.",
                "Verify core features and compatibility on original product pages.",
                "Treat shortlist rankings as guidance, not absolute truth.",
            ],
        },
        {
            "type": "how_to_compare_options",
            "content": "Compare evidence-backed specs, use-case fit, and any tradeoffs surfaced by the source material.",
        },
        {
            "type": "common_mistakes",
            "items": [
                "Choosing based only on headline specs.",
                "Ignoring practical limits such as compatibility or setup needs.",
                "Assuming affiliate placement equals a top recommendation.",
            ],
        },
        {"type": "recommended_products", "items": recommended},
    ]
    return GeneratedArticle(
        topic_key=brief.topic_key,
        article_type=brief.article_type,
        title=title,
        slug=slugify(title),
        excerpt=short_excerpt(intro),
        seo_title=title,
        seo_description=short_excerpt(f"Learn how to choose {brief.category.lower()} products with practical criteria and source-backed recommendations.", 150),
        intro=intro,
        sections=sections,
        products=recommended,
        faq=[
            {
                "question": f"What matters most when buying {brief.category.lower()}?",
                "answer": "Prioritize the use case, then validate specs and tradeoffs on original sources.",
                "evidence_ids": recommended[0].get("evidence_ids", [])[:1] if recommended else [],
            },
            {
                "question": "Are affiliate links active in the generated draft?",
                "answer": "No. The workflow leaves placeholders for editorial review.",
                "evidence_ids": recommended[0].get("evidence_ids", [])[:1] if recommended else [],
            },
        ],
        disclosure="Disclosure: This draft contains affiliate link placeholders that editors review and replace before publication.",
        affiliate_slots=affiliate_slots,
        source_manifest=source_manifest,
        risk_flags=[],
        claim_references=_build_claim_references(recommended),
        rank_rationale="Guide recommendations are sorted by evidence completeness rather than commercial preference.",
    )


def _coerce_generated_article(payload: Dict[str, Any], brief: ArticleBrief) -> GeneratedArticle:
    normalized = _normalize_generated_payload(payload, brief)
    return GeneratedArticle(
        topic_key=normalized.get("topic_key", brief.topic_key),
        article_type=normalized.get("article_type", brief.article_type),
        title=normalized["title"],
        slug=normalized.get("slug", slugify(normalized["title"])),
        excerpt=normalized["excerpt"],
        seo_title=normalized["seo_title"],
        seo_description=normalized["seo_description"],
        intro=normalized["intro"],
        sections=normalized["sections"],
        products=normalized["products"],
        faq=normalized["faq"],
        disclosure=normalized["disclosure"],
        affiliate_slots=normalized["affiliate_slots"],
        source_manifest=normalized["source_manifest"],
        risk_flags=normalized["risk_flags"],
        claim_references=normalized["claim_references"],
        rank_rationale=normalized["rank_rationale"],
    )


def _json_schema_hint(article_type: str) -> str:
    if article_type == "comparison_roundup":
        product_shape = {
            "product_name": "string",
            "best_for": "string",
            "why_it_made_the_list": "string",
            "pros": ["string"],
            "cons": ["string"],
            "key_specs": ["string"],
            "evidence_summary": "string",
            "affiliate_slot": "string",
        }
    else:
        product_shape = {
            "product_name": "string",
            "who_it_is_for": "string",
            "why_consider_it": "string",
            "watch_out_for": "string",
            "affiliate_slot": "string",
        }
    schema = {
        "article_type": article_type,
        "title": "string",
        "slug": "string",
        "excerpt": "string",
        "seo_title": "string",
        "seo_description": "string",
        "intro": "string",
        "sections": [{"type": "string", "content": "string|optional", "items": ["mixed|optional"]}],
        "products": [product_shape],
        "faq": [{"question": "string", "answer": "string"}],
        "disclosure": "string",
        "affiliate_slots": [{"slot_id": "string", "product_name": "string", "placeholder_text": "string"}],
        "source_manifest": [{"product_name": "string", "source_urls": ["string"], "origin_urls": ["string"]}],
    }
    return json.dumps(schema, indent=2, ensure_ascii=True)


def _response_json_schema(article_type: str) -> Dict[str, Any]:
    if article_type == "comparison_roundup":
        sections_schema = {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "last_updated",
                            "how_we_picked",
                            "quick_picks_summary",
                            "who_should_buy_what",
                        ],
                        "description": "Allowed comparison section type.",
                    },
                    "content": {
                        "type": ["string", "null"],
                        "description": "Single block text for narrative sections.",
                    },
                    "items": {
                        "type": ["array", "null"],
                        "description": "List data for summary sections. Use strings only for quick_picks_summary.",
                        "items": {"type": "string"},
                    },
                },
                "required": ["type"],
                "propertyOrdering": ["type", "content", "items"],
            },
        }
    else:
        sections_schema = {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": [
                            "last_updated",
                            "what_to_consider",
                            "how_to_compare_options",
                            "common_mistakes",
                        ],
                        "description": "Allowed buying guide section type.",
                    },
                    "content": {
                        "type": ["string", "null"],
                        "description": "Single block text for narrative sections.",
                    },
                    "items": {
                        "type": ["array", "null"],
                        "description": "List data for bullet sections. Use strings only.",
                        "items": {"type": "string"},
                    },
                },
                "required": ["type"],
                "propertyOrdering": ["type", "content", "items"],
            },
        }

    if article_type == "comparison_roundup":
        product_properties = {
            "product_name": {"type": "string", "description": "Canonical product name."},
            "best_for": {"type": "string", "description": "Primary buyer or use case."},
            "why_it_made_the_list": {"type": "string", "description": "Evidence-backed inclusion reason."},
            "pros": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "Evidence-backed strengths only."},
            "cons": {"type": "array", "items": {"type": "string"}, "minItems": 1, "description": "Evidence-backed limitations only."},
            "key_specs": {"type": "array", "items": {"type": "string"}, "description": "Concise spec bullets sourced from evidence."},
            "evidence_summary": {"type": "string", "description": "Short explanation of the source basis for the recommendation."},
            "affiliate_slot": {"type": "string", "description": "Placeholder slot id, not a live link."},
        }
        product_required = ["product_name", "best_for", "why_it_made_the_list", "pros", "cons", "key_specs", "evidence_summary", "affiliate_slot"]
    else:
        product_properties = {
            "product_name": {"type": "string", "description": "Canonical product name."},
            "who_it_is_for": {"type": "string", "description": "Primary buyer or use case."},
            "why_consider_it": {"type": "string", "description": "Evidence-backed reason to consider this product."},
            "watch_out_for": {"type": "string", "description": "Evidence-backed limitation or caution."},
            "affiliate_slot": {"type": "string", "description": "Placeholder slot id, not a live link."},
        }
        product_required = ["product_name", "who_it_is_for", "why_consider_it", "watch_out_for", "affiliate_slot"]

    return {
        "type": "object",
        "properties": {
            "article_type": {"type": "string"},
            "title": {"type": "string"},
            "slug": {"type": "string"},
            "excerpt": {"type": "string"},
            "seo_title": {"type": "string"},
            "seo_description": {"type": "string"},
            "intro": {"type": "string"},
            "sections": sections_schema,
            "products": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": product_properties,
                    "required": product_required,
                    "propertyOrdering": product_required,
                },
                "minItems": 1,
            },
            "faq": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"},
                    },
                    "required": ["question", "answer"],
                    "propertyOrdering": ["question", "answer"],
                },
                "minItems": 1,
            },
            "disclosure": {"type": "string"},
            "affiliate_slots": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "slot_id": {"type": "string"},
                        "product_name": {"type": "string"},
                        "placeholder_text": {"type": "string"},
                    },
                    "required": ["slot_id", "product_name", "placeholder_text"],
                    "propertyOrdering": ["slot_id", "product_name", "placeholder_text"],
                },
                "minItems": 1,
            },
            "source_manifest": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "product_name": {"type": "string"},
                        "source_urls": {"type": "array", "items": {"type": "string"}},
                        "origin_urls": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["product_name", "source_urls", "origin_urls"],
                    "propertyOrdering": ["product_name", "source_urls", "origin_urls"],
                },
                "minItems": 1,
            },
        },
        "required": [
            "article_type",
            "title",
            "slug",
            "excerpt",
            "seo_title",
            "seo_description",
            "intro",
            "sections",
            "products",
            "faq",
            "disclosure",
            "affiliate_slots",
            "source_manifest",
        ],
        "propertyOrdering": [
            "article_type",
            "title",
            "slug",
            "excerpt",
            "seo_title",
            "seo_description",
            "intro",
            "sections",
            "products",
            "faq",
            "disclosure",
            "affiliate_slots",
            "source_manifest",
        ],
    }


def _normalize_generated_payload(payload: Dict[str, Any], brief: ArticleBrief) -> Dict[str, Any]:
    normalized = dict(payload)
    normalized["article_type"] = payload.get("article_type", brief.article_type)
    normalized["sections"] = _normalize_sections(payload.get("sections") or [], brief.article_type, brief.comparison_period)
    normalized["products"] = _normalize_products(payload.get("products") or [], brief.article_type, brief.selected_products)
    normalized["faq"] = _normalize_faq(payload.get("faq") or [], brief.selected_products, normalized["products"])
    normalized["affiliate_slots"] = _normalize_affiliate_slots(
        payload.get("affiliate_slots") or [],
        normalized["products"],
    )
    normalized["source_manifest"] = payload.get("source_manifest") or _build_source_manifest_from_brief(brief)
    normalized["risk_flags"] = [str(item) for item in (payload.get("risk_flags") or [])]
    normalized["claim_references"] = _normalize_claim_references(payload.get("claim_references") or [], normalized["products"])
    normalized["rank_rationale"] = payload.get("rank_rationale") or ""
    normalized["excerpt"] = payload.get("excerpt") or short_excerpt(payload.get("intro", ""))
    normalized["seo_title"] = payload.get("seo_title") or normalized.get("title", "")
    normalized["seo_description"] = payload.get("seo_description") or short_excerpt(payload.get("intro", ""), 150)
    return normalized


def _normalize_sections(sections: List[Dict[str, Any]], article_type: str, comparison_period: str) -> List[Dict[str, Any]]:
    allowed = (
        ["last_updated", "how_we_picked", "quick_picks_summary", "who_should_buy_what"]
        if article_type == "comparison_roundup"
        else ["last_updated", "what_to_consider", "how_to_compare_options", "common_mistakes"]
    )
    by_type = {}
    for section in sections:
        section_type = section.get("type")
        if section_type in allowed and section_type not in by_type:
            by_type[section_type] = section
    normalized = []
    for section_type in allowed:
        section = dict(by_type.get(section_type, {}))
        section["type"] = section_type
        if section_type == "last_updated":
            section["content"] = section.get("content") or comparison_period
        elif section_type in {"quick_picks_summary", "what_to_consider", "common_mistakes"}:
            items = section.get("items")
            if not isinstance(items, list):
                items = []
            section["items"] = [str(item) for item in items if item is not None]
        else:
            section["content"] = section.get("content") or ""
        normalized.append(section)
    return normalized


def _normalize_products(products: List[Dict[str, Any]], article_type: str, selected_products: List[Any]) -> List[Dict[str, Any]]:
    selected_by_name = {item.display_name: item for item in selected_products}
    selected_by_slug = {slugify(item.display_name): item for item in selected_products}
    normalized = []
    for product in products:
        item = dict(product)
        matched = _match_selected_product(item.get("product_name", ""), selected_by_name, selected_by_slug)
        if article_type == "comparison_roundup":
            item["pros"] = [str(value) for value in item.get("pros") or []]
            item["cons"] = [str(value) for value in item.get("cons") or []]
            item["key_specs"] = [str(value) for value in item.get("key_specs") or []]
            item["evidence_ids"] = _normalize_evidence_ids(item.get("evidence_ids"), matched)
            item["source_confidence"] = float(item.get("source_confidence", matched.source_confidence if matched else 0.0))
        else:
            item["evidence_ids"] = _normalize_evidence_ids(item.get("evidence_ids"), matched)
            item["source_confidence"] = float(item.get("source_confidence", matched.source_confidence if matched else 0.0))
        normalized.append(item)
    return normalized


def _normalize_faq(faq: List[Dict[str, Any]], selected_products: List[Any], normalized_products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized = []
    fallback_evidence = []
    for product in normalized_products:
        if product.get("evidence_ids"):
            fallback_evidence.extend([str(item) for item in product.get("evidence_ids", [])[:1]])
    for product in selected_products:
        for binding in product.evidence_bindings[:1]:
            fallback_evidence.append(binding["evidence_id"])
    for item in faq:
        question = item.get("question")
        answer = item.get("answer")
        if question and answer:
            normalized.append(
                {
                    "question": str(question),
                    "answer": str(answer),
                    "evidence_ids": [str(value) for value in (item.get("evidence_ids") or fallback_evidence[:1])],
                }
            )
    return normalized


def _normalize_affiliate_slots(slots: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    by_id = {}
    for slot in slots:
        slot_id = slot.get("slot_id")
        if not slot_id:
            continue
        by_id[slot_id] = {
            "slot_id": str(slot_id),
            "product_name": str(slot.get("product_name", "")),
            "placeholder_text": str(slot.get("placeholder_text", "")),
        }
    normalized = []
    for product in products:
        slot_id = str(product.get("affiliate_slot", "")).strip()
        if not slot_id:
            continue
        slot = by_id.get(slot_id) or {
            "slot_id": slot_id,
            "product_name": str(product.get("product_name", "")),
            "placeholder_text": f"[Affiliate link placeholder for {product.get('product_name', 'product')}]",
        }
        if not slot["placeholder_text"]:
            slot["placeholder_text"] = f"[Affiliate link placeholder for {slot['product_name'] or 'product'}]"
        normalized.append(slot)
    return normalized


def _build_source_manifest_from_brief(brief: ArticleBrief) -> List[Dict[str, Any]]:
    manifest = []
    for product in brief.selected_products:
        manifest.append(
            {
                "product_name": product.display_name,
                "source_urls": product.source_urls,
                "origin_urls": product.origin_urls,
            }
        )
    return manifest


def _normalize_evidence_ids(raw_ids: Any, matched: Any) -> List[str]:
    if isinstance(raw_ids, list) and raw_ids:
        return [str(item) for item in raw_ids]
    if matched:
        return [binding["evidence_id"] for binding in matched.evidence_bindings]
    return []


def _normalize_claim_references(raw_references: List[Dict[str, Any]], products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    references = []
    if raw_references:
        for item in raw_references:
            product_name = str(item.get("product_name", ""))
            evidence_id = str(item.get("evidence_id", ""))
            if product_name and evidence_id:
                references.append({"product_name": product_name, "evidence_id": evidence_id})
    if references:
        return references
    return _build_claim_references(products)


def _match_selected_product(product_name: str, selected_by_name: Dict[str, Any], selected_by_slug: Dict[str, Any]) -> Any:
    if product_name in selected_by_name:
        return selected_by_name[product_name]
    product_slug = slugify(product_name)
    if product_slug in selected_by_slug:
        return selected_by_slug[product_slug]

    normalized_target = _normalize_name_token(product_name)
    for item in selected_by_name.values():
        normalized_source = _normalize_name_token(item.display_name)
        if normalized_target and normalized_source and (
            normalized_target in normalized_source or normalized_source in normalized_target
        ):
            return item
    return None


def _normalize_name_token(value: str) -> str:
    lowered = value.lower()
    lowered = lowered.replace("third generation", "3rd generation")
    lowered = lowered.replace("second generation", "2nd generation")
    lowered = lowered.replace("first generation", "1st generation")
    lowered = lowered.replace(" ii", " 2")
    lowered = lowered.replace(" iii", " 3")
    lowered = lowered.replace(" iv", " 4")
    lowered = lowered.replace("/", " ")
    lowered = lowered.replace("(", " ").replace(")", " ")
    lowered = " ".join(lowered.split())
    return lowered


def _build_claim_references(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    references = []
    for product in products:
        for evidence_id in product.get("evidence_ids", []):
            references.append(
                {
                    "product_name": product.get("product_name", ""),
                    "evidence_id": evidence_id,
                }
            )
    return references
