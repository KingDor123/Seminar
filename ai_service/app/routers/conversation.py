import logging
import asyncio
import json
import httpx
import os
from fastapi import APIRouter, HTTPException, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator, List, Dict, Any

import sys

# Robust import to handle both Docker (/app root) and Local (parent root) paths
try:
    from ai_service.pipeline import HybridPipeline
except ImportError:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pipeline_dir = os.path.abspath(os.path.join(current_dir, '../..'))
    if pipeline_dir not in sys.path:
        sys.path.append(pipeline_dir)
    from pipeline import HybridPipeline

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

async def _save_message(session_id: int, role: str, content: str, sentiment: Optional[str] = None):
    """
    Saves a message to the database asynchronously.
    """
    if not session_id or not content: return
    try:
        db_role = "ai" if role == "assistant" else role
        payload = {"role": db_role, "content": content}
        
        # Add sentiment if provided (Backend Message model should support this)
        if sentiment:
            payload["sentiment"] = sentiment

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
    background_tasks: BackgroundTasks,
    session_id: int = Form(...),
    text: str = Form(...),
    system_prompt: str = Form(...),
    difficulty: str = Form("normal")
):
    """
    Main Interaction Endpoint (Streaming SSE) with History Injection.
    """
    logger.info(f"🗣️ Interaction Request: Session={session_id}, Difficulty={difficulty}")
    
    # 1. Fetch History
    history = await _fetch_history(session_id)
    
    # 2. Save User Message
    background_tasks.add_task(_save_message, session_id, "user", text)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            pipeline = get_pipeline()
            
            yield _sse_event("transcript", json.dumps({"role": "user", "text": text}))
            yield _sse_event("status", "thinking")
            
            full_content = ""
            detected_sentiment = "neutral" # Default fallback

            # 3. Stream AI Response
            async for chunk in pipeline.process_user_message_stream(
                text=text,
                base_system_prompt=system_prompt,
                difficulty_level=difficulty,
                history=history
            ):
                # TYPE CHECK: Separate Metadata from Text
                if isinstance(chunk, dict):
                    # It's metadata (e.g., sentiment)
                    if "sentiment" in chunk:
                        detected_sentiment = chunk["sentiment"]
                        # Optional: Stream metrics to frontend
                        yield _sse_event("metrics", json.dumps(chunk))
                elif isinstance(chunk, str):
                    # It's a text token
                    full_content += chunk
                    yield _sse_event("transcript", json.dumps({"role": "assistant", "text": chunk, "partial": True}))
            
            # 4. Save AI Response with Sentiment
            await _save_message(session_id, "assistant", full_content, sentiment=detected_sentiment)
            
            # 5. Finalize
            yield _sse_event("status", "done")
            yield _sse_event("done", "[DONE]")

        except Exception as e:
            logger.error(f"❌ SSE Stream Error: {e}")
            yield _sse_event("error", str(e))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
