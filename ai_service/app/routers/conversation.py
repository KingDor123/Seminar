import logging
import json
import asyncio
import base64
import httpx
import time
import os
from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator, Any

from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService
from app.services.preprocessor import Preprocessor

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Global AI Services (Lazy Loaded) ---
_services = {
    "stt": None,
    "llm": None,
    "tts": None
}

def get_services():
    """Lazy load services to avoid heavy initialization at import time."""
    global _services
    if _services["stt"] is None:
        try:
            logger.info("lazy loading AI services...")
            _services["stt"] = STTService()
            _services["llm"] = LLMService()
            _services["tts"] = TTSService()
        except Exception as e:
            logger.critical(f"🔥 Critical AI Failure during lazy load: {e}")
            raise e
    return _services["stt"], _services["llm"], _services["tts"]

# --- Constants ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5000/api")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "supersecretkey")

# --- Pydantic Models ---
class TTSRequest(BaseModel):
    text: str
    voice: Optional[str] = None

# --- HTTP Endpoints ---

@router.post("/tts")
async def generate_tts(request: TTSRequest):
    """
    HTTP Endpoint for generating TTS audio.
    Returns JSON with base64 encoded audio.
    """
    try:
        _, _, tts_service = get_services()
        
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")

        audio_content = bytearray()
        async for chunk in tts_service.stream_audio(request.text, request.voice):
            audio_content.extend(chunk)

        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

        return {
            "audio": audio_base64,
            "visemes": []
        }

    except Exception as e:
        logger.error(f"TTS Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interact")
async def interact(
    session_id: int = Form(...),
    text: Optional[str] = Form(None),
    audio: Optional[UploadFile] = File(None),
    system_prompt: Optional[str] = Form("You are a helpful assistant."),
    voice: Optional[str] = Form(None)
):
    """
    SSE Endpoint for Chat/Voice Interaction.
    Accepts Text OR Audio (Multipart).
    Streams Server-Sent Events (Text + Audio).
    """
    logger.info(f"🗣️ Interaction Request: Session={session_id}, Text={bool(text)}, Audio={bool(audio)}")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Initialize services
            stt_service, llm_service, tts_service = get_services()
            
            # 1. Process Input (STT if Audio)
            user_text = ""
            stt_result = {}
            
            if audio:
                try:
                    audio_bytes = await audio.read()
                    if len(audio_bytes) > 0:
                        stt_result = await asyncio.to_thread(stt_service.transcribe, audio_bytes)
                        user_text = stt_result.get("clean_text", "").strip()
                        
                        if not user_text:
                            yield _sse_event("status", "processing_empty_audio")
                            yield _sse_event("debug", "No speech detected in audio.")
                            return
                except Exception as e:
                    logger.error(f"STT Error: {e}")
                    yield _sse_event("error", f"STT Failed: {str(e)}")
                    return

            # If no audio (or audio failed/empty but didn't return), check text
            if not user_text and text:
                raw_input = text
                _, user_text, filler_count = Preprocessor.process_text(raw_input)
                # Mock stt_result for consistent metrics downstream
                stt_result = {
                    "clean_text": user_text,
                    "raw_text": raw_input,
                    "filler_word_count": filler_count
                }

            if not user_text:
                yield _sse_event("error", "No input provided (text or audio).")
                return

            # Yield User Transcript
            yield _sse_event("transcript", json.dumps({"role": "user", "text": user_text}))

            # 2. Load History & Save User Message (Parallel)
            history: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
            
            # Fetch History
            prev_msgs = await _fetch_history(session_id)
            history.extend(prev_msgs)
            
            # Determine last AI message for analysis context
            last_ai_message = ""
            if len(history) > 1 and history[-1]["role"] == "assistant":
                last_ai_message = history[-1]["content"]

            # Save User Message to DB (Fire & Forget)
            asyncio.create_task(_save_message(session_id, "user", user_text))
            
            # Append current user message to history for LLM
            history.append({"role": "user", "content": user_text})

            # 4. Generate AI Response (Streaming)
            yield _sse_event("status", "thinking")
            
            full_ai_response = ""
            current_sentence = ""

            for token in llm_service.chat_stream(history):
                full_ai_response += token
                current_sentence += token
                
                # Check for sentence boundaries for TTS
                if _is_sentence_complete(current_sentence):
                    sentence_text = current_sentence.strip()
                    if sentence_text:
                        # Yield Text Chunk
                        yield _sse_event("transcript", json.dumps({"role": "assistant", "text": sentence_text, "partial": True}))
                        
                        # Generate & Yield Audio Chunk
                        try:
                            audio_chunk = bytearray()
                            async for chunk in tts_service.stream_audio(sentence_text, voice):
                                audio_chunk.extend(chunk)
                            
                            if audio_chunk:
                                b64_audio = base64.b64encode(audio_chunk).decode("utf-8")
                                yield _sse_event("audio", b64_audio)
                        except Exception as e:
                             logger.error(f"TTS Stream Error: {e}")
                    
                    current_sentence = ""

            # Process remaining text
            if current_sentence.strip():
                sentence_text = current_sentence.strip()
                yield _sse_event("transcript", json.dumps({"role": "assistant", "text": sentence_text, "partial": True}))
                try:
                    audio_chunk = bytearray()
                    async for chunk in tts_service.stream_audio(sentence_text, voice):
                        audio_chunk.extend(chunk)
                    if audio_chunk:
                        b64_audio = base64.b64encode(audio_chunk).decode("utf-8")
                        yield _sse_event("audio", b64_audio)
                except Exception as e:
                    logger.error(f"TTS Stream Error: {e}")

            # 5. Save AI Response
            asyncio.create_task(_save_message(session_id, "assistant", full_ai_response))

            # 6. Save Fast Metrics (Async - Fire & Forget)
            # Only saves WPM, Pauses, etc. No LLM analysis here.
            if last_ai_message:
                asyncio.create_task(
                    _save_fast_metrics(
                        session_id, 
                        stt_result if stt_result else {"clean_text": user_text}, 
                        0.0, 
                        last_ai_message
                    )
                )

            yield _sse_event("status", "done")
            yield _sse_event("done", "[DONE]")

        except Exception as e:
            logger.error(f"Interaction Error: {e}")
            yield _sse_event("error", str(e))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/report/generate/{session_id}")
