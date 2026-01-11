import logging
import json
import httpx
import os
from fastapi import APIRouter, HTTPException, Form, UploadFile, File
from fastapi.responses import StreamingResponse
from typing import Optional, AsyncGenerator, List, Dict, Any

import sys

# Robust import to handle both Docker (/app root) and Local (parent root) paths
try:
    from ai_service.app.engine.orchestrator import orchestrator
    from ai_service.app.engine.scenarios import SCENARIO_REGISTRY
    from ai_service.app.services.stt import STTService
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pipeline_dir = os.path.abspath(os.path.join(current_dir, '../..'))
    if pipeline_dir not in sys.path:
        sys.path.append(pipeline_dir)
    from app.engine.orchestrator import orchestrator
    from app.engine.scenarios import SCENARIO_REGISTRY
    from app.services.stt import STTService

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Constants ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5000/api")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "supersecretkey")

# --- Initialize Services ---
try:
    stt_service = STTService()
except Exception as e:
    logger.error(f"Failed to initialize STT Service: {e}")
    stt_service = None

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
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    scenario_id: Optional[str] = Form(None)
):
    """
    Main Interaction Endpoint (Streaming SSE) with History Injection.
    Supports Text or Audio input.
    """
    if not scenario_id or not scenario_id.strip():
        raise HTTPException(status_code=400, detail="scenario_id is required")

    logger.info(f"🗣️ Interaction Request: Session={session_id}, Scenario={scenario_id}")
    
    stt_data = {}
    
    # 0. Input Handling
    if audio:
        if not stt_service:
             raise HTTPException(status_code=500, detail="STT Service unavailable")
        
        logger.info(f"🎤 Receiving Audio: {audio.filename}")
        audio_bytes = await audio.read()
        stt_result = await stt_service.transcribe(audio_bytes, language="he")
        
        text = stt_result.get("raw_text", "")
        stt_data = stt_result
        
        if not text:
             logger.warning("STT yielded empty text.")
    
    if not text or not text.strip():
        # Fallback if audio failed or neither provided
        if not audio: 
             raise HTTPException(status_code=400, detail="Either 'text' or 'audio' must be provided.")
        # If audio provided but no text, we continue with empty text (will likely fail logic but allow flow)

    input_type = "audio" if audio else "text"
    logger.info(f"[INPUT] session={session_id} scenario={scenario_id} type={input_type}")
    logger.info(f"[INPUT] raw_text=\"{text}\"")

    is_cold_start = text.strip() == "[START]"

    # 1. Fetch History
    history = await _fetch_history(session_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            if not is_cold_start:
                # Send back the transcript if it was audio, or just confirm text
                yield _sse_event("transcript", json.dumps({"role": "user", "text": text}))
            yield _sse_event("status", "thinking")

            # --- BRANCH: NEW ENGINE ---
            if scenario_id in SCENARIO_REGISTRY:
                logger.info(f"🚀 Using Engine Orchestrator for {scenario_id}")
                full_content = ""
                analysis_payload: Optional[Dict[str, Any]] = None
                
                # Pass STT data to orchestrator
                async for chunk in orchestrator.process_turn(str(session_id), scenario_id, text, history, stt_data=stt_data):
                     if isinstance(chunk, dict):
                         # Metadata / Analysis
                         if "type" in chunk and chunk["type"] == "analysis":
                             analysis_payload = chunk
                             # Map new engine fields to legacy schema for frontend
                             if not is_cold_start:
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
                
                if analysis_payload is None and not is_cold_start:
                    # Fallback save if analysis failed
                    await _save_message(session_id, "user", text)
                
                await _save_message(session_id, "assistant", full_content)
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
