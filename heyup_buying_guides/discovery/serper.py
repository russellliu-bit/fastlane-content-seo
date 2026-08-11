from __future__ import annotations

import json
import urllib.request
from typing import Any, Dict, List


class SerperClient:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, location: str = "us", num: int = 8) -> List[Dict[str, Any]]:
        request = urllib.request.Request(
            url="https://google.serper.dev/search",
            data=json.dumps({"q": query, "gl": location, "num": num}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": self.api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("organic", [])
