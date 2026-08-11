from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .cache import FileCache
from .config import WorkflowConfig
from .discovery.google_trends import GoogleTrendsClient
from .discovery.serper import SerperClient
from .llm import GeminiLLMClient, build_llm_client
from .utils import slugify


@dataclass
class SeedQueryCandidate:
    topic: str
    intent: str
    format_fit: str
    priority_score: float
    reason: str
    evidence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SelectedSeedTopic:
    discovery_query: str
    editorial_title: str
    reason: str
    evidence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SeedQueryPlan:
    raw_keyword: str
    requested_article_type: str
    data_source: str
    market_signal: Dict[str, Any]
    candidate_topics: List[SeedQueryCandidate]
    selected_topic: SelectedSeedTopic

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["candidate_topics"] = [item.to_dict() for item in self.candidate_topics]
        payload["selected_topic"] = self.selected_topic.to_dict()
        payload["recommended_topic"] = {
            "topic": self.selected_topic.editorial_title,
            "reason": self.selected_topic.reason,
        }
        return payload


def generate_seed_query_plan(
    raw_keyword: str,
    article_type: str,
    config: WorkflowConfig,
    artifacts: Optional[Any] = None,
) -> SeedQueryPlan:
    _artifact_json(
        artifacts,
        "seed_stage_started.json",
        {
            "raw_keyword": raw_keyword,
            "article_type": article_type,
            "started_at": datetime.now().isoformat(),
        },
    )
    market_signal = collect_market_signal(raw_keyword, config, artifacts=artifacts)
    candidate_topics, recommended_topic = _generate_keyword_topics(raw_keyword, article_type, market_signal, config)
    candidate_topics, recommended_topic = _normalize_seed_topics(raw_keyword, article_type, candidate_topics, recommended_topic)
    candidate_topics, recommended_topic = _polish_seed_topics(raw_keyword, article_type, candidate_topics, recommended_topic, config)
    selected_topic = _select_seed_topic(raw_keyword, article_type, candidate_topics, recommended_topic)
    plan = SeedQueryPlan(
        raw_keyword=raw_keyword,
        requested_article_type=article_type,
        data_source=market_signal.get("source", "unknown"),
        market_signal=market_signal,
        candidate_topics=candidate_topics,
        selected_topic=selected_topic,
    )
    _artifact_json(artifacts, "seed_stage_completed.json", plan.to_dict())
    return plan


