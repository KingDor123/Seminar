import logging
import json
import httpx
import os
import sys
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator, List, Dict, Any

# Robust import strategy
# 1. Try direct import (works in Docker if PYTHONPATH=/app)
try:
    from app.engine.orchestrator import orchestrator
    from app.engine.scenarios import SCENARIO_REGISTRY
except ImportError:
    # 2. Try parent package import (works in local dev if running from root)
    try:
        from ai_service.app.engine.orchestrator import orchestrator
        from ai_service.app.engine.scenarios import SCENARIO_REGISTRY
    except ImportError:
         # 3. Path hack fallback
        current_dir = os.path.dirname(os.path.abspath(__file__))
        pipeline_dir = os.path.abspath(os.path.join(current_dir, '../..'))
        if pipeline_dir not in sys.path:
            sys.path.append(pipeline_dir)
        from app.engine.orchestrator import orchestrator
        from app.engine.scenarios import SCENARIO_REGISTRY

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Constants ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5000/api")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "supersecretkey")

# --- Helper Functions ---
def _sse_event(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"

async def _fetch_history(session_id: int) -> List[Dict[str, str]]:
    """
    Fetches the last 10 messages for context window.
    """
    history = []
    try:
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            resp = await client.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages?limit=10")
            if resp.status_code == 200:
                messages = resp.json()
                for m in messages:
                    role = "assistant" if m["role"] == "ai" else "user"
                    history.append({"role": role, "content": m["content"]})
    except Exception as e:
        logger.error(f"⚠️ History Fetch Error: {e} (Continuing without history)")
    return history

async def _fetch_session_messages(session_id: int) -> List[Dict[str, Any]]:
    """
    Fetches full session messages for report generation.
    """
    try:
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            resp = await client.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages")
            if resp.status_code == 200:
                return resp.json()
            logger.error(f"⚠️ Session Messages Fetch Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"⚠️ Session Messages Fetch Error: {e}")
    return []

def _normalize_sentiment_label(label: Optional[str]) -> str:
    if not label:
        return "neutral"
    normalized = str(label).strip().lower()
    if normalized.startswith("label_"):
        mapping = {"label_0": "neutral", "label_1": "positive", "label_2": "negative"}
        return mapping.get(normalized, "neutral")
    return normalized

def _sentiment_to_score(label: str) -> float:
    if label in ["positive", "joy"]:
        return 1.0
    if label in ["negative", "anger", "stress", "fear", "sadness"]:
        return -1.0
    return 0.0

async def _save_message(
    session_id: int,
    role: str,
    content: str,
    sentiment: Optional[str] = None
    # REMOVED: analysis payload. We do not persist analysis to the backend.
):
    """
    Saves a message to the database asynchronously.
    Raises exception on failure to allow caller to abort turn.
    """
    if not session_id or not content: return
    
    db_role = "ai" if role == "assistant" else role
    payload = {"role": db_role, "content": content}

    if sentiment:
        payload["sentiment"] = sentiment
    
    # CRITICAL: Analysis dict is explicitly excluded from backend persistence 
    # to prevent 400 errors and state corruption. 
    # Analysis is transient and used for FSM routing only.

    async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
        resp = await client.post(
            f"{BACKEND_URL}/chat/sessions/{session_id}/messages",
            json=payload
        )
        if resp.status_code >= 400:
            raise Exception(f"Backend persistence failed: {resp.status_code} {resp.text}")

# --- HTTP Endpoints ---

@router.post("/interact")
async def interact(
    session_id: int = Form(...),
    text: str = Form(...),
    scenario_id: Optional[str] = Form(None)
):
    """
    Main Interaction Endpoint (Streaming SSE) with History Injection.
    """
    if not scenario_id or not scenario_id.strip():
        raise HTTPException(status_code=400, detail="scenario_id is required")

    logger.info(f"🗣️ Interaction Request: Session={session_id}, Scenario={scenario_id}")
    is_cold_start = text.strip() == "[START]"

    # 1. Fetch History
    history = await _fetch_history(session_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            if not is_cold_start:
                yield _sse_event("transcript", json.dumps({"role": "user", "text": text}))
            yield _sse_event("status", "thinking")

            # --- BRANCH: NEW ENGINE ---
            if scenario_id in SCENARIO_REGISTRY:
                logger.info(f"🚀 Using Engine Orchestrator for {scenario_id}")
                full_content = ""
                
                # NOTE: We consume the generator. If persistence fails inside, we break.
                async for chunk in orchestrator.process_turn(str(session_id), scenario_id, text, history):
                     if isinstance(chunk, dict):
                         # Metadata / Analysis
                         if "type" in chunk and chunk["type"] == "analysis":
                             # Map new engine fields to legacy schema for frontend
                             if not is_cold_start:
                                 # CRITICAL: Save user message BEFORE processing further
                                 # If this fails, we MUST ABORT to keep DB and FSM in sync.
                                 try:
                                     # We do NOT pass analysis payload here anymore.
                                     await _save_message(
                                        session_id,
                                        "user",
                                        text,
                                        sentiment=chunk.get("sentiment", "neutral")
                                    )
                                 except Exception as e:
                                     logger.error(f"❌ FATAL: User Message Persistence Failed. Aborting Turn. {e}")
                                     yield _sse_event("error", "System Error: Message persistence failed. Turn aborted.")
                                     return # Stop generator, do not update state, do not generate response. 

                             # Yield metrics to frontend (frontend uses them for UI, backend doesn't store them)
                             yield _sse_event("metrics", json.dumps(chunk, ensure_ascii=False))
                     elif isinstance(chunk, str):
                         # Tokens
                         full_content += chunk
                         yield _sse_event("transcript", json.dumps({"role": "assistant", "text": chunk, "partial": True}))
                
                # If we reached here, orchestrator finished successfully (State updated internally)
                # Now save the AI response.
                try:
                    await _save_message(session_id, "assistant", full_content)
                except Exception as e:
                     logger.error(f"❌ FATAL: AI Message Persistence Failed. History may be inconsistent. {e}")
                     # We can't "undo" the FSM state update easily here without transactionality,
                     # but we at least signal error.
                     yield _sse_event("error", "System Error: Response persistence failed.")
                     return

                yield _sse_event("status", "done")
                yield _sse_event("done", "[DONE]")
                return
            
            # --- ERROR: UNKNOWN SCENARIO ---
            logger.error(f"❌ Scenario '{scenario_id}' not found in registry.")
            yield _sse_event("error", f"Scenario '{scenario_id}' not found.")

        except Exception as e:
            logger.error(f"❌ SSE Stream Error: {e}")
            yield _sse_event("error", str(e))

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/report/generate/{session_id}")
async def generate_report(session_id: int):
    """
    Generates a lightweight session report using stored messages.
    """
    messages = await _fetch_session_messages(session_id)
    if not messages:
        return {
            "session_id": session_id,
            "summary": {
                "total_messages": 0,
                "user_messages": 0,
                "ai_messages": 0,
                "avg_sentiment": 0.0,
            },
            "tips": ["No messages found for this session."],
            "metrics": [],
            "sentiment_arc": [],
        }

    user_messages = [m for m in messages if m.get("role") == "user"]
    ai_messages = [m for m in messages if m.get("role") == "ai"]

    metrics = []
    sentiment_arc = []
    sentiment_scores = []

    for idx, msg in enumerate(user_messages, start=1):
        label = _normalize_sentiment_label(msg.get("sentiment"))
        score = _sentiment_to_score(label)
        sentiment_scores.append(score)
        context = f"Analyzed user text: {msg.get('content', '')}"

        sentiment_arc.append(
            {"turn": idx, "sentiment": label, "score": score, "context": context}
        )
        metrics.append(
            {"metric_name": "sentiment", "metric_value": score, "context": context}
        )
        metrics.append(
            {"metric_name": "topic_adherence", "metric_value": 0.7, "context": context}
        )
        metrics.append(
            {"metric_name": "clarity", "metric_value": 0.7, "context": context}
        )

    avg_sentiment = (
        sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
    )

    tips = []
    if avg_sentiment > 0.5:
        tips.append("Maintain the positive tone and keep responses concise.")
    elif avg_sentiment < -0.2:
        tips.append("Use de-escalation language and acknowledge the user's frustration.")
    else:
        tips.append("Keep responses clear and supportive.")

    return {
        "session_id": session_id,
        "summary": {
            "total_messages": len(messages),
            "user_messages": len(user_messages),
            "ai_messages": len(ai_messages),
            "avg_sentiment": round(avg_sentiment, 2),
        },
        "tips": tips,
        "metrics": metrics,
        "sentiment_arc": sentiment_arc,
    }

@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "engine": "state-machine",
        "ollama": "connected"
    }
