from __future__ import annotations

import json
import re
import socket
import urllib.request
from typing import Any, Dict, List, Optional

from ..cache import FileCache
from ..config import WorkflowConfig


class GeminiSearchGroundingClient:
    def __init__(self, base_url: str, model: str, api_key: str, timeout_seconds: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def discover(self, query: str, category: str) -> Dict[str, Any]:
        prompt = (
            "Find buying-guide-worthy topics for a US English tech commerce newsroom. "
            "Return JSON only with fields: keyword, intent_type, article_type, title_hypotheses, "
            "candidate_products, source_urls, signal_summary, rationale. "
            "Prefer comparison and buying-guide intents. "
            f"Category context: {category}. Query: {query}."
        )
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"responseMimeType": "application/json"},
        }
        request = urllib.request.Request(
            url=f"{self.base_url}/models/{self.model}:generateContent",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self.api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            raw = json.loads(response.read().decode("utf-8"))
        text_parts = raw.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        content = "".join(part.get("text", "") for part in text_parts)
        return _parse_json_payload(content)


def discover_with_cache(client: GeminiSearchGroundingClient, query: str, category: str, config: WorkflowConfig) -> Dict[str, Any]:
    cache = FileCache(config.cache_root, config.llm_cache_enabled)
    cache_key = cache.make_key("grounding", client.model, query, category)
    cached = cache.get("discovery_grounding", cache_key)
    if cached:
        return cached

    last_error: Optional[Exception] = None
    for _ in range(max(1, config.discovery_grounding_retries)):
        try:
            payload = client.discover(query, category)
            if payload:
                cache.set("discovery_grounding", cache_key, payload)
            return payload
        except (urllib.error.URLError, socket.timeout, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    if cached:
        return cached
    if last_error:
        return {
            "query": query,
            "keyword": query,
            "candidate_products": [],
            "source_urls": [],
            "signal_summary": f"Grounding fallback after error: {last_error}",
            "rationale": f"Grounding failed for query: {query}",
        }
    return {
        "query": query,
        "keyword": query,
        "candidate_products": [],
        "source_urls": [],
        "signal_summary": f"Grounding returned no payload for query: {query}",
        "rationale": f"Grounding failed for query: {query}",
    }


def _parse_json_payload(content: str) -> Dict[str, Any]:
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```json\s*(\{.*\}|\[.*\])\s*```", content, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    trimmed = _extract_balanced_json(content)
    if trimmed:
        try:
            return json.loads(trimmed)
        except json.JSONDecodeError:
            pass

    return {}


def _extract_balanced_json(content: str) -> str:
    start_positions = [idx for idx, char in enumerate(content) if char in "[{"]
    for start in start_positions:
        opening = content[start]
        closing = "}" if opening == "{" else "]"
        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(content)):
            char = content[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue
            if char == '"':
                in_string = True
                continue
            if char == opening:
                depth += 1
            elif char == closing:
                depth -= 1
                if depth == 0:
                    return content[start : index + 1]
    return ""
