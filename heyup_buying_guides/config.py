from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .env import load_dotenv

DEFAULT_CATALOG = Path("codex_knowledge_base/14_external_sources_catalog.csv")


@dataclass
class SourceConfig:
    domain: str
    enabled: bool
    source_role: str
    category_mapping: List[str] = field(default_factory=list)
    parser: str = "generic_html"
    rate_limit_policy: str = "default"
    seed_url: Optional[str] = None
    title: Optional[str] = None
    why_it_matters: Optional[str] = None


@dataclass
class WorkflowConfig:
    artifact_root: Path
    cache_root: Path = Path("artifacts/cache")
    source_catalog: Path = DEFAULT_CATALOG
    state_db_path: Path = Path("artifacts/state.db")
    allowed_domains: List[str] = field(default_factory=list)
    category: str = "Audio"
    article_type: str = "comparison_roundup"
    affiliate_mode: str = "placeholder"
    author: str = "Heyup Editorial"
    blog_id: Optional[str] = None
    shopify_store: Optional[str] = None
    shopify_access_token: Optional[str] = None
    shopify_api_version: str = "2025-01"
    publish_mode: str = "stub"
    amazon_enabled: bool = True
    amazon_domain: str = "www.amazon.com"
    amazon_associate_tag: Optional[str] = None
    amazon_match_limit: int = 5
    fixtures_path: Optional[Path] = None
    llm_mode: str = "stub"
    llm_provider: str = "gemini"
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_api_key_env: str = "GEMINI_API_KEY"
    llm_timeout_seconds: int = 60
    google_search_grounding: bool = True
    serper_api_key: Optional[str] = None
    serper_api_key_env: str = "SERPER_API_KEY"
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_username: Optional[str] = None
    reddit_password: Optional[str] = None
    reddit_user_agent: str = "heyup-buying-guides/0.1"
    feishu_webhook_url: Optional[str] = None
    trend_geo: str = "US"
    discovery_frequency_hours: int = 24
    discovery_enabled: bool = True
    auto_select_topic: bool = True
    topic_seed_queries: List[str] = field(default_factory=list)
    raw_keyword: Optional[str] = None
    seed_query_count: int = 5
    apify_token: Optional[str] = None
    apify_sync_timeout_seconds: int = 300
    apify_poll_interval_seconds: int = 5
    apify_require_success_for_seed: bool = True
    max_topics: int = 10
    topic_quality_threshold: float = 0.65
    duplicate_topic_window_days: int = 14
    max_products: int = 5
    min_products: int = 3
    llm_cache_enabled: bool = True
    origin_candidate_url_limit: int = 2
    origin_url_context_budget: int = 2
    discovery_grounding_retries: int = 2
    discovery_grounding_timeout_seconds: int = 30