def collect_market_signal(raw_keyword: str, config: WorkflowConfig, artifacts: Optional[Any] = None) -> Dict[str, Any]:
    if config.llm_mode == "stub":
        payload = {
            "raw_keyword": raw_keyword,
            "market": config.trend_geo,
            "source": "stub_market_signal",
            "top_queries": [
                raw_keyword,
                f"best {raw_keyword}",
                f"{raw_keyword} 2026",
            ],
            "rising_queries": [
                f"best {raw_keyword} 2026",
                f"{raw_keyword} vs competitors",
            ],
            "geo_hotspots": [],
            "serp_titles": [],
            "serp_links": [],
            "trend_summary": f"Stub market signal generated for {raw_keyword}.",
        }
        _artifact_json(artifacts, "seed_market_signal.json", payload)
        return payload

    cache = FileCache(config.cache_root) if config.llm_cache_enabled else None
    cache_key = {"raw_keyword": raw_keyword, "geo": config.trend_geo}
    if cache:
        cached = cache.get("seed_market_signal", cache_key)
        if cached:
            _artifact_json(artifacts, "seed_market_signal.json", cached)
            _artifact_json(artifacts, "seed_stage_status.json", {"status": "cache_hit", "source": cached.get("source")})
            return cached

    if config.apify_token:
        try:
            _artifact_json(artifacts, "seed_stage_status.json", {"status": "apify_started"})
            market_signal = _collect_market_signal_via_apify(raw_keyword, config, artifacts=artifacts)
            if _market_signal_is_empty(market_signal):
                failure_payload = market_signal.get("_apify_failure") or {
                    "reason": "empty_market_signal",
                    "message": "Apify actor finished without usable trend queries.",
                }
                _artifact_json(artifacts, "apify_run_failure.json", failure_payload)
                _artifact_json(
                    artifacts,
                    "seed_stage_status.json",
                    {
                        "status": "apify_empty_result",
                        "failure": failure_payload,
                    },
                )
                if config.apify_require_success_for_seed:
                    raise RuntimeError(failure_payload.get("message") or "Apify actor returned no usable trend queries.")
                market_signal = _collect_market_signal_via_local_tools(raw_keyword, config)
                market_signal["fallback_reason"] = failure_payload.get("message") or failure_payload.get("reason", "apify_empty_result")
                market_signal["fallback_from"] = "apify/google-trends-scraper"
        except Exception as exc:
            status = "apify_failed_seed_blocked" if config.apify_require_success_for_seed else "apify_failed_fallback_used"
            _artifact_json(
                artifacts,
                "seed_stage_status.json",
                {
                    "status": status,
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
            )
            _artifact_json(
                artifacts,
                "apify_run_failure.json",
                {
                    "reason": "exception",
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
            )
            if config.apify_require_success_for_seed:
                raise
            market_signal = _collect_market_signal_via_local_tools(raw_keyword, config)
            market_signal["fallback_reason"] = f"{exc.__class__.__name__}: {exc}"
            market_signal["fallback_from"] = "apify/google-trends-scraper"
    else:
        market_signal = _collect_market_signal_via_local_tools(raw_keyword, config)
    if cache:
        cache.set("seed_market_signal", cache_key, market_signal)
    market_signal = _sanitize_market_signal(market_signal)
    _artifact_json(artifacts, "seed_market_signal.json", market_signal)
    return market_signal


def _collect_market_signal_via_apify(raw_keyword: str, config: WorkflowConfig, artifacts: Optional[Any] = None) -> Dict[str, Any]:
    run_input = {
        "searchTerms": [raw_keyword],
        "geo": config.trend_geo,
        "timeRange": "today 3-m",
        "maxItems": 10,
        "maxConcurrency": 2,
        "maxRequestRetries": 3,
        "pageLoadTimeoutSecs": 90,
    }
    _artifact_json(artifacts, "apify_run_input.json", run_input)
    run = _apify_start_actor_run("apify/google-trends-scraper", run_input, config)
    _artifact_json(artifacts, "apify_run_started.json", run)
    completed = _apify_wait_for_run(run["id"], config, artifacts=artifacts)
    dataset_id = (completed.get("defaultDatasetId") or completed.get("data", {}).get("defaultDatasetId"))
    if not dataset_id:
        raise ValueError("Apify actor finished without a dataset id.")
    rows = _apify_fetch_dataset_items(dataset_id, config)
    _artifact_json(artifacts, "apify_dataset_items_preview.json", rows[:1])
    payload = rows[0] if rows else {}
    normalized = _normalize_market_signal_from_trends(raw_keyword, config, payload, source="apify/google-trends-scraper")
    normalized["_apify_failure"] = {
        "reason": "empty_dataset" if not rows else "empty_trend_fields",
        "message": str(completed.get("statusMessage", "")).strip() or "Apify actor returned no usable dataset items.",
        "run_id": run["id"],
        "dataset_id": dataset_id,
        "status": completed.get("status"),
        "status_message": completed.get("statusMessage"),
        "row_count": len(rows),
    }
    return normalized


def _apify_start_actor_run(actor_name: str, run_input: Dict[str, Any], config: WorkflowConfig) -> Dict[str, Any]:
    encoded_actor = actor_name.replace("/", "~")
    path = f"/v2/acts/{encoded_actor}/runs?token={urllib.parse.quote(config.apify_token or '')}"
    payload = _apify_api_request(path, data=run_input, timeout_seconds=30)
    data = payload.get("data", payload)
    if not data.get("id"):
        raise ValueError(f"Apify actor start response missing run id: {payload}")
    return data


def _apify_wait_for_run(run_id: str, config: WorkflowConfig, artifacts: Optional[Any] = None) -> Dict[str, Any]:
    deadline = time.time() + config.apify_sync_timeout_seconds
    terminal_statuses = {"SUCCEEDED", "FAILED", "TIMED-OUT", "ABORTED"}
    poll_log: List[Dict[str, Any]] = []
    while time.time() < deadline:
        payload = _apify_api_request(
            f"/v2/actor-runs/{run_id}?token={urllib.parse.quote(config.apify_token or '')}",
            timeout_seconds=30,
        )
        data = payload.get("data", payload)
        status = str(data.get("status", "")).upper()
        status_message = str(data.get("statusMessage", "")).strip()
        dataset_id = data.get("defaultDatasetId") or data.get("data", {}).get("defaultDatasetId")
        poll_log.append(
            {
                "checked_at": datetime.now().isoformat(),
                "status": status,
                "status_message": status_message,
                "dataset_id": dataset_id,
            }
        )
        _artifact_json(artifacts, "apify_run_poll_log.json", poll_log)
        if dataset_id and (data.get("isStatusMessageTerminal") or status_message.startswith("Finished!")):
            return data
        if status in terminal_statuses:
            if status != "SUCCEEDED":
                raise RuntimeError(f"Apify actor run {run_id} finished with status {status}.")
            return data
        time.sleep(max(1, config.apify_poll_interval_seconds))
    raise TimeoutError(f"Apify actor run {run_id} did not finish within {config.apify_sync_timeout_seconds} seconds.")


def _apify_fetch_dataset_items(dataset_id: str, config: WorkflowConfig) -> List[Dict[str, Any]]:
    params = urllib.parse.urlencode(
        {
            "token": config.apify_token or "",
            "format": "json",
            "clean": "true",
        }
    )
    payload = _apify_api_request(
        f"/v2/datasets/{dataset_id}/items?{params}",
        timeout_seconds=60,
    )
    if isinstance(payload, list):
        return payload
    data = payload.get("data")
    if isinstance(data, list):
        return data
    return []


def _apify_api_request(path: str, data: Optional[Dict[str, Any]] = None, timeout_seconds: int = 30) -> Any:
    url = f"https://api.apify.com{path}"
    request = urllib.request.Request(
        url=url,
        data=json.dumps(data).encode("utf-8") if data is not None else None,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def _collect_market_signal_via_local_tools(raw_keyword: str, config: WorkflowConfig) -> Dict[str, Any]:
    trends_client = GoogleTrendsClient()
    trend_feed = trends_client.fetch_trending_queries(config.trend_geo)
    serper_client = SerperClient(config.serper_api_key) if config.serper_api_key else None
    organic = serper_client.search(raw_keyword, config.trend_geo.lower(), num=8) if serper_client else []
    return {
        "raw_keyword": raw_keyword,
        "market": config.trend_geo,
        "source": "google_trends_rss+serper",
        "top_queries": [item["title"] for item in trend_feed[:10]],
        "rising_queries": [],
        "geo_hotspots": [],
        "serp_titles": [item.get("title", "") for item in organic if item.get("title")],
        "serp_links": [item.get("link", "") for item in organic if item.get("link")],
        "trend_summary": f"Fallback market signal for {raw_keyword} in {config.trend_geo} using local Google Trends RSS and Serper.",
    }


def _normalize_market_signal_from_trends(
    raw_keyword: str,
    config: WorkflowConfig,
    payload: Dict[str, Any],
    source: str,
) -> Dict[str, Any]:
    top_queries = [item.get("query", "") for item in payload.get("relatedQueries_top", []) if item.get("query")]
    rising_queries = [item.get("query", "") for item in payload.get("relatedQueries_rising", []) if item.get("query")]
    geo_hotspots = [item.get("geoName", "") for item in payload.get("interestBySubregion", [])[:10] if item.get("geoName")]
    trend_summary = (
        f"Interest for {raw_keyword} in {config.trend_geo} shows active demand with top related queries and rising brand/product terms."
    )
    return {
        "raw_keyword": raw_keyword,
        "market": config.trend_geo,
        "source": source,
        "top_queries": top_queries[:25],
        "rising_queries": rising_queries[:15],
        "geo_hotspots": geo_hotspots,
        "serp_titles": [],
        "serp_links": [],
        "trend_summary": trend_summary,
    }


def _market_signal_is_empty(market_signal: Dict[str, Any]) -> bool:
    return not any(
        market_signal.get(key)
        for key in ("top_queries", "rising_queries", "geo_hotspots", "serp_titles", "serp_links")
    )


def _sanitize_market_signal(market_signal: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in market_signal.items() if not str(key).startswith("_")}


def _generate_keyword_topics(
    raw_keyword: str,
    article_type: str,
    market_signal: Dict[str, Any],
    config: WorkflowConfig,
) -> tuple[List[SeedQueryCandidate], Dict[str, str]]:
    if config.llm_mode == "stub":
        candidates = _stub_seed_topics(raw_keyword, article_type, market_signal)
        return candidates[: config.seed_query_count], {
            "topic": candidates[0].topic if candidates else raw_keyword,
            "reason": "Deterministic stub output based on keyword and article type.",
        }

    client = build_llm_client(config)
    if not isinstance(client, GeminiLLMClient):
        candidates = _stub_seed_topics(raw_keyword, article_type, market_signal)
        return candidates[: config.seed_query_count], {
            "topic": candidates[0].topic if candidates else raw_keyword,
            "reason": "Fallback output because Gemini client was unavailable.",
        }

    prompt = _build_keyword_prompt(raw_keyword, article_type, market_signal, config.seed_query_count)
    schema = {
        "type": "object",
        "properties": {
            "raw_keyword": {"type": "string"},
            "requested_article_type": {"type": "string"},
            "candidate_topics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string"},
                        "intent": {"type": "string"},
                        "format_fit": {"type": "string"},
                        "priority_score": {"type": "number"},
                        "reason": {"type": "string"},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["topic", "intent", "format_fit", "priority_score", "reason", "evidence"],
                },
            },
            "recommended_topic": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["topic", "reason"],
            },
        },
        "required": ["raw_keyword", "requested_article_type", "candidate_topics", "recommended_topic"],
    }
    result = client.generate_json_object(prompt, schema)
    candidates = [
        SeedQueryCandidate(
            topic=str(item.get("topic", "")).strip(),
            intent=str(item.get("intent", "")).strip(),
            format_fit=str(item.get("format_fit", "")).strip(),
            priority_score=float(item.get("priority_score", 0.0) or 0.0),
            reason=str(item.get("reason", "")).strip(),
            evidence=[str(value) for value in item.get("evidence", []) if value],
        )
        for item in result.get("candidate_topics", [])
        if str(item.get("topic", "")).strip()
    ]
    candidates = [item for item in candidates if item.format_fit == article_type]
    if not candidates:
        candidates = _stub_seed_topics(raw_keyword, article_type, market_signal)
    recommended = result.get("recommended_topic") or {
        "topic": candidates[0].topic if candidates else raw_keyword,
        "reason": "Fallback to top candidate because recommended topic was missing.",
    }
    return candidates[: config.seed_query_count], recommended


