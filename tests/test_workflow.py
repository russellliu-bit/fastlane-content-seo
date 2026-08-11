from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from heyup_buying_guides.amazon_resolver import resolve_amazon_links
from heyup_buying_guides.config import WorkflowConfig
from heyup_buying_guides.env import load_dotenv
from heyup_buying_guides.llm import GeminiLLMClient, OpenAICompatibleLLMClient, build_llm_client
from heyup_buying_guides.render import render_article_html
from heyup_buying_guides.orchestrator import _infer_category_from_keyword, run_workflow
from heyup_buying_guides.seed_query_generator import (
    _normalize_seed_topic_title,
    collect_market_signal,
    generate_seed_query_plan,
    seed_queries_to_discovery_queries,
)
from heyup_buying_guides.schemas import ArticleBrief, CandidateProduct, GeneratedArticle, TopicCandidate
from heyup_buying_guides.shopify import ShopifyGraphQLPublisher
from heyup_buying_guides.storage import StateStore


ROOT = Path(__file__).resolve().parents[1]
BASE_ENV = {
    key: value
    for key, value in os.environ.items()
    if key not in {
        "LLM_MODE",
        "LLM_PROVIDER",
        "LLM_MODEL",
        "LLM_BASE_URL",
        "LLM_API_KEY_ENV",
        "GEMINI_API_KEY",
        "FEISHU_WEBHOOK_URL",
        "PUBLISH_MODE",
        "SHOPIFY_STORE",
        "SHOPIFY_ACCESS_TOKEN",
        "SHOPIFY_BLOG_ID",
        "SHOPIFY_API_VERSION",
        "SERPER_API_KEY",
        "AMAZON_ENABLED",
        "AMAZON_DOMAIN",
        "AMAZON_ASSOCIATE_TAG",
        "AMAZON_MATCH_LIMIT",
    }
}