def load_workflow_config(path: Path) -> WorkflowConfig:
    dotenv_path = path.parent / ".env"
    if not dotenv_path.exists():
        dotenv_path = Path.cwd() / ".env"
    load_dotenv(dotenv_path)
    raw = json.loads(path.read_text())
    artifact_root = Path(raw.get("artifact_root", "artifacts"))
    cfg = WorkflowConfig(
        artifact_root=artifact_root,
        cache_root=Path(_resolve_value(raw, "cache_root", "CACHE_ROOT", "artifacts/cache")),
        source_catalog=Path(raw.get("source_catalog", str(DEFAULT_CATALOG))),
        state_db_path=Path(raw.get("state_db_path", _resolve_value(raw, "state_db_path", "STATE_DB_PATH", "artifacts/state.db"))),
        allowed_domains=list(raw.get("allowed_domains", [])),
        category=raw.get("category", "Audio"),
        article_type=raw.get("article_type", "comparison_roundup"),
        affiliate_mode=raw.get("affiliate_mode", "placeholder"),
        author=raw.get("author", "Heyup Editorial"),
        blog_id=_resolve_value(raw, "blog_id", "SHOPIFY_BLOG_ID"),
        shopify_store=_resolve_value(raw, "shopify_store", "SHOPIFY_STORE"),
        shopify_access_token=_resolve_value(raw, "shopify_access_token", "SHOPIFY_ACCESS_TOKEN"),
        shopify_api_version=_resolve_value(raw, "shopify_api_version", "SHOPIFY_API_VERSION", "2025-01"),
        publish_mode=_resolve_value(raw, "publish_mode", "PUBLISH_MODE", "stub"),
        amazon_enabled=_resolve_value(raw, "amazon_enabled", "AMAZON_ENABLED", "true").lower() == "true",
        amazon_domain=_resolve_value(raw, "amazon_domain", "AMAZON_DOMAIN", "www.amazon.com"),
        amazon_associate_tag=_resolve_value(raw, "amazon_associate_tag", "AMAZON_ASSOCIATE_TAG"),
        amazon_match_limit=int(_resolve_value(raw, "amazon_match_limit", "AMAZON_MATCH_LIMIT", 5)),
        fixtures_path=Path(raw["fixtures_path"]) if raw.get("fixtures_path") else None,
        llm_mode=_resolve_value(raw, "llm_mode", "LLM_MODE", "stub"),
        llm_provider=_resolve_value(raw, "llm_provider", "LLM_PROVIDER", "gemini"),
        llm_base_url=_resolve_value(raw, "llm_base_url", "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
        llm_model=_resolve_value(raw, "llm_model", "LLM_MODEL"),
        llm_api_key_env=_resolve_value(raw, "llm_api_key_env", "LLM_API_KEY_ENV", "GEMINI_API_KEY"),
        llm_api_key=_resolve_api_key(raw),
        llm_timeout_seconds=int(_resolve_value(raw, "llm_timeout_seconds", "LLM_TIMEOUT_SECONDS", 60)),
        google_search_grounding=_resolve_value(raw, "google_search_grounding", "GOOGLE_SEARCH_GROUNDING", "true").lower() == "true",
        serper_api_key=_resolve_value(raw, "serper_api_key", "SERPER_API_KEY"),
        serper_api_key_env=_resolve_value(raw, "serper_api_key_env", "SERPER_API_KEY_ENV", "SERPER_API_KEY"),
        reddit_client_id=_resolve_value(raw, "reddit_client_id", "REDDIT_CLIENT_ID"),
        reddit_client_secret=_resolve_value(raw, "reddit_client_secret", "REDDIT_CLIENT_SECRET"),
        reddit_username=_resolve_value(raw, "reddit_username", "REDDIT_USERNAME"),
        reddit_password=_resolve_value(raw, "reddit_password", "REDDIT_PASSWORD"),
        reddit_user_agent=_resolve_value(raw, "reddit_user_agent", "REDDIT_USER_AGENT", "heyup-buying-guides/0.1"),
        feishu_webhook_url=_resolve_value(raw, "feishu_webhook_url", "FEISHU_WEBHOOK_URL"),
        trend_geo=_resolve_value(raw, "trend_geo", "TREND_GEO", "US"),
        discovery_frequency_hours=int(_resolve_value(raw, "discovery_frequency_hours", "DISCOVERY_FREQUENCY_HOURS", 24)),
        discovery_enabled=_resolve_value(raw, "discovery_enabled", "DISCOVERY_ENABLED", "true").lower() == "true",
        auto_select_topic=_resolve_value(raw, "auto_select_topic", "AUTO_SELECT_TOPIC", "true").lower() == "true",
        topic_seed_queries=list(raw.get("topic_seed_queries", [])),
        raw_keyword=_resolve_value(raw, "raw_keyword", "RAW_KEYWORD"),
        seed_query_count=int(_resolve_value(raw, "seed_query_count", "SEED_QUERY_COUNT", 5)),
        apify_token=_resolve_value(raw, "apify_token", "APIFY_TOKEN"),
        apify_sync_timeout_seconds=int(_resolve_value(raw, "apify_sync_timeout_seconds", "APIFY_SYNC_TIMEOUT_SECONDS", 300)),
        apify_poll_interval_seconds=int(_resolve_value(raw, "apify_poll_interval_seconds", "APIFY_POLL_INTERVAL_SECONDS", 5)),
        apify_require_success_for_seed=_resolve_value(raw, "apify_require_success_for_seed", "APIFY_REQUIRE_SUCCESS_FOR_SEED", "true").lower() == "true",
        max_topics=int(_resolve_value(raw, "max_topics", "MAX_TOPICS", 10)),
        topic_quality_threshold=float(_resolve_value(raw, "topic_quality_threshold", "TOPIC_QUALITY_THRESHOLD", 0.65)),
        duplicate_topic_window_days=int(_resolve_value(raw, "duplicate_topic_window_days", "DUPLICATE_TOPIC_WINDOW_DAYS", 14)),
        max_products=int(raw.get("max_products", 5)),
        min_products=int(raw.get("min_products", 3)),
        llm_cache_enabled=_resolve_value(raw, "llm_cache_enabled", "LLM_CACHE_ENABLED", "true").lower() == "true",
        origin_candidate_url_limit=int(_resolve_value(raw, "origin_candidate_url_limit", "ORIGIN_CANDIDATE_URL_LIMIT", 2)),
        origin_url_context_budget=int(_resolve_value(raw, "origin_url_context_budget", "ORIGIN_URL_CONTEXT_BUDGET", 2)),
        discovery_grounding_retries=int(_resolve_value(raw, "discovery_grounding_retries", "DISCOVERY_GROUNDING_RETRIES", 2)),
        discovery_grounding_timeout_seconds=int(_resolve_value(raw, "discovery_grounding_timeout_seconds", "DISCOVERY_GROUNDING_TIMEOUT_SECONDS", 30)),
    )
    return cfg


def _resolve_value(raw: Dict[str, Any], field_name: str, env_name: str, default: Optional[Any] = None) -> Optional[str]:
    env_value = os.getenv(env_name)
    if env_value not in (None, ""):
        return env_value
    value = raw.get(field_name)
    if value not in (None, ""):
        return str(value)
    if default is None:
        return None
    return str(default)


def _resolve_api_key(raw: Dict[str, Any]) -> Optional[str]:
    explicit_key = raw.get("llm_api_key")
    if explicit_key:
        return str(explicit_key)
    api_key_env_name = _resolve_value(raw, "llm_api_key_env", "LLM_API_KEY_ENV", "GEMINI_API_KEY")
    if not api_key_env_name:
        return None
    return os.getenv(api_key_env_name)


def load_source_configs(catalog_path: Path, allowed_domains: List[str]) -> List[SourceConfig]:
    results: List[SourceConfig] = []
    with catalog_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            domain = _extract_domain(row["url"])
            if allowed_domains and domain not in allowed_domains:
                continue
            role = _role_from_group(row["group"])
            results.append(
                SourceConfig(
                    domain=domain,
                    enabled=True,
                    source_role=role,
                    category_mapping=_infer_categories(row["title"], row["why_it_matters"]),
                    parser="generic_html",
                    rate_limit_policy="default",
                    seed_url=row["url"],
                    title=row["title"],
                    why_it_matters=row["why_it_matters"],
                )
            )
    return results


def _extract_domain(url: str) -> str:
    trimmed = url.replace("https://", "").replace("http://", "")
    return trimmed.split("/", 1)[0]


def _role_from_group(group: str) -> str:
    if group == "Reference samples":
        return "reference_site"
    if group == "Compliance":
        return "policy_reference"
    if group == "Google Search":
        return "search_guidance"
    return "other"


def _infer_categories(title: str, why: str) -> List[str]:
    joined = f"{title} {why}".lower()
    categories = []
    keywords = {
        "audio": "Audio",
        "headphone": "Audio",
        "laptop": "Computing",
        "smartphone": "Smartphones & Tablets",
        "wearable": "Wearables",
        "gaming": "Gaming Accessories",
    }
    for key, value in keywords.items():
        if key in joined and value not in categories:
            categories.append(value)
    return categories or ["Tech & Gadgets"]