def _normalize_seed_topics(
    raw_keyword: str,
    article_type: str,
    candidates: List[SeedQueryCandidate],
    recommended: Dict[str, str],
) -> tuple[List[SeedQueryCandidate], Dict[str, str]]:
    current_year = datetime.now().year
    normalized_candidates: List[SeedQueryCandidate] = []
    seen = set()
    for item in candidates:
        normalized_topic = _normalize_seed_topic_title(item.topic, article_type, raw_keyword, current_year)
        key = slugify(normalized_topic)
        if not key or key in seen:
            continue
        seen.add(key)
        normalized_candidates.append(
            SeedQueryCandidate(
                topic=normalized_topic,
                intent=item.intent,
                format_fit=article_type,
                priority_score=item.priority_score,
                reason=item.reason,
                evidence=item.evidence,
            )
        )
    if not normalized_candidates:
        normalized_candidates = _stub_seed_topics(raw_keyword, article_type, {"top_queries": [], "rising_queries": []})

    recommended_topic = str(recommended.get("topic") or "").strip()
    normalized_recommended_topic = _normalize_seed_topic_title(
        recommended_topic or normalized_candidates[0].topic,
        article_type,
        raw_keyword,
        current_year,
    )
    normalized_recommended = {
        "topic": normalized_recommended_topic,
        "reason": str(recommended.get("reason") or "Normalized from generated candidate topics.").strip(),
    }
    recommended_key = slugify(normalized_recommended_topic)
    for item in normalized_candidates:
        if slugify(item.topic) == recommended_key:
            normalized_recommended["topic"] = item.topic
            break
    return normalized_candidates, normalized_recommended


