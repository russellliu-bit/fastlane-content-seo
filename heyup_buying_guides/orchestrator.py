from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .artifacts import ArtifactStore
from .amazon_resolver import resolve_amazon_links
from .config import WorkflowConfig, load_source_configs
from .discovery.google_trends import GoogleTrendsClient
from .discovery.reddit import RedditClient
from .discovery.search_grounding import GeminiSearchGroundingClient, discover_with_cache
from .discovery.serper import SerperClient
from .evidence_extractor import bind_candidate_evidence
from .notify import send_feishu_webhook
from .origin_resolver import resolve_brand_origins
from .render import render_article_html
from .schemas import RunReport, TopicCandidate
from .seed_query_generator import generate_seed_query_plan, seed_queries_to_discovery_queries
from .storage import StateStore
from .stages.briefing import build_article_brief
from .stages.discover import discover_sources
from .stages.enrich import enrich_candidates
from .stages.extract import extract_candidates
from .stages.fetch import fetch_documents
from .stages.generate import generate_article_json
from .stages.normalize import normalize_and_dedupe
from .stages.publish import publish_draft
from .stages.score import score_and_select
from .stages.validate import validate_article
from .topic_ranker import build_topic_candidates
from .utils import ensure_dir, utc_now_iso


def run_workflow(config: WorkflowConfig) -> RunReport:
    run_id = uuid4().hex[:12]
    artifacts = ArtifactStore(ensure_dir(config.artifact_root), run_id)
    started_at = utc_now_iso()
    state_store = StateStore(config.state_db_path)

    selected_topic = None
    topic_scores: Dict[str, float] = {}
    quality_score = 0.0
    blocking_reasons: List[str] = []
    documents = []

    use_seed_driven_discovery = bool(config.raw_keyword)
    workflow_category = _resolve_workflow_category(config)
    seed_plan = None
    if config.discovery_enabled and (config.auto_select_topic or use_seed_driven_discovery):
        topics, seed_plan = run_discovery(config, artifacts, run_id, state_store)
        selected_topic = _pick_topic(topics, config.topic_quality_threshold)
        if selected_topic:
            topic_scores = selected_topic.signal_scores
            quality_score = selected_topic.draftability_score
        else:
            blocking_reasons.append("no_topic_passed_threshold")

    if selected_topic:
        normalized = normalize_and_dedupe(resolve_brand_origins(bind_candidate_evidence(selected_topic.candidate_products), config))
        normalized = enrich_candidates(normalized)
        selected = score_and_select(normalized, config.max_products)
        artifacts.write_json("normalized_candidates.json", [item.to_dict() for item in normalized])
        artifacts.write_json("selected_candidates.json", [item.to_dict() for item in selected])
        brief = build_article_brief(selected_topic.article_type, selected_topic.category, selected, config.affiliate_mode, topic=selected_topic)
        if seed_plan and seed_plan.selected_topic.editorial_title:
            brief.title_candidates = _prepend_unique_title(seed_plan.selected_topic.editorial_title, brief.title_candidates)
        artifacts.write_json("topic_candidate.json", selected_topic.to_dict())
        artifacts.write_json("article_brief.json", brief.to_dict())
    else:
        sources = load_source_configs(config.source_catalog, config.allowed_domains)
        discovered = discover_sources(sources)
        artifacts.write_json("discovered_sources.json", discovered)

        documents = fetch_documents(discovered, config.fixtures_path)
        artifacts.write_json("raw_sources.json", [item.to_dict() for item in documents])

        extracted = extract_candidates(documents, workflow_category, config)
        artifacts.write_json("extracted_candidates.json", [item.to_dict() for item in extracted])

        enriched = enrich_candidates(resolve_brand_origins(bind_candidate_evidence(extracted), config))
        artifacts.write_json("enriched_candidates.json", [item.to_dict() for item in enriched])

        normalized = normalize_and_dedupe(enriched)
        artifacts.write_json("normalized_candidates.json", [item.to_dict() for item in normalized])

        selected = score_and_select(normalized, config.max_products)
        artifacts.write_json("selected_candidates.json", [item.to_dict() for item in selected])

        brief = build_article_brief(config.article_type, workflow_category, selected, config.affiliate_mode)
        artifacts.write_json("article_brief.json", brief.to_dict())
        topic_scores = {}
        quality_score = max((item.confidence_score for item in selected), default=0.0)

    article, prompt = generate_article_json(brief, config)
    if selected_topic:
        recent = state_store.get_recent_topic_runs(selected_topic.topic_key, limit=5)
        if recent:
            article.risk_flags.append("duplicate_topic_risk")
    article, amazon_matches = resolve_amazon_links(article, config)
    artifacts.write_text("generation_prompt.txt", prompt)
    artifacts.write_json("generated_article.json", article.to_dict())
    artifacts.write_json("amazon_matches.json", [item.to_dict() for item in amazon_matches])

    errors = validate_article(article, brief, config.min_products)
    if selected_topic and quality_score < config.topic_quality_threshold:
        errors.append("topic_quality_below_threshold")
    blocking_reasons.extend(errors)
    validation_status = "passed" if not errors else "failed"

    html = render_article_html(article)
    artifacts.write_text("rendered_article.html", html)

    shopify_status = "skipped"
    shopify_article_id = None
    if not errors:
        publish_result = publish_draft(article, html, config)
        shopify_status = publish_result.status
        shopify_article_id = publish_result.article_id
        artifacts.write_json("shopify_response.json", publish_result.raw_response or {})
        state_store.save_publication_attempt(run_id, article.topic_key, publish_result.status, "shopify", publish_result.raw_response or {})
        _notify_success(config, article.title, publish_result.url or shopify_article_id or "", article)
    else:
        _notify_failure(config, brief.topic_key, blocking_reasons or errors)

    report = RunReport(
        run_id=run_id,
        started_at=started_at,
        source_pages_count=len(documents),
        candidate_count=len(normalized),
        selected_count=len(selected),
        article_type=article.article_type,
        article_title=article.title,
        validation_status=validation_status,
        shopify_status=shopify_status,
        shopify_article_id=shopify_article_id,
        topic_key=brief.topic_key,
        topic_scores=topic_scores,
        quality_score=quality_score,
        blocking_reasons=blocking_reasons,
        errors=errors,
        artifact_paths=artifacts.paths,
    )
    artifacts.write_json("run_report.json", report.to_dict())
    state_store.save_article_run(report)
    return report


