"""
Query Analytics Engine — Milestone 4.1
---------------------------------------
Records real query activity from the live pipeline, computes statistics,
and detects knowledge gaps from actual usage patterns.

Storage: SQLite database (analytics.db) — completely separate from the
         ChromaDB knowledge-base vector store so existing data is never
         polluted.
"""

import sqlite3
import json
import os
import time
import re
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

_HERE = os.path.dirname(os.path.abspath(__file__))
_M4_DIR = os.path.dirname(_HERE)
_DB_PATH = os.path.join(_M4_DIR, "data", "analytics.db")

STATUS_ANSWERED = "Answered"
STATUS_LOW_CONFIDENCE = "Low Confidence"
STATUS_UNANSWERED = "Unanswered"
STATUS_CLARIFICATION = "Clarification Required"
STATUS_RETRIEVAL_FAILED = "Retrieval Failed"

HIGH_CONFIDENCE_THRESHOLD = 0.60
LOW_CONFIDENCE_THRESHOLD = 0.30
GAP_FREQUENCY_THRESHOLD = 2

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS query_analytics (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp               REAL NOT NULL,
    timestamp_iso           TEXT NOT NULL,
    session_id              TEXT NOT NULL,
    query                   TEXT NOT NULL,
    resolved_query          TEXT,
    query_type              TEXT NOT NULL DEFAULT 'factual',
    classification_confidence REAL NOT NULL DEFAULT 0.0,
    resolution_path         TEXT,
    retrieved_docs          TEXT,
    retrieved_chunks        INTEGER NOT NULL DEFAULT 0,
    relevance_scores        TEXT,
    generated_response      TEXT,
    response_confidence     REAL NOT NULL DEFAULT 0.0,
    clarification_required  INTEGER NOT NULL DEFAULT 0,
    clarification_count     INTEGER NOT NULL DEFAULT 0,
    resolution_status       TEXT NOT NULL DEFAULT 'Unanswered',
    knowledge_domain        TEXT,
    was_answered            INTEGER NOT NULL DEFAULT 0,
    has_sufficient_retrieval INTEGER NOT NULL DEFAULT 0
);
"""


class QueryAnalyticsEngine:
    """Records, stores, and analyses real system query activity."""

    def __init__(self, db_path: str = _DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._ensure_schema()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _ensure_schema(self):
        with self._get_conn() as conn:
            conn.execute(_CREATE_TABLE_SQL)
            conn.commit()

    def record_query(self, pipeline_result: Dict[str, Any], session_id: str = "default") -> int:
        """Persist one query event derived from the orchestrator pipeline result."""
        now = time.time()
        timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

        query = pipeline_result.get("query", "")
        resolved_query = pipeline_result.get("refined_query") or query
        query_type = pipeline_result.get("query_type", "factual")
        classification_confidence = float(pipeline_result.get("classification_confidence", 0.0))

        is_clarification = bool(pipeline_result.get("is_clarification", False))
        citations = pipeline_result.get("citations", []) or []
        transparency = pipeline_result.get("transparency", {}) or {}
        confidence_dict = pipeline_result.get("confidence", {}) or {}
        response_confidence = float(confidence_dict.get("score", 0.0))
        answer = pipeline_result.get("answer", "") or ""

        retrieved_doc_names = list({c.get("document_name", "") for c in citations if c.get("document_name")})
        retrieved_chunks = len(citations)
        relevance_scores = [float(c.get("relevance_score", 0.0)) for c in citations]
        has_sufficient_retrieval = any(s >= LOW_CONFIDENCE_THRESHOLD for s in relevance_scores)

        clarification_count = 0
        for step in (pipeline_result.get("telemetry", {}) or {}).get("pipeline_steps", []):
            if step.get("agent") == "Clarification Agent":
                if step.get("details", {}).get("clarification_required"):
                    clarification_count += 1

        if is_clarification:
            resolution_path = "clarification"
        elif retrieved_chunks == 0:
            resolution_path = "retrieval_failed"
        else:
            resolution_path = "retrieval_generation"

        insufficient = transparency.get("insufficient_evidence", False)
        if is_clarification:
            resolution_status = STATUS_CLARIFICATION
        elif retrieved_chunks == 0:
            resolution_status = STATUS_RETRIEVAL_FAILED
        elif insufficient or response_confidence < LOW_CONFIDENCE_THRESHOLD:
            resolution_status = STATUS_UNANSWERED
        elif response_confidence < HIGH_CONFIDENCE_THRESHOLD:
            resolution_status = STATUS_LOW_CONFIDENCE
        else:
            resolution_status = STATUS_ANSWERED

        insufficient_markers = [
            "sufficient information was not found",
            "clarification requested",
            "insufficient supporting evidence",
        ]
        was_answered = 1
        for marker in insufficient_markers:
            if marker in answer.lower():
                was_answered = 0
                break
        if is_clarification:
            was_answered = 0

        knowledge_domain = self._infer_domain(query, retrieved_doc_names)

        record = {
            "timestamp": now,
            "timestamp_iso": timestamp_iso,
            "session_id": session_id,
            "query": query,
            "resolved_query": resolved_query,
            "query_type": query_type,
            "classification_confidence": classification_confidence,
            "resolution_path": resolution_path,
            "retrieved_docs": json.dumps(retrieved_doc_names),
            "retrieved_chunks": retrieved_chunks,
            "relevance_scores": json.dumps(relevance_scores),
            "generated_response": answer[:2000],
            "response_confidence": response_confidence,
            "clarification_required": 1 if is_clarification else 0,
            "clarification_count": clarification_count,
            "resolution_status": resolution_status,
            "knowledge_domain": knowledge_domain,
            "was_answered": was_answered,
            "has_sufficient_retrieval": 1 if has_sufficient_retrieval else 0,
        }

        cols = ", ".join(record.keys())
        placeholders = ", ".join(["?"] * len(record))
        with self._get_conn() as conn:
            cursor = conn.execute(
                f"INSERT INTO query_analytics ({cols}) VALUES ({placeholders})",
                list(record.values()),
            )
            conn.commit()
            return cursor.lastrowid

    def _infer_domain(self, query: str, doc_names: List[str]) -> str:
        domain_keywords = {
            "AI & Machine Learning": [
                "machine learning", "deep learning", "neural network", "ai", "nlp",
                "computer vision", "training", "model", "dataset", "algorithm",
                "classification", "regression", "clustering", "reinforcement",
                "transformer", "bert", "gpt", "llm", "embedding",
                "ai_ml", "machine_learning", "artificial_intelligence",
            ],
            "Cloud Computing": [
                "cloud", "iaas", "paas", "saas", "aws", "azure", "gcp",
                "kubernetes", "docker", "serverless", "virtualization",
                "cloud_computing", "cloudsync", "product_manual",
            ],
            "Cybersecurity": [
                "security", "firewall", "encryption", "vpn", "threat", "vulnerability",
                "malware", "ransomware", "phishing", "zero trust",
                "siem", "soc", "incident response", "cyberattack",
                "cybersecurity", "network_security",
            ],
            "HR & Policy": [
                "leave", "policy", "employee", "hr", "salary", "vacation",
                "benefits", "performance review", "onboarding", "hr_policy",
            ],
        }
        combined_text = (query + " " + " ".join(doc_names)).lower()
        best_domain = "General"
        best_score = 0
        for domain, keywords in domain_keywords.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            if score > best_score:
                best_score = score
                best_domain = domain
        return best_domain

    def get_summary_stats(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Returns high-level dashboard statistics."""
        where_clause, params = self._build_where(filters)
        sep = "AND" if where_clause else "WHERE"
        with self._get_conn() as conn:
            total = conn.execute(f"SELECT COUNT(*) FROM query_analytics {where_clause}", params).fetchone()[0]

            def count_status(s):
                return conn.execute(
                    f"SELECT COUNT(*) FROM query_analytics {where_clause} {sep} resolution_status = ?",
                    params + [s]
                ).fetchone()[0]

            answered = count_status(STATUS_ANSWERED)
            low_conf = count_status(STATUS_LOW_CONFIDENCE)
            unanswered = count_status(STATUS_UNANSWERED)
            clarification = count_status(STATUS_CLARIFICATION)
            retrieval_failed = count_status(STATUS_RETRIEVAL_FAILED)

            avg_conf_row = conn.execute(
                f"SELECT AVG(response_confidence) FROM query_analytics {where_clause}", params
            ).fetchone()[0]
            avg_confidence = round(float(avg_conf_row or 0.0), 4)

            type_rows = conn.execute(
                f"SELECT query_type, COUNT(*) as cnt FROM query_analytics {where_clause} GROUP BY query_type", params
            ).fetchall()
            query_type_dist = {row["query_type"]: row["cnt"] for row in type_rows}

            domain_rows = conn.execute(
                f"SELECT knowledge_domain, COUNT(*) as cnt FROM query_analytics {where_clause} GROUP BY knowledge_domain", params
            ).fetchall()
            domain_dist = {row["knowledge_domain"]: row["cnt"] for row in domain_rows}

            avg_chunks_row = conn.execute(
                f"SELECT AVG(retrieved_chunks) FROM query_analytics {where_clause}", params
            ).fetchone()[0]
            avg_chunks = round(float(avg_chunks_row or 0.0), 2)

            sufficient_ret = conn.execute(
                f"SELECT COUNT(*) FROM query_analytics {where_clause} {sep} has_sufficient_retrieval = ?",
                params + [1]
            ).fetchone()[0]

            high_conf = conn.execute(
                f"SELECT COUNT(*) FROM query_analytics {where_clause} {sep} response_confidence >= ?",
                params + [HIGH_CONFIDENCE_THRESHOLD]
            ).fetchone()[0]
            med_conf = conn.execute(
                f"SELECT COUNT(*) FROM query_analytics {where_clause} {sep} response_confidence >= ? AND response_confidence < ?",
                params + [LOW_CONFIDENCE_THRESHOLD, HIGH_CONFIDENCE_THRESHOLD]
            ).fetchone()[0]
            low_conf_cnt = conn.execute(
                f"SELECT COUNT(*) FROM query_analytics {where_clause} {sep} response_confidence < ?",
                params + [LOW_CONFIDENCE_THRESHOLD]
            ).fetchone()[0]

        resolution_rate = round(answered / total, 4) if total > 0 else 0.0
        knowledge_gap_count = unanswered + retrieval_failed

        return {
            "total_queries": total,
            "answered": answered,
            "answered_queries": answered,
            "low_confidence": low_conf,
            "unanswered": unanswered,
            "knowledge_gap_count": knowledge_gap_count,
            "resolution_rate": resolution_rate,
            "clarification_requests": clarification,
            "retrieval_failed": retrieval_failed,
            "average_confidence": avg_confidence,
            "by_domain": domain_dist,
            "by_type": query_type_dist,
            "by_confidence": {
                "High": high_conf,
                "Medium": med_conf,
                "Low": low_conf_cnt
            },
            "query_type_distribution": query_type_dist,
            "knowledge_domain_distribution": domain_dist,
            "retrieval_performance": {
                "average_chunks_retrieved": avg_chunks,
                "sufficient_retrieval_count": sufficient_ret,
                "sufficient_retrieval_rate": round(sufficient_ret / total, 4) if total > 0 else 0.0,
            },
        }

    def get_knowledge_gaps(self, min_frequency: int = GAP_FREQUENCY_THRESHOLD) -> List[Dict[str, Any]]:
        """Detects knowledge gaps from actual query data (not hardcoded)."""
        with self._get_conn() as conn:
            rows = conn.execute(
                """
                SELECT query, resolved_query, knowledge_domain, resolution_status,
                       response_confidence, retrieved_chunks
                FROM query_analytics
                WHERE (resolution_status = ? OR resolution_status = ?
                       OR (response_confidence < ? AND was_answered = 0))
                  AND clarification_required = 0
                ORDER BY timestamp DESC
                """,
                [STATUS_UNANSWERED, STATUS_RETRIEVAL_FAILED, LOW_CONFIDENCE_THRESHOLD],
            ).fetchall()

        if not rows:
            return []

        topic_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            q = (row["resolved_query"] or row["query"]).strip()
            topics = self._extract_topics(q)
            for topic in topics:
                key = topic.lower()
                if key not in topic_map:
                    topic_map[key] = {
                        "topic": topic,
                        "query_count": 0,
                        "domains": set(),
                        "sample_queries": [],
                        "avg_confidence": [],
                    }
                topic_map[key]["query_count"] += 1
                if row["knowledge_domain"]:
                    topic_map[key]["domains"].add(row["knowledge_domain"])
                if len(topic_map[key]["sample_queries"]) < 3:
                    topic_map[key]["sample_queries"].append(q)
                topic_map[key]["avg_confidence"].append(float(row["response_confidence"]))

        gaps = []
        for key, data in topic_map.items():
            if data["query_count"] >= min_frequency:
                avg_conf = round(sum(data["avg_confidence"]) / len(data["avg_confidence"]), 4)
                domain_str = list(data["domains"])[0] if data["domains"] else "General"
                gaps.append({
                    "topic": data["topic"].title(),
                    "frequency": data["query_count"],
                    "query_count": data["query_count"],
                    "average_confidence": avg_conf,
                    "domain": domain_str,
                    "domains": list(data["domains"]),
                    "sample_queries": data["sample_queries"],
                })

        gaps.sort(key=lambda x: x["query_count"], reverse=True)
        return gaps

    def _extract_topics(self, query: str) -> List[str]:
        """Extract meaningful topic keywords from a query string."""
        stop_words = {
            "what", "is", "are", "how", "does", "do", "tell", "me", "about",
            "a", "an", "the", "of", "for", "in", "on", "at", "to", "and",
            "or", "can", "you", "i", "my", "your", "its", "their", "there",
            "please", "could", "would", "should", "give", "explain",
            "describe", "compare", "difference", "between", "with", "from",
            "today", "current", "latest", "when", "where", "who", "which",
        }
        clean = re.sub(r"[^\w\s]", " ", query.lower())
        words = [w for w in clean.split() if w and w not in stop_words and len(w) > 2]
        topics = list(words)
        orig_words = re.sub(r"[^\w\s]", " ", query.lower()).split()
        orig_filtered = [w for w in orig_words if w not in stop_words and len(w) > 2]
        for i in range(len(orig_filtered) - 1):
            bigram = f"{orig_filtered[i]} {orig_filtered[i+1]}"
            topics.append(bigram)
        return list(set(topics))

    def get_recent_queries(self, limit: int = 50, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Returns the most recent query records."""
        where_clause, params = self._build_where(filters)
        with self._get_conn() as conn:
            rows = conn.execute(
                f"""
                SELECT id, timestamp, timestamp_iso, session_id, query, resolved_query,
                       query_type, classification_confidence, resolution_status,
                       knowledge_domain, response_confidence, retrieved_chunks,
                       retrieved_docs, relevance_scores, was_answered,
                       has_sufficient_retrieval, clarification_required
                FROM query_analytics
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params + [limit],
            ).fetchall()

        results = []
        for row in rows:
            d = dict(row)
            try:
                d["retrieved_docs"] = json.loads(d.get("retrieved_docs") or "[]")
            except Exception:
                d["retrieved_docs"] = []
            try:
                d["relevance_scores"] = json.loads(d.get("relevance_scores") or "[]")
            except Exception:
                d["relevance_scores"] = []

            conf_score = float(d.get("response_confidence", 0.0))
            if conf_score >= HIGH_CONFIDENCE_THRESHOLD:
                conf_level = "High"
            elif conf_score >= LOW_CONFIDENCE_THRESHOLD:
                conf_level = "Medium"
            else:
                conf_level = "Low"

            res_status = d.get("resolution_status", "Unanswered")
            if res_status == STATUS_ANSWERED:
                norm_status = "answered"
            elif res_status in (STATUS_UNANSWERED, STATUS_RETRIEVAL_FAILED):
                norm_status = "knowledge_gap"
            elif res_status == STATUS_CLARIFICATION:
                norm_status = "clarification_needed"
            else:
                norm_status = res_status.lower().replace(" ", "_")

            d["query_text"] = d.get("query", "")
            d["domain"] = d.get("knowledge_domain", "General")
            d["status"] = norm_status
            d["confidence_score"] = conf_score
            d["confidence_level"] = conf_level
            d["timestamp"] = d.get("timestamp_iso", "")
            results.append(d)
        return results

    def get_frequently_asked_topics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns the most frequently queried topics across all queries."""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT query, resolved_query FROM query_analytics ORDER BY timestamp DESC"
            ).fetchall()

        topic_counts: Dict[str, int] = {}
        for row in rows:
            q = (row["resolved_query"] or row["query"]).strip()
            topics = self._extract_topics(q)
            for t in topics:
                key = t.lower()
                topic_counts[key] = topic_counts.get(key, 0) + 1

        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        return [
            {"topic": t.title(), "count": c}
            for t, c in sorted_topics[:limit]
            if c > 0 and len(t) > 2
        ]

    get_frequent_topics = get_frequently_asked_topics

    def _build_where(self, filters: Optional[Dict[str, Any]]) -> tuple:
        """Builds a WHERE clause and params list from filter dict."""
        if not filters:
            return "", []

        clauses = []
        params = []

        domain_val = filters.get("knowledge_domain") or filters.get("domain")
        if domain_val:
            clauses.append("knowledge_domain = ?")
            params.append(domain_val)

        if filters.get("query_type"):
            clauses.append("query_type = ?")
            params.append(filters["query_type"])

        status_val = filters.get("resolution_status") or filters.get("status")
        if status_val:
            s_lower = status_val.lower()
            if s_lower == "answered":
                clauses.append("resolution_status = ?")
                params.append(STATUS_ANSWERED)
            elif s_lower in ["knowledge_gap", "unanswered"]:
                clauses.append("resolution_status IN (?, ?)")
                params.extend([STATUS_UNANSWERED, STATUS_RETRIEVAL_FAILED])
            elif s_lower in ["clarification_needed", "clarification"]:
                clauses.append("resolution_status = ?")
                params.append(STATUS_CLARIFICATION)
            else:
                clauses.append("resolution_status = ?")
                params.append(status_val)

        if filters.get("confidence_level"):
            level = filters["confidence_level"]
            if level == "High":
                clauses.append("response_confidence >= ?")
                params.append(HIGH_CONFIDENCE_THRESHOLD)
            elif level == "Medium":
                clauses.append("response_confidence >= ? AND response_confidence < ?")
                params.extend([LOW_CONFIDENCE_THRESHOLD, HIGH_CONFIDENCE_THRESHOLD])
            elif level == "Low":
                clauses.append("response_confidence < ?")
                params.append(LOW_CONFIDENCE_THRESHOLD)

        if filters.get("date_from"):
            clauses.append("timestamp >= ?")
            params.append(float(filters["date_from"]))
        if filters.get("date_to"):
            clauses.append("timestamp <= ?")
            params.append(float(filters["date_to"]))

        if clauses:
            return "WHERE " + " AND ".join(clauses), params
        return "", []

    def clear_all(self):
        """Clears all analytics records (for testing)."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM query_analytics")
            conn.commit()

