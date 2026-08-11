from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ShopifyPublishResult:
    status: str
    article_id: Optional[str] = None
    url: Optional[str] = None
    raw_response: Optional[Dict] = None


class StubShopifyPublisher:
    def publish_draft(self, payload: Dict) -> ShopifyPublishResult:
        fake_id = f"gid://shopify/Article/{abs(hash(payload['title'])) % 1000000}"
        return ShopifyPublishResult(status="stubbed", article_id=fake_id, url=f"stub://drafts/{payload['handle']}", raw_response=payload)


class ShopifyRestPublisher:
    def __init__(self, store: str, access_token: str, api_version: str, blog_id: str) -> None:
        self.store = store
        self.access_token = access_token
        self.api_version = api_version
        self.blog_id = blog_id

    def publish_draft(self, payload: Dict) -> ShopifyPublishResult:
        url = f"https://{self.store}/admin/api/{self.api_version}/blogs/{self.blog_id}/articles.json"
        handle = payload["handle"]
        body = {
            "article": {
                "title": payload["title"],
                "author": payload["author"],
                "tags": ", ".join(payload["tags"]),
                "body_html": payload["body_html"],
                "summary_html": payload["excerpt"],
                "published": False,
                "handle": handle,
                "metafields": [
                    {
                        "namespace": "global",
                        "key": "title_tag",
                        "type": "single_line_text_field",
                        "value": payload["seo_title"],
                    },
                    {
                        "namespace": "global",
                        "key": "description_tag",
                        "type": "single_line_text_field",
                        "value": payload["seo_description"],
                    },
                    {
                        "namespace": "heyup_automation",
                        "key": "topic_key",
                        "type": "single_line_text_field",
                        "value": payload["topic_key"],
                    },
                    {
                        "namespace": "heyup_automation",
                        "key": "risk_flags",
                        "type": "json",
                        "value": json.dumps(payload["risk_flags"]),
                    },
                    {
                        "namespace": "heyup_automation",
                        "key": "source_manifest_summary",
                        "type": "json",
                        "value": json.dumps(payload["source_manifest_summary"]),
                    },
                ],
            }
        }
        request = urllib.request.Request(
            url=url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            parsed = json.loads(response.read().decode("utf-8"))
        if "errors" in parsed:
            if "handle" in json.dumps(parsed["errors"]).lower():
                alt_handle = f"{handle}-{abs(hash(payload['topic_key'])) % 10000}"
                body["article"]["handle"] = alt_handle
                retry_request = urllib.request.Request(
                    url=url,
                    data=json.dumps(body).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "X-Shopify-Access-Token": self.access_token,
                    },
                    method="POST",
                )
                with urllib.request.urlopen(retry_request, timeout=30) as retry_response:
                    parsed = json.loads(retry_response.read().decode("utf-8"))
        article = parsed.get("article", {})
        return ShopifyPublishResult(
            status="published",
            article_id=str(article.get("id")) if article.get("id") is not None else None,
            url=article.get("admin_graphql_api_id"),
            raw_response=parsed,
        )


class ShopifyGraphQLPublisher:
    def __init__(self, store: str, access_token: str, api_version: str, blog_id: str) -> None:
        self.store = store
        self.access_token = access_token
        self.api_version = api_version
        self.blog_id = blog_id

    def publish_draft(self, payload: Dict) -> ShopifyPublishResult:
        query = """
            mutation CreateArticle($article: ArticleCreateInput!) {
              articleCreate(article: $article) {
                article {
                  id
                  title
                  handle
                  summary
                  blog {
                    id
                  }
                }
                userErrors {
                  field
                  message
                }
              }
            }
        """
        variables = {
            "article": {
                "blogId": self._to_blog_gid(self.blog_id),
                "title": payload["title"],
                "handle": payload["handle"],
                "author": {"name": payload["author"]},
                "body": payload["body_html"],
                "summary": payload["excerpt"],
                "isPublished": False,
                "tags": payload["tags"],
                "metafields": [
                    {
                        "namespace": "global",
                        "key": "title_tag",
                        "value": payload["seo_title"],
                        "type": "single_line_text_field",
                    },
                    {
                        "namespace": "global",
                        "key": "description_tag",
                        "value": payload["seo_description"],
                        "type": "single_line_text_field",
                    },
                    {
                        "namespace": "heyup_automation",
                        "key": "topic_key",
                        "value": payload["topic_key"],
                        "type": "single_line_text_field",
                    },
                    {
                        "namespace": "heyup_automation",
                        "key": "risk_flags",
                        "value": json.dumps(payload["risk_flags"]),
                        "type": "json",
                    },
                    {
                        "namespace": "heyup_automation",
                        "key": "source_manifest_summary",
                        "value": json.dumps(payload["source_manifest_summary"]),
                        "type": "json",
                    },
                ],
            }
        }
        parsed = self._graphql_request(query, variables)
        create_payload = parsed.get("data", {}).get("articleCreate", {})
        user_errors = create_payload.get("userErrors", [])
        if user_errors and self._has_handle_conflict(user_errors):
            variables["article"]["handle"] = f"{payload['handle']}-{abs(hash(payload['topic_key'])) % 10000}"
            parsed = self._graphql_request(query, variables)
            create_payload = parsed.get("data", {}).get("articleCreate", {})
            user_errors = create_payload.get("userErrors", [])
        if user_errors:
            return ShopifyPublishResult(status="failed", raw_response=parsed)
        article = create_payload.get("article", {})
        return ShopifyPublishResult(
            status="published",
            article_id=article.get("id"),
            url=article.get("id"),
            raw_response=parsed,
        )

    def _graphql_request(self, query: str, variables: Dict) -> Dict:
        url = f"https://{self.store}/admin/api/{self.api_version}/graphql.json"
        request = urllib.request.Request(
            url=url,
            data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def _to_blog_gid(self, blog_id: str) -> str:
        if blog_id.startswith("gid://shopify/Blog/"):
            return blog_id
        return f"gid://shopify/Blog/{blog_id}"

    def _has_handle_conflict(self, user_errors: list) -> bool:
        serialized = json.dumps(user_errors).lower()
        return "handle" in serialized