def _normalize_seed_topic_title(topic: str, article_type: str, raw_keyword: str, current_year: int) -> str:
    cleaned = " ".join(str(topic or "").replace("’", "'").split()).strip(" :-")
    cleaned = _normalize_year_tokens(cleaned, current_year)
    if not cleaned:
        cleaned = _default_seed_topic(raw_keyword, article_type, current_year)

    lowered = cleaned.lower()
    if article_type == "comparison_roundup":
        if re.search(r"\bvs\.?\b", lowered):
            return _ensure_vs_title_case(cleaned, current_year)
        if not re.search(r"\b(best|top)\b", lowered):
            cleaned = f"Best {raw_keyword.title()} of {current_year}"
        cleaned = _ensure_roundup_year(cleaned, current_year)
        return cleaned

    if re.search(r"\bvs\.?\b", lowered):
        return _ensure_vs_title_case(cleaned, current_year)
    if "buying guide" in lowered:
        cleaned = _ensure_buying_guide_year(cleaned, current_year)
    elif "how to choose" in lowered:
        cleaned = _ensure_how_to_choose_year(cleaned, current_year)
    elif re.search(r"\b(best|top)\b", lowered):
        cleaned = _ensure_roundup_year(cleaned, current_year)
    else:
        cleaned = _default_seed_topic(raw_keyword, article_type, current_year)
    return cleaned


