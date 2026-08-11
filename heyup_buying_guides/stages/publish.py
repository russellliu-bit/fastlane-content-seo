from __future__ import annotations

from typing import Dict

from ..config import WorkflowConfig
from ..schemas import GeneratedArticle
from ..shopify import ShopifyGraphQLPublisher, ShopifyRestPublisher, ShopifyPublishResult, StubShopifyPublisher


def publish_draft(article: GeneratedArticle, html: str, config: WorkflowConfig) -> ShopifyPublishResult:
    payload: Dict = {
        "title": article.title,
        "handle": article.slug,
        "body_html": html,
        "excerpt": article.excerpt,
        "tags": [article.article_type, "buying-guide", config.category.lower().replace(" ", "-"), "draft-auto-generated"],
        "author": config.author,
        "seo_title": article.seo_title,
        "seo_description": article.seo_description,
        "topic_key": article.topic_key,
        "risk_flags": article.risk_flags,
        "source_manifest_summary": [item["product_name"] for item in article.source_manifest],
    }
    if config.publish_mode == "rest":
        if not (config.shopify_store and config.shopify_access_token and config.blog_id):
            raise ValueError("shopify_store, shopify_access_token, and blog_id are required for rest publish mode.")
        publisher = ShopifyRestPublisher(
            store=config.shopify_store,
            access_token=config.shopify_access_token,
            api_version=config.shopify_api_version,
            blog_id=config.blog_id,
        )
    elif config.publish_mode == "graphql":
        if not (config.shopify_store and config.shopify_access_token and config.blog_id):
            raise ValueError("shopify_store, shopify_access_token, and blog_id are required for graphql publish mode.")
        publisher = ShopifyGraphQLPublisher(
            store=config.shopify_store,
            access_token=config.shopify_access_token,
            api_version=config.shopify_api_version,
            blog_id=config.blog_id,
        )
    else:
        publisher = StubShopifyPublisher()
    return publisher.publish_draft(payload)