def run_discovery(
    config: WorkflowConfig,
    artifacts: ArtifactStore,
    run_id: str,
    state_store: StateStore,
) -> tuple[List[TopicCandidate], Optional[Any]]:
    seed_plan = None
    workflow_category = _resolve_workflow_category(config)
    artifacts.write_json(
        "discovery_stage_started.json",
        {
            "run_id": run_id,
            "raw_keyword": config.raw_keyword,
            "article_type": config.article_type,
            "workflow_category": workflow_category,
        },
    )
    if config.raw_keyword:
        seed_plan = generate_seed_query_plan(config.raw_keyword, config.article_type, config, artifacts=artifacts)
        artifacts.write_json("seed_queries.json", seed_plan.to_dict())
    topics = _load_discovery_fixtures(config.fixtures_path)
    if topics is None:
        dynamic_queries = seed_queries_to_discovery_queries(seed_plan) if config.raw_keyword else None
        artifacts.write_json(
            "seed_discovery_queries.json",
            {
                "queries": dynamic_queries or config.topic_seed_queries,
                "workflow_category": workflow_category,
            },
        )
        topics = _discover_topics_live(config, dynamic_queries, workflow_category, artifacts=artifacts)
    artifacts.write_json(
        "discovery_stage_completed.json",
        {
            "topic_count": len(topics),
            "ready_topic_count": len([item for item in topics if item.status == "ready"]),
            "workflow_category": workflow_category,
        },
    )
    artifacts.write_json("topic_candidates.json", [item.to_dict() for item in topics])
    state_store.save_discovery_run(run_id, "completed", topics)
    return topics, seed_plan