def _normalize_year_tokens(text: str, current_year: int) -> str:
    return re.sub(r"\b20(2[0-9]|3[0-5])\b", str(current_year), text)


def _ensure_roundup_year(text: str, current_year: int) -> str:
    if re.search(r"\b20(2[0-9]|3[0-5])\b", text):
        return text
    if ":" in text:
        head, tail = text.split(":", 1)
        return f"{head} of {current_year}: {tail.strip()}"
    return f"{text} of {current_year}"


def _ensure_buying_guide_year(text: str, current_year: int) -> str:
    if re.search(r"\b20(2[0-9]|3[0-5])\b", text):
        return text
    if ":" in text:
        head, tail = text.split(":", 1)
        return f"{head} {current_year}: {tail.strip()}"
    return f"{text} {current_year}"


def _ensure_how_to_choose_year(text: str, current_year: int) -> str:
    if re.search(r"\b20(2[0-9]|3[0-5])\b", text):
        return text
    return f"{text} in {current_year}"


def _ensure_vs_title_case(text: str, current_year: int) -> str:
    cleaned = text.replace("Vs.", "vs.").replace(" VS ", " vs ")
    return _normalize_year_tokens(cleaned, current_year)


def _default_seed_topic(raw_keyword: str, article_type: str, current_year: int) -> str:
    if article_type == "comparison_roundup":
        return f"Best {raw_keyword.title()} of {current_year}"
    return f"{raw_keyword.title()} Buying Guide {current_year}: How to Choose the Right Option"


def _select_seed_topic(
    raw_keyword: str,
    article_type: str,
    candidates: List[SeedQueryCandidate],
    recommended: Dict[str, str],
) -> SelectedSeedTopic:
    editorial_title = str(recommended.get("topic") or "").strip()
    reason = str(recommended.get("reason") or "").strip() or "Selected as the highest-priority seed topic."
    chosen = None
    if editorial_title:
        chosen = next((item for item in candidates if slugify(item.topic) == slugify(editorial_title)), None)
    if chosen is None and candidates:
        chosen = max(candidates, key=lambda item: item.priority_score)
        editorial_title = chosen.topic
        if not reason:
            reason = chosen.reason
    if chosen is None:
        editorial_title = _default_seed_topic(raw_keyword, article_type, datetime.now().year)
        chosen = SeedQueryCandidate(
            topic=editorial_title,
            intent="commercial investigation",
            format_fit=article_type,
            priority_score=0.0,
            reason=reason or "Fallback selection because no seed candidates were available.",
            evidence=[raw_keyword],
        )
    discovery_query = _build_discovery_query(editorial_title, raw_keyword, article_type)
    return SelectedSeedTopic(
        discovery_query=discovery_query,
        editorial_title=editorial_title,
        reason=reason or chosen.reason,
        evidence=chosen.evidence,
    )


