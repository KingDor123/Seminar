import os
import logging
from typing import Optional, List, Dict, Any

import asyncpg
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = logging.getLogger(__name__)

_db_pool: Optional[asyncpg.pool.Pool] = None


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
    Aggregates global stats for the dashboard.
    """
    pool = await _get_db_pool()
    
    try:
        # 1. Overview Stats
        # Note: 'messages' table might not exist if using 'session_messages' or similar. 
        # Checking conversation.py: POST to /chat/sessions/{id}/messages. 
        # Backend likely maps this to a 'messages' table.
        # We will assume standard tables: 'sessions', 'messages'.
        
        # Total Sessions
        total_sessions = await pool.fetchval("SELECT COUNT(*) FROM sessions")
        
        # Total Messages
        total_messages = await pool.fetchval("SELECT COUNT(*) FROM messages")
        
        # 2. Sentiment Breakdown (using 'sentiment' column in messages if it exists, or session_metrics)
        # Strategy: Use session_metrics for aggregated sentiment if per-message sentiment isn't stored directly
        # or assuming messages has a 'sentiment' column. 
        # Let's use 'session_metrics' table which we know exists from the summary endpoint.
        # We'll approximate based on 'sentiment' metric entries.
        
        sentiment_rows = await pool.fetch("""
            SELECT 
                CASE 
                    WHEN metric_value > 0.3 THEN 'Positive'
                    WHEN metric_value < -0.3 THEN 'Negative'
                    ELSE 'Neutral'
                END as label,
                COUNT(*) as count
            FROM session_metrics 
            WHERE metric_name = 'sentiment'
            GROUP BY label
        """)
        
        sentiment_breakdown = {row['label']: row['count'] for row in sentiment_rows}
        
        # Ensure keys exist
        sentiment_stats = {
            "Positive": sentiment_breakdown.get("Positive", 0),
            "Neutral": sentiment_breakdown.get("Neutral", 0),
            "Negative": sentiment_breakdown.get("Negative", 0)
        }

        # 3. Recent Activity
        recent_rows = await pool.fetch("""
            SELECT id, scenario_id, start_time 
            FROM sessions 
            ORDER BY start_time DESC 
            LIMIT 5
        """)
        
        recent_activity = [
            {
                "id": r["id"],
                "scenario": r["scenario_id"],
                "date": r["start_time"].isoformat() if r["start_time"] else None
            }
            for r in recent_rows
        ]

        return {
            "overview": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_score": 75 # Placeholder until global score logic is refined
            },
            "sentiment": sentiment_stats,
            "recent_activity": recent_activity
        }

    except Exception as e:
        logger.error(f"Dashboard Data Error: {e}")
        # Return fallback zeros on error to prevent frontend crash
        return {
            "overview": {"total_sessions": 0, "total_messages": 0, "avg_score": 0},
            "sentiment": {"Positive": 0, "Neutral": 0, "Negative": 0},
            "recent_activity": []
        }


@router.get("/summary")
async def get_sessions_summary(user_id: Optional[int] = Query(default=None)) -> List[Dict[str, Any]]:
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
    except Exception as exc:
        # Don't crash, just return empty
        logger.error(f"Summary Fetch Error: {exc}")
        return []

    summaries: List[Dict[str, Any]] = []
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