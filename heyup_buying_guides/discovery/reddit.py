from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional


class RedditClient:
    def __init__(self, client_id: str, client_secret: str, username: str, password: str, user_agent: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.user_agent = user_agent

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        praw_results = self._search_with_praw(query, limit)
        if praw_results is not None:
            return praw_results
        token = self._get_access_token()
        url = (
            "https://oauth.reddit.com/search?"
            + urllib.parse.urlencode({"q": query, "limit": limit, "sort": "top", "t": "week", "type": "link"})
        )
        request = urllib.request.Request(
            url=url,
            headers={
                "Authorization": f"bearer {token}",
                "User-Agent": self.user_agent,
            },
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        children = payload.get("data", {}).get("children", [])
        return [child.get("data", {}) for child in children]

    def _search_with_praw(self, query: str, limit: int) -> Optional[List[Dict[str, Any]]]:
        try:
            import praw
        except ImportError:
            return None

        reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
        )
        try:
            posts: List[Dict[str, Any]] = []
            for submission in reddit.subreddit("all").search(query, sort="top", time_filter="week", limit=limit):
                posts.append(
                    {
                        "id": submission.id,
                        "title": submission.title,
                        "selftext": submission.selftext or "",
                        "author": str(submission.author) if submission.author else "[deleted]",
                        "subreddit": submission.subreddit.display_name,
                        "permalink": submission.permalink,
                        "score": submission.score,
                        "num_comments": submission.num_comments,
                        "created_utc": submission.created_utc,
                    }
                )
            return posts
        except Exception:
            return None

    def _get_access_token(self) -> str:
        token = self._client_credentials_token()
        if token:
            return token
        return self._password_grant_token()

    def _client_credentials_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        encoded = base64.b64encode(credentials).decode("utf-8")
        body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        request = urllib.request.Request(
            url="https://www.reddit.com/api/v1/access_token",
            data=body,
            headers={
                "Authorization": f"Basic {encoded}",
                "User-Agent": self.user_agent,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload["access_token"]
        except Exception:
            return ""

    def _password_grant_token(self) -> str:
        credentials = f"{self.client_id}:{self.client_secret}".encode("utf-8")
        encoded = base64.b64encode(credentials).decode("utf-8")
        body = urllib.parse.urlencode(
            {
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            }
        ).encode("utf-8")
        request = urllib.request.Request(
            url="https://www.reddit.com/api/v1/access_token",
            data=body,
            headers={
                "Authorization": f"Basic {encoded}",
                "User-Agent": self.user_agent,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["access_token"]