def _build_discovery_query(editorial_title: str, raw_keyword: str, article_type: str) -> str:
    title = editorial_title.strip().replace("’", "'")
    title = re.sub(r"^[Tt]he\s+", "", title)
    if re.search(r"\bvs\.?\b", title, re.IGNORECASE):
        query = re.split(r"\s*:\s*", title, maxsplit=1)[0]
        return query.strip()
    if article_type == "buying_guide":
        if re.search(r"\bhow to choose\b", title, re.IGNORECASE):
            query = re.split(r"\s*:\s*", title, maxsplit=1)[0]
            return query.strip()
        match = re.search(r"\b(best|top)\b.+?\b(20\d{2})\b", title, re.IGNORECASE)
        if match:
            query = re.split(r"\s*:\s*", title, maxsplit=1)[0]
            query = re.sub(r"^The\s+", "", query, flags=re.IGNORECASE).strip()
            return query
        if re.search(r"\bbuying guide\b", title, re.IGNORECASE):
            query = re.split(r"\s*:\s*", title, maxsplit=1)[0]
            return query.strip()
    query = re.split(r"\s*:\s*", title, maxsplit=1)[0].strip()
    if not query:
        return raw_keyword
    return query


def _artifact_json(artifacts: Optional[Any], filename: str, payload: Any) -> None:
    if artifacts is None:
        return
    try:
        artifacts.write_json(filename, payload)
    except Exception:
        return


def _polish_seed_topics(
    raw_keyword: str,
    article_type: str,
    candidates: List[SeedQueryCandidate],
    recommended: Dict[str, str],
    config: WorkflowConfig,
) -> tuple[List[SeedQueryCandidate], Dict[str, str]]:
    if config.llm_mode == "stub":
        return candidates, recommended

    client = build_llm_client(config)
    if not isinstance(client, GeminiLLMClient):
        return candidates, recommended

    cache = FileCache(config.cache_root) if config.llm_cache_enabled else None
    cache_key = {
        "raw_keyword": raw_keyword,
        "article_type": article_type,
        "candidates": [item.topic for item in candidates],
        "recommended": recommended.get("topic"),
    }
    if cache:
        cached = cache.get("seed_topic_polish", cache_key)
        if cached:
            return _coerce_polished_topics(raw_keyword, article_type, candidates, recommended, cached)

    prompt = (
        "You are polishing English newsroom seed topics for SEO-driven buying guides.\n"
        f"raw_keyword: {raw_keyword}\n"
        f"article_type: {article_type}\n"
        "Task: lightly polish the titles for clarity and native English.\n"
        "Rules:\n"
        "- Preserve the same topic intent.\n"
        "- Preserve the year exactly.\n"
        "- Do not add or remove brands, products, or use cases.\n"
        "- Do not broaden or narrow the topic.\n"
        "- Keep buying_guide titles editorial and practical.\n"
        "- Keep comparison_roundup titles comparison- or roundup-friendly.\n"
        "- Return concise, publication-ready English titles only.\n\n"
        f"Candidates JSON:\n{json.dumps([item.to_dict() for item in candidates], ensure_ascii=False)}\n\n"
        f"Recommended JSON:\n{json.dumps(recommended, ensure_ascii=False)}"
    )
    schema = {
        "type": "object",
        "properties": {
            "candidate_topics": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "original_topic": {"type": "string"},
                        "polished_topic": {"type": "string"},
                    },
                    "required": ["original_topic", "polished_topic"],
                },
            },
            "recommended_topic": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["topic", "reason"],
            },
        },
        "required": ["candidate_topics", "recommended_topic"],
    }

    try:
        result = client.generate_json_object(prompt, schema)
    except Exception:
        return candidates, recommended
    if cache:
        cache.set("seed_topic_polish", cache_key, result)
    return _coerce_polished_topics(raw_keyword, article_type, candidates, recommended, result)


