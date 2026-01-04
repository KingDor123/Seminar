import logging
import json
import httpx
import os
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator, List, Dict, Any

import sys

# Robust import to handle both Docker (/app root) and Local (parent root) paths
try:
    from ai_service.pipeline import HybridPipeline
    from ai_service.app.engine.orchestrator import orchestrator
    from ai_service.app.engine.scenarios import SCENARIO_REGISTRY
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pipeline_dir = os.path.abspath(os.path.join(current_dir, '../..'))
    if pipeline_dir not in sys.path:
        sys.path.append(pipeline_dir)
    from pipeline import HybridPipeline
    from app.engine.orchestrator import orchestrator
    from app.engine.scenarios import SCENARIO_REGISTRY

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Constants ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5000/api")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "supersecretkey")

# --- Singleton Pipeline Initialization ---
_pipeline: Optional[HybridPipeline] = None

def get_pipeline() -> HybridPipeline:
    global _pipeline
    if _pipeline is None:
        try:
            logger.info("⚙️ Initializing HybridPipeline Singleton...")
            _pipeline = HybridPipeline() 
            logger.info("✅ HybridPipeline Ready.")
        except Exception as e:
            logger.critical(f"🔥 Pipeline Initialization Failed: {e}")
            raise e
    return _pipeline

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

async def _fetch_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    if not scenario_id:
        return None
    try:
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            resp = await client.get(f"{BACKEND_URL}/scenarios/{scenario_id}")
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                logger.warning(f"⚠️ Scenario not found: {scenario_id}")
                return None
            logger.error(f"⚠️ Scenario Fetch Failed: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"⚠️ Scenario Fetch Error: {e}")
    return None

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
    sentiment: Optional[str] = None,
    analysis: Optional[Dict[str, Any]] = None
):
    """
    Saves a message to the database asynchronously.
    """
    if not session_id or not content: return
    try:
        db_role = "ai" if role == "assistant" else role
        payload = {"role": db_role, "content": content}

        if sentiment:
            payload["sentiment"] = sentiment
        if analysis:
            payload["analysis"] = analysis

        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            await client.post(
                f"{BACKEND_URL}/chat/sessions/{session_id}/messages",
                json=payload
            )
    except Exception as e:
        logger.error(f"❌ DB Save Error: {e}")

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

    # 1. Fetch History
    history = await _fetch_history(session_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            yield _sse_event("transcript", json.dumps({"role": "user", "text": text}))
            yield _sse_event("status", "thinking")

            # --- BRANCH: NEW ENGINE ---
            if scenario_id in SCENARIO_REGISTRY:
                logger.info(f"🚀 Using Engine Orchestrator for {scenario_id}")
                full_content = ""
                analysis_payload: Optional[Dict[str, Any]] = None
                
                async for chunk in orchestrator.process_turn(str(session_id), scenario_id, text, history):
                     if isinstance(chunk, dict):
                         # Metadata / Analysis
                         if "type" in chunk and chunk["type"] == "analysis":
                             analysis_payload = chunk
                             # Map new engine fields to legacy schema for frontend
                             await _save_message(
                                session_id,
                                "user",
                                text,
                                sentiment=chunk.get("sentiment", "neutral"),
                                analysis=chunk
                            )
                             yield _sse_event("metrics", json.dumps(chunk, ensure_ascii=False))
                     elif isinstance(chunk, str):
                         # Tokens
                         full_content += chunk
                         yield _sse_event("transcript", json.dumps({"role": "assistant", "text": chunk, "partial": True}))
                
                if analysis_payload is None:
                    # Fallback save if analysis failed
                    await _save_message(session_id, "user", text)
                
                await _save_message(session_id, "assistant", full_content)
                yield _sse_event("status", "done")
                yield _sse_event("done", "[DONE]")
                return

            # --- BRANCH: LEGACY PIPELINE ---
            logger.info(f"🐢 Using Legacy HybridPipeline for {scenario_id}")
            scenario = await _fetch_scenario(scenario_id.strip())
            if not scenario:
                yield _sse_event("error", "Invalid scenario_id")
                return

            persona_prompt = scenario.get("persona_prompt")
            scenario_goal = scenario.get("scenario_goal")
            difficulty = str(scenario.get("difficulty") or "normal")
            
            pipeline = get_pipeline()
            full_content = ""
            detected_sentiment = "neutral" 
            analysis_payload = None

            async for chunk in pipeline.process_user_message_stream(
                text=text,
                base_system_prompt=persona_prompt,
                difficulty_level=difficulty,
                scenario_goal=scenario_goal,
                history=history
            ):
                if isinstance(chunk, dict):
                    if "sentiment" in chunk:
                        detected_sentiment = chunk["sentiment"]
                        if analysis_payload is None:
                            analysis_payload = chunk
                            await _save_message(
                                session_id,
                                "user",
                                text,
                                sentiment=detected_sentiment,
                                analysis=analysis_payload
                            )
                        yield _sse_event("metrics", json.dumps(chunk, ensure_ascii=False))
                elif isinstance(chunk, str):
                    full_content += chunk
                    yield _sse_event("transcript", json.dumps({"role": "assistant", "text": chunk, "partial": True}))
            
            if analysis_payload is None:
                await _save_message(session_id, "user", text)

            await _save_message(session_id, "assistant", full_content)
            
            yield _sse_event("status", "done")
            yield _sse_event("done", "[DONE]")

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
    pipeline = get_pipeline()
    return {
        "status": "online",
        "device": pipeline.device,
        "models": {
            "hebert": "loaded",
            "aya": "connected"
        }
    }
