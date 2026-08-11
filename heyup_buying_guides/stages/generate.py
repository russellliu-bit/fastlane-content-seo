from __future__ import annotations

from typing import Tuple

from ..config import WorkflowConfig
from ..llm import StubLLMClient, build_llm_client
from ..prompts import render_prompt
from ..schemas import ArticleBrief, GeneratedArticle


def generate_article_json(brief: ArticleBrief, config: WorkflowConfig) -> Tuple[GeneratedArticle, str]:
    prompt_name = "comparison_roundup.txt" if brief.article_type == "comparison_roundup" else "buying_guide.txt"
    prompt = render_prompt(
        prompt_name,
        {
            "category": brief.category,
            "keyword": brief.keyword,
            "angle": brief.angle,
            "article_type": brief.article_type,
            "comparison_period": brief.comparison_period,
        },
    )
    client = build_llm_client(config)
    if isinstance(client, StubLLMClient):
        article = client.generate_article(brief)
    else:
        article = client.generate_article(brief, prompt)
    return article, prompt