def _coerce_polished_topics(
    raw_keyword: str,
    article_type: str,
    candidates: List[SeedQueryCandidate],
    recommended: Dict[str, str],
    result: Dict[str, Any],
) -> tuple[List[SeedQueryCandidate], Dict[str, str]]:
    current_year = datetime.now().year
    mapping = {}
    for item in result.get("candidate_topics", []):
        original = str(item.get("original_topic") or "").strip()
        polished = str(item.get("polished_topic") or "").strip()
        if original and polished:
            mapping[slugify(original)] = polished

    polished_candidates: List[SeedQueryCandidate] = []
    for item in candidates:
        polished_topic = mapping.get(slugify(item.topic), item.topic)
        polished_topic = _normalize_seed_topic_title(polished_topic, article_type, raw_keyword, current_year)
        polished_candidates.append(
            SeedQueryCandidate(
                topic=polished_topic,
                intent=item.intent,
                format_fit=item.format_fit,
                priority_score=item.priority_score,
                reason=item.reason,
                evidence=item.evidence,
            )
        )

    recommended_topic = str(result.get("recommended_topic", {}).get("topic") or recommended.get("topic") or "").strip()
    recommended_reason = str(result.get("recommended_topic", {}).get("reason") or recommended.get("reason") or "").strip()
    recommended_topic = _normalize_seed_topic_title(
        recommended_topic or polished_candidates[0].topic,
        article_type,
        raw_keyword,
        current_year,
    )
    recommended_key = slugify(recommended_topic)
    for item in polished_candidates:
        if slugify(item.topic) == recommended_key:
            recommended_topic = item.topic
            break
    return polished_candidates, {"topic": recommended_topic, "reason": recommended_reason or "Polished for editorial readability."}


def _build_keyword_prompt(raw_keyword: str, article_type: str, market_signal: Dict[str, Any], limit: int) -> str:
    return (
        "You are executing the keyword-research skill for a buying-guides newsroom.\n"
        f"raw_keyword: {raw_keyword}\n"
        f"requested_article_type: {article_type}\n"
        "target_market: US\n"
        "target_language: English\n"
        "Goal: transform one raw keyword into shortlist topic candidates suitable for downstream discovery.\n\n"
        "Rules:\n"
        "- Prefer commercial investigation intent.\n"
        "- For comparison_roundup, generate either best/top/list-style roundup topics or explicit X vs Y comparisons.\n"
        "- For buying_guide, prefer best/how to choose/use-case topics.\n"
        "- Avoid purely informational topics unless they can be reframed into commercial intent.\n"
        "- Prefer topics with real product/entity specificity and strong discovery potential.\n"
        f"- Output at most {limit} candidate topics.\n\n"
        f"Market signal JSON:\n{json.dumps(market_signal, ensure_ascii=False)}"
    )


def _stub_seed_topics(raw_keyword: str, article_type: str, market_signal: Dict[str, Any]) -> List[SeedQueryCandidate]:
    top_queries = market_signal.get("top_queries", [])
    rising_queries = market_signal.get("rising_queries", [])
    if article_type == "comparison_roundup":
        base = [
            SeedQueryCandidate(
                topic=f"Best {raw_keyword.title()} 2026",
                intent="commercial_comparison",
                format_fit="comparison_roundup",
                priority_score=4.5,
                reason="Broad commercial roundup built from the raw keyword.",
                evidence=[raw_keyword, *top_queries[:2]],
            ),
            SeedQueryCandidate(
                topic=f"{_pick_brandish(top_queries, rising_queries, 'Ray-Ban Meta')} vs {_pick_brandish(rising_queries, top_queries, 'Rokid AI Glasses')}",
                intent="commercial_comparison",
                format_fit="comparison_roundup",
                priority_score=4.1,
                reason="Entity-vs-entity comparison inferred from market signal.",
                evidence=top_queries[:2] + rising_queries[:2],
            ),
        ]
    else:
        base = [
            SeedQueryCandidate(
                topic=f"How to Choose {raw_keyword.title()} in 2026",
                intent="commercial",
                format_fit="buying_guide",
                priority_score=4.3,
                reason="Buyer-guide framing built from the raw keyword.",
                evidence=[raw_keyword, *top_queries[:2]],
            ),
            SeedQueryCandidate(
                topic=f"Best {raw_keyword.title()} for Daily Use",
                intent="commercial",
                format_fit="buying_guide",
                priority_score=4.0,
                reason="Use-case guide inferred from market signal.",
                evidence=top_queries[:2] + rising_queries[:1],
            ),
        ]
    return base


def _pick_brandish(primary: List[str], secondary: List[str], fallback: str) -> str:
    for pool in (primary, secondary):
        for item in pool:
            cleaned = item.strip()
            if cleaned and len(cleaned.split()) >= 2:
                return cleaned.title()
    return fallback


def seed_queries_to_discovery_queries(plan: SeedQueryPlan) -> List[str]:
    if plan.selected_topic.discovery_query:
        return [plan.selected_topic.discovery_query]
    if plan.selected_topic.editorial_title:
        return [plan.selected_topic.editorial_title]
    return []
