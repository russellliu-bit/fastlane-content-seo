from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .cache import FileCache
from .config import WorkflowConfig
from .discovery.serper import SerperClient
from .schemas import GeneratedArticle

_BANNED_TOKENS = (
    "case",
    "cover",
    "replacement",
    "charger",
    "cable",
    "bundle",
    "renewed",
    "refurbished",
    "refill",
    "ear pads",
    "earpads",
    "accessory",
    "adapter",
)


@dataclass
class AmazonMatch:
    product_name: str
    slot_id: str
    url: Optional[str]
    asin: Optional[str]
    title: str
    confidence: float
    status: str
    notes: List[str]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def resolve_amazon_links(article: GeneratedArticle, config: WorkflowConfig) -> Tuple[GeneratedArticle, List[AmazonMatch]]:
    if config.llm_mode == "stub" or not config.amazon_enabled or not config.serper_api_key:
        if config.amazon_enabled and not config.amazon_associate_tag and "missing_amazon_associate_tag" not in article.risk_flags:
            article.risk_flags.append("missing_amazon_associate_tag")
        return article, []

    serper = SerperClient(config.serper_api_key)
    cache = FileCache(config.cache_root) if config.llm_cache_enabled else None
    matches: List[AmazonMatch] = []
    slot_map = {slot.get("slot_id", ""): slot for slot in article.affiliate_slots}

    for product in article.products:
        slot_id = str(product.get("affiliate_slot", "")).strip()
        product_name = str(product.get("product_name", "")).strip()
        if not slot_id or not product_name:
            continue
        match = _resolve_product(product_name, slot_id, config, serper, cache)
        matches.append(match)
        if match.url:
            product["affiliate_url"] = match.url
            product["amazon_asin"] = match.asin
            slot_map.setdefault(slot_id, {})
            slot_map[slot_id]["slot_id"] = slot_id
            slot_map[slot_id]["product_name"] = product_name
            slot_map[slot_id]["url"] = match.url
            slot_map[slot_id]["asin"] = match.asin or ""
            slot_map[slot_id]["marketplace"] = config.amazon_domain
            slot_map[slot_id]["confidence"] = f"{match.confidence:.2f}"
            slot_map[slot_id]["placeholder_text"] = match.url
        else:
            if "missing_amazon_match" not in article.risk_flags:
                article.risk_flags.append("missing_amazon_match")

    article.affiliate_slots = list(slot_map.values())
    if not config.amazon_associate_tag and "missing_amazon_associate_tag" not in article.risk_flags:
        article.risk_flags.append("missing_amazon_associate_tag")
    return article, matches


def _resolve_product(
    product_name: str,
    slot_id: str,
    config: WorkflowConfig,
    serper: SerperClient,
    cache: Optional[FileCache],
) -> AmazonMatch:
    query = f'site:{config.amazon_domain} "{product_name}"'
    cached = cache.get("amazon_serper", {"query": query, "domain": config.amazon_domain}) if cache else None
    if cached is None:
        try:
            results = serper.search(query, "us", num=config.amazon_match_limit)
        except URLError:
            return AmazonMatch(
                product_name=product_name,
                slot_id=slot_id,
                url=None,
                asin=None,
                title="",
                confidence=0.0,
                status="lookup_failed",
                notes=["serper_lookup_failed"],
            )
        if cache:
            cache.set("amazon_serper", {"query": query, "domain": config.amazon_domain}, results)
    else:
        results = cached

    best_url: Optional[str] = None
    best_title = ""
    best_asin: Optional[str] = None
    best_score = 0.0
    notes: List[str] = []
    for item in results:
        candidate = _normalize_amazon_url(str(item.get("link", "")).strip(), config.amazon_domain, config.amazon_associate_tag)
        title = str(item.get("title", "")).strip()
        if not candidate:
            continue
        asin = _extract_asin(candidate)
        if not asin:
            continue
        score, score_notes = _score_candidate(product_name, title, candidate)
        if score > best_score:
            best_score = score
            best_url = candidate
            best_title = title
            best_asin = asin
            notes = score_notes

    status = "matched" if best_url else "missing"
    return AmazonMatch(
        product_name=product_name,
        slot_id=slot_id,
        url=best_url,
        asin=best_asin,
        title=best_title,
        confidence=round(best_score, 2),
        status=status,
        notes=notes,
    )


def _normalize_amazon_url(url: str, domain: str, associate_tag: Optional[str]) -> Optional[str]:
    if not url:
        return None
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if domain not in host and "amazon.com" not in host:
        return None
    path = parsed.path
    asin = _extract_asin(url)
    if not asin:
        return None
    clean_path = f"/dp/{asin}"
    query = dict(parse_qsl(parsed.query, keep_blank_values=False))
    if associate_tag:
        query["tag"] = associate_tag
    filtered = {
        key: value
        for key, value in query.items()
        if key in {"tag", "psc", "smid", "th"}
    }
    return urlunparse(("https", domain, clean_path, "", urlencode(filtered), ""))


def _extract_asin(url: str) -> Optional[str]:
    parsed = urlparse(url)
    parts = [segment for segment in parsed.path.split("/") if segment]
    for index, segment in enumerate(parts):
        upper = segment.upper()
        if upper == "DP" and index + 1 < len(parts):
            asin = parts[index + 1].upper()
            if len(asin) == 10 and asin.isalnum():
                return asin
        if len(upper) == 10 and upper.isalnum() and any(char.isdigit() for char in upper):
            return upper
    return None


def _score_candidate(product_name: str, title: str, url: str) -> Tuple[float, List[str]]:
    notes: List[str] = []
    product_tokens = set(_tokenize(product_name))
    title_tokens = set(_tokenize(title))
    overlap = len(product_tokens & title_tokens)
    score = min(0.95, overlap / max(len(product_tokens), 1))
    if overlap:
        notes.append(f"token_overlap={overlap}")
    lowered_title = title.lower()
    lowered_url = url.lower()
    if any(token in lowered_title or token in lowered_url for token in _BANNED_TOKENS):
        score -= 0.35
        notes.append("banned_token")
    if "amazon.com/dp/" in lowered_url:
        score += 0.15
        notes.append("canonical_dp")
    return min(1.0, max(0.0, score)), notes


def _tokenize(value: str) -> List[str]:
    cleaned = value.lower()
    for char in "()[]/,.-":
        cleaned = cleaned.replace(char, " ")
    return [token for token in cleaned.split() if token]
