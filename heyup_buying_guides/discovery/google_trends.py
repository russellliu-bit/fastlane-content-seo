from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, List


class GoogleTrendsClient:
    def fetch_trending_queries(self, geo: str = "US") -> List[Dict[str, str]]:
        url = f"https://trends.google.com/trending/rss?geo={urllib.parse.quote(geo)}"
        with urllib.request.urlopen(url, timeout=30) as response:
            xml_payload = response.read().decode("utf-8")
        root = ET.fromstring(xml_payload)
        items = []
        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            traffic = item.findtext("{https://trends.google.com/trending/rss}approx_traffic") or ""
            items.append({"title": title, "approx_traffic": traffic})
        return items

    def score_keyword(self, keyword: str, trends: List[Dict[str, str]]) -> float:
        query_terms = set(keyword.lower().split())
        if not query_terms:
            return 0.0
        score = 0.0
        for item in trends:
            title_terms = set(item["title"].lower().split())
            overlap = len(query_terms & title_terms)
            if overlap:
                score = max(score, min(1.0, overlap / max(len(query_terms), 1)))
        return round(score, 3)