def _discover_topics_live(
    config: WorkflowConfig,
    override_queries: Optional[List[str]] = None,
    category_override: Optional[str] = None,
    artifacts: Optional[ArtifactStore] = None,
) -> List[TopicCandidate]:
    effective_category = category_override or config.category
    seed_queries = override_queries or config.topic_seed_queries or [
        "best wireless headphones 2026",
        "how to choose noise cancelling headphones",
        "best earbuds for commuting 2026",
    ]
    grounding = GeminiSearchGroundingClient(
        config.llm_base_url,
        config.llm_model or "gemini-2.5-flash",
        config.llm_api_key or "",
        timeout_seconds=config.discovery_grounding_timeout_seconds,
    )
    trends_client = GoogleTrendsClient()
    serper_client = SerperClient(config.serper_api_key) if config.serper_api_key else None
    reddit_client = (
        RedditClient(
            config.reddit_client_id or "",
            config.reddit_client_secret or "",
            config.reddit_username or "",
            config.reddit_password or "",
            config.reddit_user_agent,
        )
        if all([config.reddit_client_id, config.reddit_client_secret, config.reddit_username, config.reddit_password])
        else None
    )
    discovered_topics = []
    trend_feed = trends_client.fetch_trending_queries(config.trend_geo)
    trend_scores: Dict[str, float] = {}
    reddit_scores: Dict[str, float] = {}
    query_logs: List[Dict[str, Any]] = []
    for query in seed_queries:
        query_log: Dict[str, Any] = {
            "query": query,
            "category": effective_category,
            "steps": [{"name": "grounding_started"}],
        }
        _artifact_json(artifacts, "discovery_stage_status.json", {"current_query": query, "status": "grounding_started"})
        _artifact_json(
            artifacts,
            "grounding_call_started.json",
            {"query": query, "category": effective_category, "model": grounding.model},
        )
        discovered = _coerce_discovery_payload(discover_with_cache(grounding, query, effective_category, config), query, effective_category)
        query_log["keyword"] = discovered.get("keyword", query)
        query_log["article_type"] = discovered.get("article_type")
        query_log["candidate_product_count"] = len(discovered.get("candidate_products", []))
        query_log["steps"].append({"name": "grounding_completed"})
        if serper_client:
            query_log["steps"].append({"name": "serper_started"})
            _artifact_json(artifacts, "discovery_stage_status.json", {"current_query": query, "status": "serper_started"})
            organic = serper_client.search(query, config.trend_geo.lower())
            discovered.setdefault("source_urls", [])
            discovered["source_urls"].extend([item.get("link") for item in organic if item.get("link")])
            discovered.setdefault("signal_summary", "")
            if organic:
                discovered["signal_summary"] = (discovered["signal_summary"] + " Search results support buying intent.").strip()
            query_log["serper_result_count"] = len(organic)
            query_log["steps"].append({"name": "serper_completed"})
        discovered["query"] = query
        discovered_topics.append(discovered)
        trend_scores[discovered.get("keyword", query)] = trends_client.score_keyword(discovered.get("keyword", query), trend_feed)
        query_log["trend_score"] = trend_scores[discovered.get("keyword", query)]
        if reddit_client:
            query_log["steps"].append({"name": "reddit_started"})
            _artifact_json(artifacts, "discovery_stage_status.json", {"current_query": query, "status": "reddit_started"})
            posts = reddit_client.search(discovered.get("keyword", query), limit=5)
            reddit_scores[discovered.get("keyword", query)] = _reddit_score(posts)
            query_log["reddit_post_count"] = len(posts)
            query_log["reddit_score"] = reddit_scores[discovered.get("keyword", query)]
            query_log["steps"].append({"name": "reddit_completed"})
        query_logs.append(query_log)
        _artifact_json(
            artifacts,
            "discovery_stage_status.json",
            {"current_query": query, "status": "query_completed", "query_log": query_log},
        )
        _artifact_json(artifacts, "discovery_query_logs.json", query_logs)
    return build_topic_candidates(
        effective_category,
        discovered_topics,
        trend_scores,
        reddit_scores,
        config.max_topics,
        config.topic_quality_threshold,
    )


def _coerce_discovery_payload(payload: Any, query: str, category: str) -> Dict[str, Any]:
    if isinstance(payload, list):
        if not payload:
            return {"query": query, "keyword": query, "candidate_products": [], "source_urls": [], "signal_summary": ""}
        first = next((item for item in payload if isinstance(item, dict)), {})
        payload = first
    elif not isinstance(payload, dict):
        payload = {}

    if isinstance(payload.get("topics"), list):
        first_topic = next((item for item in payload["topics"] if isinstance(item, dict)), None)
        if first_topic:
            payload = first_topic

    payload.setdefault("query", query)
    payload.setdefault("keyword", query)
    payload.setdefault("article_type", _infer_article_type(query))
    payload.setdefault("intent_type", "comparison" if payload["article_type"] == "comparison_roundup" else "guide")
    payload.setdefault("title_hypotheses", [])
    payload.setdefault("candidate_products", [])
    payload.setdefault("source_urls", [])
    payload.setdefault("signal_summary", f"Grounding returned buying-guide candidates for {category.lower()}.")
    payload.setdefault("rationale", f"Discovered from query: {query}")
    return payload


def _infer_article_type(query: str) -> str:
    lowered = query.lower()
    if any(token in lowered for token in ("how to choose", "what to look for", "buyer's guide", "buyers guide")):
        return "buying_guide"
    return "comparison_roundup"


