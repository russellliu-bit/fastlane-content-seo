from __future__ import annotations

from typing import Dict, List

from .schemas import GeneratedArticle


def render_article_html(article: GeneratedArticle) -> str:
    parts: List[str] = [
        f"<article data-article-type=\"{article.article_type}\">",
        f"<h1>{article.title}</h1>",
        f"<p><strong>{article.disclosure}</strong></p>",
        f"<p>{article.intro}</p>",
    ]
    for section in article.sections:
        parts.append(_render_section(section))
    parts.append(_render_products(article))
    parts.append("<section><h2>FAQ</h2>")
    for item in article.faq:
        parts.append(f"<h3>{item['question']}</h3><p>{item['answer']}</p>")
        if item.get("evidence_ids"):
            parts.append(f"<p><small>Evidence: {', '.join(item['evidence_ids'])}</small></p>")
    parts.append("</section>")
    parts.append("</article>")
    return "\n".join(parts)


def _render_section(section: Dict) -> str:
    section_type = section["type"]
    if section_type == "last_updated":
        return f"<p><em>Last updated: {section['content']}</em></p>"
    if section_type in {"how_we_picked", "how_to_compare_options", "who_should_buy_what"}:
        return f"<section><h2>{_title(section_type)}</h2><p>{section['content']}</p></section>"
    if section_type in {"quick_picks_summary", "what_to_consider", "common_mistakes"}:
        parts = [f"<section><h2>{_title(section_type)}</h2>"]
        parts.append("<ul>")
        for item in section.get("items", []):
            parts.append(f"<li>{item}</li>")
        parts.append("</ul>")
        parts.append("</section>")
        return "\n".join(parts)
    return ""


def _title(value: str) -> str:
    return value.replace("_", " ").title()


def _render_products(article: GeneratedArticle) -> str:
    if article.article_type == "comparison_roundup":
        parts = ["<section><h2>Ranked Product Sections</h2>"]
        for index, item in enumerate(article.products, start=1):
            affiliate_url = item.get("affiliate_url", "#")
            parts.append("<div class=\"product-card\">")
            parts.append(f"<h3>{index}. {item.get('product_name', '')}</h3>")
            parts.append(f"<p><strong>Best For:</strong> {item.get('best_for', '')}</p>")
            parts.append(f"<p><strong>Why It Made The List:</strong> {item.get('why_it_made_the_list', '')}</p>")
            parts.append("<p><strong>Pros:</strong></p><ul>")
            for entry in item.get("pros", []):
                parts.append(f"<li>{entry}</li>")
            parts.append("</ul>")
            parts.append("<p><strong>Cons:</strong></p><ul>")
            for entry in item.get("cons", []):
                parts.append(f"<li>{entry}</li>")
            parts.append("</ul>")
            parts.append("<p><strong>Key Specs:</strong></p><ul>")
            for entry in item.get("key_specs", []):
                parts.append(f"<li>{entry}</li>")
            parts.append("</ul>")
            parts.append(f"<p><strong>Evidence Summary:</strong> {item.get('evidence_summary', '')}</p>")
            if item.get("evidence_ids"):
                parts.append(f"<p><small>Evidence IDs: {', '.join(item.get('evidence_ids', []))}</small></p>")
            parts.append(f"<p><a href=\"{affiliate_url}\" rel=\"sponsored noopener\">{item.get('affiliate_slot', '')}</a></p>")
            parts.append("</div>")
        parts.append("</section>")
        return "\n".join(parts)

    parts = ["<section><h2>Recommended Products</h2>"]
    for item in article.products:
        affiliate_url = item.get("affiliate_url", "#")
        parts.append("<div class=\"product-card\">")
        parts.append(f"<h3>{item.get('product_name', '')}</h3>")
        parts.append(f"<p><strong>Who It Is For:</strong> {item.get('who_it_is_for', '')}</p>")
        parts.append(f"<p><strong>Why Consider It:</strong> {item.get('why_consider_it', '')}</p>")
        parts.append(f"<p><strong>Watch Out For:</strong> {item.get('watch_out_for', '')}</p>")
        if item.get("evidence_ids"):
            parts.append(f"<p><small>Evidence IDs: {', '.join(item.get('evidence_ids', []))}</small></p>")
        parts.append(f"<p><a href=\"{affiliate_url}\" rel=\"sponsored noopener\">{item.get('affiliate_slot', '')}</a></p>")
        parts.append("</div>")
    parts.append("</section>")
    return "\n".join(parts)
