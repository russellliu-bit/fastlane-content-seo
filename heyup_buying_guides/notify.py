from __future__ import annotations

import json
import urllib.request
from typing import Dict, List, Optional


def send_feishu_webhook(webhook_url: Optional[str], title: str, lines: List[str]) -> Dict:
    payload = {
        "msg_type": "text",
        "content": {
            "text": "\n".join([title] + lines),
        },
    }
    if not webhook_url:
        return payload
    request = urllib.request.Request(
        url=webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))
