from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from ..schemas import ArticleBrief, CandidateProduct, TopicCandidate


def build_article_brief(
    article_type: str,
    category: str,
    selected_products: List[CandidateProduct],
    affiliate_mode: str,
    topic: Optional[TopicCandidate] = None,
) -> ArticleBrief:
    month_year = datetime.utcnow().strftime("%B %Y")
    if article_type == "comparison_roundup":
        titles = topic.title_hypotheses if topic and topic.title_hypotheses else [f"Best {category} Picks for {month_year}"]
        sections = [
            "last_updated",
            "disclosure",
            "intro",
            "how_we_picked",
            "quick_picks_summary",
            "ranked_product_sections",
            "who_should_buy_what",
            "faq",
        ]
        keyword = topic.keyword if topic else f"best {category.lower()} {datetime.utcnow().year}"
        angle = topic.signal_summary if topic and topic.signal_summary else f"Evidence-backed shortlist for {category.lower()} buyers"
    else:
        titles = topic.title_hypotheses if topic and topic.title_hypotheses else [f"How to Choose {category} in {month_year}"]
        sections = [
            "last_updated",
            "disclosure",
            "intro",
            "what_to_consider",
            "how_to_compare_options",
            "common_mistakes",
            "recommended_products",
            "faq",
        ]
        keyword = topic.keyword if topic else f"how to choose {category.lower()}"
        angle = topic.signal_summary if topic and topic.signal_summary else f"Practical buying guide for {category.lower()}"

    return ArticleBrief(
        topic_key=topic.topic_key if topic else f"{category.lower()}-{article_type}",
        article_type=article_type,
        category=category,
        keyword=keyword,
        angle=angle,
        title_candidates=titles,
        comparison_period=month_year,
        selected_products=selected_products,
        must_have_sections=sections,
        disclosure_required=True,
        affiliate_mode=affiliate_mode,
    )