class WorkflowTest(unittest.TestCase):
    def test_workflow_generates_artifacts_and_stub_publish(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = {
                "artifact_root": str(Path(tmpdir) / "artifacts"),
                "source_catalog": str(ROOT / "codex_knowledge_base/14_external_sources_catalog.csv"),
                "allowed_domains": [
                    "toproductsreviews.com",
                    "www.bestproductsreviews.com",
                    "www.bestchoice.com"
                ],
                "category": "Audio",
                "article_type": "comparison_roundup",
                "affiliate_mode": "placeholder",
                "author": "Heyup Editorial",
                "publish_mode": "stub",
                "llm_mode": "stub",
                "fixtures_path": str(ROOT / "tests/fixtures/audio_comparison"),
                "max_products": 5,
                "min_products": 3,
                "discovery_enabled": True,
                "auto_select_topic": True
            }
            config_path.write_text(json.dumps(config))

            proc = subprocess.run(
                [sys.executable, "-m", "heyup_buying_guides.cli", "run", "--config", str(config_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={**BASE_ENV, "LLM_MODE": "stub", "PUBLISH_MODE": "stub", "FEISHU_WEBHOOK_URL": ""},
                check=True,
            )
            report = json.loads(proc.stdout)
            self.assertEqual(report["validation_status"], "passed")
            self.assertEqual(report["shopify_status"], "stubbed")
            self.assertTrue(report["shopify_article_id"])
            self.assertEqual(report["topic_key"], "best-wireless-headphones-2026")
            artifact_paths = report["artifact_paths"]
            self.assertTrue(any(path.endswith("generated_article.json") for path in artifact_paths))
            self.assertTrue(any(path.endswith("rendered_article.html") for path in artifact_paths))

    def test_buying_guide_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = {
                "artifact_root": str(Path(tmpdir) / "artifacts"),
                "source_catalog": str(ROOT / "codex_knowledge_base/14_external_sources_catalog.csv"),
                "allowed_domains": [
                    "toproductsreviews.com",
                    "www.bestproductsreviews.com"
                ],
                "category": "Audio",
                "article_type": "buying_guide",
                "affiliate_mode": "placeholder",
                "author": "Heyup Editorial",
                "publish_mode": "stub",
                "llm_mode": "stub",
                "fixtures_path": str(ROOT / "tests/fixtures/audio_comparison"),
                "max_products": 4,
                "min_products": 3,
                "discovery_enabled": False,
                "auto_select_topic": False
            }
            config_path.write_text(json.dumps(config))

            proc = subprocess.run(
                [sys.executable, "-m", "heyup_buying_guides.cli", "run", "--config", str(config_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={**BASE_ENV, "LLM_MODE": "stub", "PUBLISH_MODE": "stub", "FEISHU_WEBHOOK_URL": ""},
                check=True,
            )
            report = json.loads(proc.stdout)
            self.assertEqual(report["article_type"], "buying_guide")
            self.assertEqual(report["validation_status"], "passed")

    def test_discover_command_uses_fixture_topics(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config = {
                "artifact_root": str(Path(tmpdir) / "artifacts"),
                "state_db_path": str(Path(tmpdir) / "artifacts/state.db"),
                "source_catalog": str(ROOT / "codex_knowledge_base/14_external_sources_catalog.csv"),
                "allowed_domains": [
                    "toproductsreviews.com",
                    "www.bestproductsreviews.com",
                    "www.bestchoice.com"
                ],
                "category": "Audio",
                "llm_mode": "stub",
                "fixtures_path": str(ROOT / "tests/fixtures/audio_comparison")
            }
            config_path.write_text(json.dumps(config))
            proc = subprocess.run(
                [sys.executable, "-m", "heyup_buying_guides.cli", "discover", "--config", str(config_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                env={**BASE_ENV, "LLM_MODE": "stub"},
                check=True,
            )
            topics = json.loads(proc.stdout)
            self.assertEqual(topics[0]["topic_key"], "best-wireless-headphones-2026")
            self.assertEqual(topics[0]["status"], "ready")

    def test_state_store_persists_topic_and_article_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(Path(tmpdir) / "state.db")
            report = {
                "run_id": "run123",
                "topic_key": "best-wireless-headphones-2026",
                "article_title": "Best Audio Picks for March 2026",
                "article_type": "comparison_roundup",
                "quality_score": 0.8,
                "validation_status": "passed",
                "shopify_status": "stubbed",
                "shopify_article_id": "gid://shopify/Article/1",
                "created_at": "2026-03-11T00:00:00+00:00",
                "payload_json": "{}"
            }
            from heyup_buying_guides.schemas import RunReport

            run_report = RunReport(
                run_id="run123",
                started_at="2026-03-11T00:00:00+00:00",
                source_pages_count=0,
                candidate_count=4,
                selected_count=4,
                article_type="comparison_roundup",
                article_title="Best Audio Picks for March 2026",
                validation_status="passed",
                shopify_status="stubbed",
                shopify_article_id="gid://shopify/Article/1",
                topic_key="best-wireless-headphones-2026",
                topic_scores={"search_discovery_score": 0.9},
                quality_score=0.8,
                blocking_reasons=[],
                errors=[],
                artifact_paths=[],
            )
            store.save_article_run(run_report)
            recent = store.get_recent_topic_runs("best-wireless-headphones-2026")
            self.assertEqual(recent[0]["run_id"], "run123")

    def test_build_llm_client_requires_model_and_key(self) -> None:
        config = WorkflowConfig(
            artifact_root=ROOT / "artifacts",
            llm_mode="live",
            llm_provider="gemini",
        )
        with self.assertRaises(ValueError):
            build_llm_client(config)

    def test_gemini_client_parses_json_response(self) -> None:
        client = GeminiLLMClient(
            base_url="https://generativelanguage.googleapis.com/v1beta",
            model="gemini-2.5-flash",
            api_key="test-key",
            timeout_seconds=5,
        )
        brief = ArticleBrief(
            topic_key="best-wireless-headphones-2026",
            article_type="comparison_roundup",
            category="Audio",
            keyword="best audio 2026",
            angle="Evidence-backed shortlist",
            title_candidates=["Best Audio Picks for March 2026"],
            comparison_period="March 2026",
            selected_products=[
                CandidateProduct(
                    normalized_name="sony wh-1000xm5",
                    display_name="Sony WH-1000XM5",
                    brand="Sony",
                    category="Audio",
                    source_urls=["https://example.com/sony"],
                    origin_urls=["https://sony.com/wh1000xm5"],
                    specs={"type": "Wireless"},
                    positioning="A strong shortlist option backed by source evidence.",
                    pros_evidence=["Battery life is highlighted in source coverage."],
                    cons_evidence=["Premium pricing may be a tradeoff."],
                    best_for_signals=["buyers who want strong ANC"],
                    confidence_score=0.8,
                    dedupe_key="sony-wh-1000xm5",
                )
            ],
            must_have_sections=["intro"],
            disclosure_required=True,
            affiliate_mode="placeholder",
        )

        response_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "article_type": "comparison_roundup",
                                        "title": "Best Audio Picks for March 2026",
                                        "slug": "best-audio-picks-for-march-2026",
                                        "excerpt": "Short excerpt",
                                        "seo_title": "Best Audio Picks for March 2026",
                                        "seo_description": "SEO description",
                                        "intro": "Intro text",
                                        "sections": [{"type": "how_we_picked", "content": "Method"}],
                                        "products": [
                                            {
                                                "product_name": "Sony WH-1000XM5",
                                                "best_for": "buyers who want strong ANC",
                                                "why_it_made_the_list": "Evidence-backed pick",
                                                "pros": ["Battery life is highlighted in source coverage."],
                                                "cons": ["Premium pricing may be a tradeoff."],
                                                "key_specs": ["type: Wireless"],
                                                "evidence_summary": "Battery and pricing tradeoffs are visible in source evidence.",
                                                "affiliate_slot": "affiliate-slot-sony-wh-1000xm5"
                                            }
                                        ],
                                        "faq": [{"question": "Q", "answer": "A"}],
                                        "disclosure": "Disclosure text",
                                        "affiliate_slots": [
                                            {
                                                "slot_id": "affiliate-slot-sony-wh-1000xm5",
                                                "product_name": "Sony WH-1000XM5",
                                                "placeholder_text": "[Affiliate link placeholder for Sony WH-1000XM5]"
                                            }
                                        ],
                                        "source_manifest": [
                                            {
                                                "product_name": "Sony WH-1000XM5",
                                                "source_urls": ["https://example.com/sony"],
                                                "origin_urls": ["https://sony.com/wh1000xm5"]
                                            }
                                        ]
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(response_payload).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=FakeResponse()):
            article = client.generate_article(brief, "Prompt")

        self.assertEqual(article.title, "Best Audio Picks for March 2026")
        self.assertEqual(article.products[0]["product_name"], "Sony WH-1000XM5")

    def test_load_dotenv_reads_local_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            old_key = os.environ.get("GEMINI_API_KEY")
            old_mode = os.environ.get("LLM_MODE")
            env_path = Path(tmpdir) / ".env"
            env_path.write_text("GEMINI_API_KEY=test-key\nLLM_MODE=live\n")
            loaded = load_dotenv(env_path)
            self.assertEqual(loaded["GEMINI_API_KEY"], "test-key")
            self.assertEqual(loaded["LLM_MODE"], "live")
            if old_key is None:
                os.environ.pop("GEMINI_API_KEY", None)
            else:
                os.environ["GEMINI_API_KEY"] = old_key
            if old_mode is None:
                os.environ.pop("LLM_MODE", None)
            else:
                os.environ["LLM_MODE"] = old_mode

    def test_shopify_graphql_publisher_creates_draft_payload(self) -> None:
        publisher = ShopifyGraphQLPublisher(
            store="heyup-dev.myshopify.com",
            access_token="test-token",
            api_version="2025-01",
            blog_id="81610834074",
        )
        response_payload = {
            "data": {
                "articleCreate": {
                    "article": {
                        "id": "gid://shopify/Article/123",
                        "title": "Best Audio Picks for March 2026",
                        "handle": "best-audio-picks-for-march-2026",
                        "summary": "Summary",
                        "blog": {"id": "gid://shopify/Blog/81610834074"},
                    },
                    "userErrors": [],
                }
            }
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return json.dumps(response_payload).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as mocked:
            result = publisher.publish_draft(
                {
                    "title": "Best Audio Picks for March 2026",
                    "handle": "best-audio-picks-for-march-2026",
                    "body_html": "<p>Body</p>",
                    "excerpt": "Summary",
                    "tags": ["comparison_roundup", "buying-guide"],
                    "author": "Heyup Editorial",
                    "seo_title": "SEO title",
                    "seo_description": "SEO description",
                    "topic_key": "best-wireless-headphones-2026",
                    "risk_flags": [],
                    "source_manifest_summary": ["Sony WH-1000XM5"],
                }
            )
        self.assertEqual(result.status, "published")
        self.assertEqual(result.article_id, "gid://shopify/Article/123")
        request = mocked.call_args[0][0]
        body = json.loads(request.data.decode("utf-8"))
        self.assertEqual(body["variables"]["article"]["blogId"], "gid://shopify/Blog/81610834074")

    def test_amazon_resolver_populates_affiliate_url(self) -> None:
        article = GeneratedArticle(
            topic_key="best-noise-cancelling-headphones",
            article_type="buying_guide",
            title="Best Noise-Canceling Headphones",
            slug="best-noise-cancelling-headphones",
            excerpt="Excerpt",
            seo_title="SEO",
            seo_description="SEO desc",
            intro="Intro",
            sections=[],
            products=[
                {
                    "product_name": "Sony WH-1000XM5",
                    "who_it_is_for": "Travelers",
                    "why_consider_it": "ANC",
                    "watch_out_for": "Case size",
                    "affiliate_slot": "affiliate-slot-sony-wh-1000xm5",
                    "evidence_ids": ["sony-wh-1000xm5-source-1"],
                    "source_confidence": 0.8,
                }
            ],
            faq=[],
            disclosure="Disclosure",
            affiliate_slots=[
                {
                    "slot_id": "affiliate-slot-sony-wh-1000xm5",
                    "product_name": "Sony WH-1000XM5",
                    "placeholder_text": "[Affiliate link placeholder for Sony WH-1000XM5]",
                }
            ],
            source_manifest=[],
        )
        config = WorkflowConfig(
            artifact_root=Path("artifacts"),
            serper_api_key="test-serper",
            amazon_associate_tag="heyup-20",
            llm_cache_enabled=False,
            llm_mode="live",
        )
        organic = [
            {
                "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones - Amazon.com",
                "link": "https://www.amazon.com/Sony-WH-1000XM5-Canceling-Headphones/dp/B09XS7JWHH/ref=sr_1_1",
            }
        ]

        with patch("heyup_buying_guides.amazon_resolver.SerperClient.search", return_value=organic):
            resolved, matches = resolve_amazon_links(article, config)

        self.assertEqual(matches[0].status, "matched")
        self.assertIn("tag=heyup-20", resolved.products[0]["affiliate_url"])
        self.assertEqual(resolved.affiliate_slots[0]["asin"], "B09XS7JWHH")

    def test_render_uses_affiliate_url_when_available(self) -> None:
        article = GeneratedArticle(
            topic_key="best-noise-cancelling-headphones",
            article_type="buying_guide",
            title="Best Noise-Canceling Headphones",
            slug="best-noise-cancelling-headphones",
            excerpt="Excerpt",
            seo_title="SEO",
            seo_description="SEO desc",
            intro="Intro",
            sections=[],
            products=[
                {
                    "product_name": "Sony WH-1000XM5",
                    "who_it_is_for": "Travelers",
                    "why_consider_it": "ANC",
                    "watch_out_for": "Case size",
                    "affiliate_slot": "affiliate-slot-sony-wh-1000xm5",
                    "affiliate_url": "https://www.amazon.com/dp/B09XS7JWHH?tag=heyup-20",
                    "evidence_ids": ["sony-wh-1000xm5-source-1"],
                    "source_confidence": 0.8,
                }
            ],
            faq=[],
            disclosure="Disclosure",
            affiliate_slots=[],
            source_manifest=[],
        )

        html = render_article_html(article)
        self.assertIn('href="https://www.amazon.com/dp/B09XS7JWHH?tag=heyup-20"', html)

    def test_seed_query_generator_stub_plan(self) -> None:
        config = WorkflowConfig(
            artifact_root=Path("artifacts"),
            llm_mode="stub",
            article_type="comparison_roundup",
            raw_keyword="ai glasses",
            seed_query_count=3,
        )
        plan = generate_seed_query_plan("ai glasses", "comparison_roundup", config)
        queries = seed_queries_to_discovery_queries(plan)
        self.assertEqual(plan.raw_keyword, "ai glasses")
        self.assertTrue(plan.candidate_topics)
        self.assertEqual(len(queries), 1)
        self.assertTrue(plan.selected_topic.discovery_query)
        self.assertTrue(plan.selected_topic.editorial_title)
        self.assertIn("Best Ai Glasses", plan.selected_topic.editorial_title)
        self.assertLessEqual(len(plan.candidate_topics), 3)

    def test_seed_market_signal_uses_apify_async_flow(self) -> None:
        config = WorkflowConfig(
            artifact_root=Path("artifacts"),
            llm_mode="live",
            article_type="buying_guide",
            raw_keyword="laptop",
            apify_token="test-apify-token",
            llm_cache_enabled=False,
        )
        start_response = {"data": {"id": "run123", "status": "RUNNING"}}
        poll_response = {"data": {"id": "run123", "status": "SUCCEEDED", "defaultDatasetId": "dataset123"}}
        dataset_response = [
            {
                "relatedQueries_top": [{"query": "best laptop"}],
                "relatedQueries_rising": [{"query": "gaming laptop"}],
                "interestBySubregion": [{"geoName": "California"}],
            }
        ]
        with patch(
            "heyup_buying_guides.seed_query_generator._apify_api_request",
            side_effect=[start_response, poll_response, dataset_response],
        ):
            market_signal = collect_market_signal("laptop", config)
        self.assertEqual(market_signal["source"], "apify/google-trends-scraper")
        self.assertIn("best laptop", market_signal["top_queries"])

    def test_seed_topic_normalizes_years_and_titles(self) -> None:
        self.assertEqual(
            _normalize_seed_topic_title(
                "Best Laptops of 2024: Buying Advice",
                "buying_guide",
                "laptop",
                2026,
            ),
            "Best Laptops of 2026: Buying Advice",
        )
        self.assertEqual(
            _normalize_seed_topic_title(
                "The Comprehensive Laptop Buying Guide: How to Choose Your Next PC",
                "buying_guide",
                "laptop",
                2026,
            ),
            "The Comprehensive Laptop Buying Guide 2026: How to Choose Your Next PC",
        )
        self.assertEqual(
            _normalize_seed_topic_title(
                "Meta Ray-Ban vs. Xreal One",
                "comparison_roundup",
                "ai glasses",
                2026,
            ),
            "Meta Ray-Ban vs. Xreal One",
        )

    def test_run_workflow_uses_seed_discovery_when_raw_keyword_present(self) -> None:
        config = WorkflowConfig(
            artifact_root=Path("artifacts"),
            state_db_path=Path("artifacts/test_state.db"),
            llm_mode="stub",
            publish_mode="stub",
            discovery_enabled=True,
            auto_select_topic=False,
            raw_keyword="laptop",
            article_type="buying_guide",
        )
        topic = TopicCandidate(
            topic_key="best-laptops",
            category="Computing",
            intent_type="guide",
            article_type="buying_guide",
            keyword="best laptops",
            title_hypotheses=["Best Laptops of 2026"],
            signal_summary="Signal summary",
            signal_scores={"search_discovery_score": 0.9},
            candidate_products=[],
            source_urls=[],
            brand_origin_coverage=1.0,
            draftability_score=0.9,
            risk_flags=[],
            status="ready",
            rationale="Test topic",
        )
        article = GeneratedArticle(
            topic_key="best-laptops",
            article_type="buying_guide",
            title="Best Laptops of 2026",
            slug="best-laptops-of-2026",
            excerpt="Excerpt",
            seo_title="SEO",
            seo_description="SEO desc",
            intro="Intro",
            sections=[],
            products=[],
            faq=[],
            disclosure="Disclosure",
            affiliate_slots=[],
            source_manifest=[],
        )
        from heyup_buying_guides.seed_query_generator import SelectedSeedTopic, SeedQueryPlan

        seed_plan = SeedQueryPlan(
            raw_keyword="laptop",
            requested_article_type="buying_guide",
            data_source="stub_market_signal",
            market_signal={},
            candidate_topics=[],
            selected_topic=SelectedSeedTopic(
                discovery_query="best laptops 2026",
                editorial_title="The Best Laptops of 2026: A Complete Buying Guide",
                reason="Top seed topic",
                evidence=["best laptops 2026"],
            ),
        )
        with patch("heyup_buying_guides.orchestrator.run_discovery", return_value=([topic], seed_plan)) as mock_discovery, \
             patch("heyup_buying_guides.orchestrator.normalize_and_dedupe", return_value=[]), \
             patch("heyup_buying_guides.orchestrator.bind_candidate_evidence", return_value=[]), \
             patch("heyup_buying_guides.orchestrator.resolve_brand_origins", return_value=[]), \
             patch("heyup_buying_guides.orchestrator.enrich_candidates", return_value=[]), \
             patch("heyup_buying_guides.orchestrator.score_and_select", return_value=[]), \
             patch("heyup_buying_guides.orchestrator.build_article_brief") as mock_brief, \
             patch("heyup_buying_guides.orchestrator.generate_article_json", return_value=(article, "Prompt")), \
             patch("heyup_buying_guides.orchestrator.resolve_amazon_links", return_value=(article, [])), \
             patch("heyup_buying_guides.orchestrator.validate_article", return_value=[]), \
             patch("heyup_buying_guides.orchestrator.render_article_html", return_value="<p>Body</p>"), \
             patch("heyup_buying_guides.orchestrator.publish_draft") as mock_publish, \
             patch("heyup_buying_guides.orchestrator._notify_success"), \
             patch("heyup_buying_guides.orchestrator._notify_failure"):
            brief = ArticleBrief(
                topic_key="best-laptops",
                article_type="buying_guide",
                category="Computing",
                keyword="best laptops",
                angle="Guide",
                title_candidates=["Best Laptops of 2026"],
                comparison_period="March 2026",
                selected_products=[],
                must_have_sections=[],
                disclosure_required=True,
                affiliate_mode="placeholder",
            )
            mock_brief.return_value = brief
            class PublishResult:
                status = "stubbed"
                article_id = "gid://shopify/Article/1"
                url = ""
                raw_response = {}
            mock_publish.return_value = PublishResult()
            report = run_workflow(config)
        self.assertEqual(report.topic_key, "best-laptops")
        mock_discovery.assert_called_once()
        self.assertEqual(mock_brief.return_value.title_candidates[0], "The Best Laptops of 2026: A Complete Buying Guide")

    def test_infer_category_from_raw_keyword(self) -> None:
        self.assertEqual(_infer_category_from_keyword("laptop"), "Computing")
        self.assertEqual(_infer_category_from_keyword("noise cancelling headphones"), "Audio")
        self.assertEqual(_infer_category_from_keyword("ai glasses"), "Wearables")


if __name__ == "__main__":
    unittest.main()
