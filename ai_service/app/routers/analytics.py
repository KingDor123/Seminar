import os
import logging
from typing import Optional, List, Dict, Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query
from app.schemas import MessageRead  # Import for type hinting/validation concepts

router = APIRouter()
logger = logging.getLogger(__name__)

_db_pool: Optional[asyncpg.pool.Pool] = None


async def _column_exists(conn: asyncpg.Connection, table: str, column: str) -> bool:
    return await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = $1
              AND column_name = $2
        )
        """,
        table,
        column,
    )


async def _get_db_pool() -> asyncpg.pool.Pool:
    global _db_pool
    if _db_pool is None:
        try:
            logger.info("🔌 Connecting to Analytics DB...")
            _db_pool = await asyncpg.create_pool(
                host=os.getenv("DB_HOST", "db"),
                user=os.getenv("DB_USER", "softskill"),
                password=os.getenv("DB_PASSWORD", "supersecret"),
                database=os.getenv("DB_NAME", "softskill_db"),
                port=int(os.getenv("DB_PORT", "5432")),
                min_size=1,
                max_size=5
            )
            logger.info("✅ Analytics DB Connected.")
        except Exception as e:
            logger.error(f"❌ DB Connection Failed: {e}")
            raise e
    return _db_pool


@router.get("/dashboard")
async def get_dashboard_analytics():
    """
    Aggregates global stats for the dashboard using real DB data.
    """
    pool = await _get_db_pool()

    try:
        async with pool.acquire() as conn:
            counts = await conn.fetchrow(
                """
                SELECT
                    (SELECT COUNT(DISTINCT id) FROM sessions) AS total_sessions,
                    (SELECT COUNT(*) FROM messages) AS total_messages,
                    (SELECT COUNT(*) FROM messages WHERE role = 'user') AS total_user_messages
                """
            )
            total_sessions = int(counts["total_sessions"] or 0)
            total_messages = int(counts["total_messages"] or 0)
            total_user_messages = int(counts["total_user_messages"] or 0)

            sentiment_stats = {"positive": 0, "neutral": 0, "negative": 0}
            has_sentiment = await _column_exists(conn, "messages", "sentiment")
            if has_sentiment:
                sentiment_rows = await conn.fetch(
                    """
                    SELECT
                        CASE
                            WHEN label LIKE 'positive%' THEN 'positive'
                            WHEN label IN ('negative', 'stress', 'anger', 'fear') OR label LIKE 'negative%' THEN 'negative'
                            ELSE 'neutral'
                        END AS sentiment,
                        COUNT(*) AS count
                    FROM (
                        SELECT LOWER(COALESCE(sentiment::text, 'neutral')) AS label
                        FROM messages
                        WHERE role = 'user'
                    ) t
                    GROUP BY sentiment
                    """
                )
                for row in sentiment_rows:
                    sentiment_stats[row["sentiment"]] = int(row["count"])
            else:
                sentiment_stats["neutral"] = total_user_messages

            score_rows = await conn.fetch(
                """
                SELECT
                    s.id AS session_id,
                    COUNT(sm.id) AS metrics_count,
                    AVG(CASE WHEN sm.metric_name = 'fluency_score' THEN sm.metric_value END) AS avg_fluency,
                    AVG(CASE WHEN sm.metric_name = 'sentiment' THEN sm.metric_value END) AS avg_sentiment,
                    COALESCE(SUM(CASE WHEN sm.metric_name IN ('filler_count', 'filler_word_count') THEN sm.metric_value ELSE 0 END), 0) AS total_fillers
                FROM sessions s
                LEFT JOIN session_metrics sm ON sm.session_id = s.id
                GROUP BY s.id
                """
            )
            scores: List[int] = []
            for row in score_rows:
                if not row["metrics_count"]:
                    continue
                avg_fluency = float(row["avg_fluency"] or 0.0)
                avg_sentiment = float(row["avg_sentiment"] or 0.0)
                total_fillers = float(row["total_fillers"] or 0.0)
                score = 60 + min(20, (avg_fluency / 10) * 20) - (total_fillers * 2) + ((avg_sentiment + 1) * 10)
                score = max(0, min(100, round(score)))
                scores.append(score)

            avg_score = round(sum(scores) / len(scores)) if scores and total_messages > 0 else 0

            recent_rows = await conn.fetch(
                """
                SELECT id, scenario_id, start_time
                FROM sessions
                ORDER BY start_time DESC NULLS LAST
                LIMIT 5
                """
            )

            recent_activity = [
                {
                    "id": r["id"],
                    "scenario": r["scenario_id"],
                    "date": r["start_time"].isoformat() if r["start_time"] else None,
                }
                for r in recent_rows
            ]

        return {
            "overview": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_score": avg_score,
            },
            "sentiment": sentiment_stats,
            "recent_activity": recent_activity,
        }

    except Exception as e:
        logger.error(f"Dashboard Data Error: {e}")
        return {
            "overview": {"total_sessions": 0, "total_messages": 0, "avg_score": 0},
            "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
            "recent_activity": [],
        }

@router.get("/sessions_list")
async def get_sessions_list():
    """
    Returns a comprehensive list of all sessions with summary metadata.
    """
    pool = await _get_db_pool()
    try:
        async with pool.acquire() as conn:
            has_sentiment = await _column_exists(conn, "messages", "sentiment")
            if has_sentiment:
                sql = """
                    SELECT
                        s.id,
                        s.scenario_id,
                        s.start_time AS created_at,
                        COUNT(m.id) AS message_count,
                        (
                            SELECT sentiment
                            FROM messages m2
                            WHERE m2.session_id = s.id
                              AND m2.role = 'user'
                              AND m2.sentiment IS NOT NULL
                            ORDER BY m2.id DESC
                            LIMIT 1
                        ) AS last_sentiment
                    FROM sessions s
                    LEFT JOIN messages m ON m.session_id = s.id
                    GROUP BY s.id
                    ORDER BY s.start_time DESC NULLS LAST
                """
            else:
                sql = """
                    SELECT
                        s.id,
                        s.scenario_id,
                        s.start_time AS created_at,
                        COUNT(m.id) AS message_count,
                        NULL::text AS last_sentiment
                    FROM sessions s
                    LEFT JOIN messages m ON m.session_id = s.id
                    GROUP BY s.id
                    ORDER BY s.start_time DESC NULLS LAST
                """
            rows = await conn.fetch(sql)

        sessions = []
        for r in rows:
            raw_sent = r["last_sentiment"]
            overall_sentiment = "Neutral"
            if raw_sent is not None:
                raw_sent = str(raw_sent).lower()
                if "positive" in raw_sent:
                    overall_sentiment = "Positive"
                elif any(x in raw_sent for x in ["negative", "stress", "anger", "fear"]):
                    overall_sentiment = "Negative"

            sessions.append(
                {
                    "session_id": r["id"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else None,
                    "scenario_id": r["scenario_id"],
                    "message_count": r["message_count"],
                    "overall_sentiment": overall_sentiment,
                }
            )

        return sessions

    except Exception as e:
        logger.error(f"Session List Error: {e}")
        return []

@router.get("/summary")
async def get_sessions_summary(user_id: Optional[int] = Query(default=None)) -> List[Dict[str, Any]]:
    # ... (Existing logic for backward compatibility)
    pool = await _get_db_pool()
    where_clause = ""
    params = []
    if user_id is not None:
        where_clause = "WHERE s.user_id = $1"
        params.append(user_id)

    sql = f"""
        SELECT
            s.id AS session_id,
            s.start_time AS date,
            AVG(CASE WHEN sm.metric_name = 'fluency_score' THEN sm.metric_value END) AS avg_fluency,
            AVG(CASE WHEN sm.metric_name = 'sentiment' THEN sm.metric_value END) AS avg_sentiment,
            COALESCE(SUM(CASE WHEN sm.metric_name IN ('filler_count', 'filler_word_count') THEN sm.metric_value ELSE 0 END), 0) AS total_fillers
        FROM sessions s
        LEFT JOIN session_metrics sm ON sm.session_id = s.id
        {where_clause}
        GROUP BY s.id, s.start_time
        ORDER BY s.start_time DESC
    """
    try:
        rows = await pool.fetch(sql, *params)
        summaries = []
        for row in rows:
            avg_fluency = float(row["avg_fluency"] or 0.0)
            avg_sentiment = float(row["avg_sentiment"] or 0.0)
            total_fillers = float(row["total_fillers"] or 0.0)
            score = 60 + min(20, (avg_fluency / 10) * 20) - (total_fillers * 2) + ((avg_sentiment + 1) * 10)
            score = max(0, min(100, round(score)))
            summaries.append({
                "session_id": row["session_id"],
                "score": score,
                "fluency": round(avg_fluency, 2),
                "fillers": int(total_fillers),
                "date": row["date"].isoformat() if row["date"] else None
            })
        return summaries
    except Exception as exc:
        logger.error(f"Summary Fetch Error: {exc}")
        return []