def _load_discovery_fixtures(fixtures_path: Optional[Path]) -> Optional[List[TopicCandidate]]:
    if not fixtures_path:
        return None
    candidate_file = fixtures_path / "topic_candidates.json"
    if not candidate_file.exists():
        return None
    payload = json.loads(candidate_file.read_text())
    from .schemas import CandidateProduct

    topics = []
    for item in payload:
        item["candidate_products"] = [CandidateProduct(**candidate) for candidate in item.get("candidate_products", [])]
        topics.append(TopicCandidate(**item))
    return topics


def _resolve_workflow_category(config: WorkflowConfig) -> str:
    if not config.raw_keyword:
        return config.category
    return _infer_category_from_keyword(config.raw_keyword) or config.category


def _infer_category_from_keyword(raw_keyword: str) -> Optional[str]:
    lowered = raw_keyword.strip().lower()
    category_rules = {
        "Computing": ["laptop", "macbook", "notebook", "chromebook", "desktop", "pc", "monitor"],
        "Smartphones & Tablets": ["smartphone", "iphone", "android phone", "phone", "tablet", "ipad", "foldable"],
        "Audio": ["headphone", "headphones", "earbud", "earbuds", "speaker", "soundbar", "microphone", "dac", "amp"],
        "Wearables": ["smartwatch", "watch", "ring", "glasses", "fitness tracker", "wearable"],
        "Gaming Accessories": ["gaming headset", "gaming mouse", "gaming keyboard", "controller", "gaming laptop", "handheld"],
        "Smart Home": ["smart home", "robot vacuum", "security camera", "doorbell", "air purifier", "smart light", "home hub"],
    }
    for category, keywords in category_rules.items():
        for keyword in keywords:
            pattern = r"(^|\b)" + re.escape(keyword) + r"(\b|$)"
            if re.search(pattern, lowered):
                return category
    return None


def _pick_topic(topics: List[TopicCandidate], min_score: float) -> Optional[TopicCandidate]:
    ready = [item for item in topics if item.status == "ready" and item.draftability_score >= min_score]
    return ready[0] if ready else None


def _reddit_score(posts: List[Dict]) -> float:
    if not posts:
        return 0.0
    score = 0.0
    for post in posts:
        score = max(score, min(1.0, (post.get("score", 0) + post.get("num_comments", 0)) / 500.0))
    return round(score, 3)


def _notify_success(config: WorkflowConfig, title: str, draft_link: str, article: Any) -> None:
    admin_link = _build_shopify_admin_article_link(config.shopify_store, draft_link)
    lines = [
        "",
        f"Article: {title}",
        f"Topic: {article.topic_key}",
        f"Type: {article.article_type}",
        f"Risks: {', '.join(article.risk_flags) if article.risk_flags else 'none'}",
        "",
        "👉 Review in Shopify:",
        admin_link or draft_link,
        "",
        "Next: add affiliate links, add images, final factual review, publish.",
    ]
    send_feishu_webhook(config.feishu_webhook_url, "✅ Buying Guide Sync Complete", lines)


def _notify_failure(config: WorkflowConfig, topic_key: str, reasons: List[str]) -> None:
    lines = [
        f"Topic: {topic_key}",
        f"Blocking reasons: {', '.join(reasons) if reasons else 'unknown'}",
        "Manual follow-up: review topic quality, evidence coverage, and FAQ compliance.",
    ]
    send_feishu_webhook(config.feishu_webhook_url, "[Heyup Buying Guides] Draft blocked", lines)


def _build_shopify_admin_article_link(shopify_store: Optional[str], article_ref: str) -> str:
    if not shopify_store or not article_ref:
        return article_ref
    article_id = _extract_numeric_id(article_ref)
    if not article_id:
        return article_ref
    store_handle = shopify_store.split(".", 1)[0]
    return f"https://admin.shopify.com/store/{store_handle}/content/articles/{article_id}"


def _extract_numeric_id(value: str) -> str:
    if not value:
        return ""
    if value.isdigit():
        return value
    if "/" in value:
        tail = value.rsplit("/", 1)[-1]
        if tail.isdigit():
            return tail
    return ""


def _prepend_unique_title(title: str, titles: List[str]) -> List[str]:
    merged = [title] + list(titles or [])
    deduped = []
    seen = set()
    for item in merged:
        key = item.strip().lower()
        if item and key not in seen:
            deduped.append(item)
            seen.add(key)
    return deduped


def _artifact_json(artifacts: Optional[ArtifactStore], filename: str, payload: Any) -> None:
    if artifacts is None:
        return
    artifacts.write_json(filename, payload)
