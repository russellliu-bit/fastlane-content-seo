from __future__ import annotations

from typing import List

from ..schemas import ArticleBrief, GeneratedArticle


def validate_article(article: GeneratedArticle, brief: ArticleBrief, min_products: int) -> List[str]:
    errors: List[str] = []
    required_sections = set(brief.must_have_sections) - {"disclosure", "intro", "faq", "ranked_product_sections", "recommended_products"}
    present_sections = {section.get("type") for section in article.sections}
    if not article.disclosure:
        errors.append("Disclosure block is required.")
    if len(article.affiliate_slots) == 0:
        errors.append("At least one affiliate slot is required.")
    if len(article.products) < min_products:
        errors.append(f"At least {min_products} products are required.")
    if article.article_type != brief.article_type:
        errors.append("Article type does not match brief.")
    if article.topic_key != brief.topic_key:
        errors.append("Topic key does not match brief.")
    if not article.intro:
        errors.append("Intro is required.")
    missing_sections = sorted(required_sections - present_sections)
    if missing_sections:
        errors.append(f"Missing required sections: {', '.join(missing_sections)}")
    if article.article_type == "comparison_roundup":
        for product in article.products:
            for key in ("best_for", "why_it_made_the_list", "pros", "cons", "affiliate_slot", "evidence_summary", "evidence_ids"):
                if not product.get(key):
                    errors.append(f"Comparison product is missing required field: {key}")
    else:
        for product in article.products:
            for key in ("who_it_is_for", "why_consider_it", "watch_out_for", "affiliate_slot", "evidence_ids"):
                if not product.get(key):
                    errors.append(f"Buying guide product is missing required field: {key}")
    if len(article.faq) == 0:
        errors.append("FAQ is required.")
    for item in article.faq:
        if not item.get("evidence_ids"):
            errors.append("FAQ item is missing evidence_ids")
    if not article.source_manifest:
        errors.append("Source manifest is required.")
    if not article.claim_references:
        errors.append("Claim references are required.")
    return errors
