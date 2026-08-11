from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import RunReport, TopicCandidate
from .utils import ensure_dir, utc_now_iso


class StateStore:
    def __init__(self, db_path: Path) -> None:
        ensure_dir(db_path.parent)
        self.db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS discovery_runs (
                    run_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    topic_count INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS topic_candidates (
                    topic_key TEXT NOT NULL,
                    discovery_run_id TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    article_type TEXT NOT NULL,
                    draftability_score REAL NOT NULL,
                    status TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (topic_key, discovery_run_id)
                );
                CREATE TABLE IF NOT EXISTS article_runs (
                    run_id TEXT PRIMARY KEY,
                    topic_key TEXT NOT NULL,
                    article_title TEXT NOT NULL,
                    article_type TEXT NOT NULL,
                    quality_score REAL NOT NULL,
                    validation_status TEXT NOT NULL,
                    shopify_status TEXT NOT NULL,
                    shopify_article_id TEXT,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS publication_attempts (
                    run_id TEXT PRIMARY KEY,
                    topic_key TEXT NOT NULL,
                    status TEXT NOT NULL,
                    target TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def save_discovery_run(self, run_id: str, status: str, topics: List[TopicCandidate]) -> None:
        payload = [topic.to_dict() for topic in topics]
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO discovery_runs (run_id, started_at, status, topic_count, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, now, status, len(topics), json.dumps(payload)),
            )
            for topic in topics:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO topic_candidates
                    (topic_key, discovery_run_id, keyword, article_type, draftability_score, status, payload_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic.topic_key,
                        run_id,
                        topic.keyword,
                        topic.article_type,
                        topic.draftability_score,
                        topic.status,
                        json.dumps(topic.to_dict()),
                        now,
                    ),
                )

    def get_top_topics(self, limit: int = 10, min_score: float = 0.0) -> List[TopicCandidate]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_json FROM topic_candidates
                WHERE status = 'ready' AND draftability_score >= ?
                ORDER BY draftability_score DESC, created_at DESC
                LIMIT ?
                """,
                (min_score, limit),
            ).fetchall()
        return [self._topic_from_row(row["payload_json"]) for row in rows]

    def get_recent_topic_runs(self, topic_key: str, limit: int = 5) -> List[Dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload_json FROM article_runs
                WHERE topic_key = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (topic_key, limit),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def save_article_run(self, report: RunReport) -> None:
        payload = report.to_dict()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO article_runs
                (run_id, topic_key, article_title, article_type, quality_score, validation_status, shopify_status, shopify_article_id, created_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.run_id,
                    report.topic_key,
                    report.article_title,
                    report.article_type,
                    report.quality_score,
                    report.validation_status,
                    report.shopify_status,
                    report.shopify_article_id,
                    utc_now_iso(),
                    json.dumps(payload),
                ),
            )

    def save_publication_attempt(self, run_id: str, topic_key: str, status: str, target: str, payload: Dict) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO publication_attempts
                (run_id, topic_key, status, target, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (run_id, topic_key, status, target, json.dumps(payload), utc_now_iso()),
            )

    def _topic_from_row(self, payload_json: str) -> TopicCandidate:
        payload = json.loads(payload_json)
        from .schemas import CandidateProduct

        payload["candidate_products"] = [CandidateProduct(**item) for item in payload.get("candidate_products", [])]
        return TopicCandidate(**payload)