async def generate_report(session_id: int):
    """
    Trigger a full retrospective analysis of the session.
    Iterates through history and runs deep LLM analysis on user messages.
    """
    logger.info(f"📊 Generating Report for Session {session_id}...")
    try:
        _, llm_service, _ = get_services()
        
        # 1. Fetch Full History
        history = await _fetch_history(session_id)
        if not history:
            return {"status": "empty", "message": "No history found for this session."}

        analyzed_count = 0
        
        # 2. Iterate and Analyze
        # We look for User messages and their preceding AI context
        for i in range(len(history)):
            msg = history[i]
            if msg["role"] == "user":
                user_text = msg["content"]
                
                # Find preceding AI message for context
                context = ""
                if i > 0 and history[i-1]["role"] == "assistant":
                    context = history[i-1]["content"]
                
                # Skip if empty
                if not user_text.strip(): continue

                # Run Deep Analysis (Synchronous here is fine, it's a background job for the user)
                behavior_context = {}
                
                analysis_results = await asyncio.to_thread(
                    llm_service.analyze_behavior, 
                    user_text, 
                    context,
                    behavior_context
                )
                
                # Save Metrics
                for metric_name, metric_value in analysis_results.items():
                    if isinstance(metric_value, (int, float)):
                        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
                            await client.post(
                                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                                json={"name": metric_name, "value": metric_value, "context": f"Retrospective: '{user_text[:20]}...'"}
                            )
                analyzed_count += 1

        return {"status": "success", "analyzed_messages": analyzed_count}

    except Exception as e:
        logger.error(f"Report Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Helpers ---

def _sse_event(event_type: str, data: str) -> str:
    return f"event: {event_type}\ndata: {data}\n\n"

def _is_sentence_complete(text: str) -> bool:
    text = text.strip()
    if not text: return False
    return text[-1] in [".", "?", "!", "\n"] and len(text) > 3

async def _fetch_history(session_id: int) -> List[Dict[str, str]]:
    history = []
    try:
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            resp = await client.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages")
            if resp.status_code == 200:
                messages = resp.json()
                for m in messages:
                    role = "assistant" if m["role"] == "ai" else m["role"]
                    history.append({"role": role, "content": m["content"]})
    except Exception as e:
        logger.error(f"History Fetch Error: {e}")
    return history

async def _save_message(session_id: int, role: str, content: str):
    if not session_id or not content: return
    try:
        db_role = "ai" if role == "assistant" else role
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            await client.post(
                f"{BACKEND_URL}/chat/sessions/{session_id}/messages",
                json={"role": db_role, "content": content}
            )
    except Exception as e:
        logger.error(f"DB Save Error: {e}")

async def _save_fast_metrics(
    session_id: int, 
    stt_result: Dict[str, Any], 
    latency: float, 
    last_ai_message: str
):
    """
    Saves ONLY fast, STT-based metrics (WPM, Pauses, Fillers).
    NO LLM calls here.
    """
    if not session_id: return

    try:
        user_text = stt_result.get("clean_text", "")
        
        # 1. Save Latency
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "response_latency", "value": latency, "context": f"Response to: '{last_ai_message}'"}
            )
        
        # 2. Save Speech Rate
        wpm = stt_result.get("speech_rate_wpm", 0.0)
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "speech_rate_wpm", "value": wpm, "context": user_text}
            )
            
        # 3. Save Pauses
        pause_count = stt_result.get("pause_count", 0)
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "pause_count", "value": float(pause_count), "context": user_text}
            )

        # 4. Save Fillers
        filler_count = stt_result.get("filler_word_count", 0)
        async with httpx.AsyncClient(headers={"x-internal-api-key": INTERNAL_API_KEY}) as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "filler_word_count", "value": float(filler_count), "context": user_text}
            )

    except Exception as e:
        logger.error(f"❌ Error during fast metric saving: {e}")
