import logging
import json
import asyncio
import base64
import httpx
import time
from fastapi import APIRouter, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, AsyncGenerator

from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Global AI Services ---
try:
    stt_service = STTService()
    llm_service = LLMService()
    tts_service = TTSService()
except Exception as e:
    logger.critical(f"🔥 Critical AI Failure: {e}")

# --- Constants ---
BACKEND_URL = "http://backend:5000/api"

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
            # 1. Process Input (STT if Audio)
            user_text = text or ""
            if audio:
                try:
                    audio_bytes = await audio.read()
                    if len(audio_bytes) > 0:
                        transcribed = await asyncio.to_thread(stt_service.transcribe, audio_bytes)
                        user_text = transcribed.strip()
                        if not user_text:
                            yield _sse_event("status", "processing_empty_audio")
                            # If audio was noise, we might want to stop or ask for repeat.
                            # For now, let's yield a debug event and stop if empty.
                            yield _sse_event("debug", "No speech detected in audio.")
                            return
                except Exception as e:
                    logger.error(f"STT Error: {e}")
                    yield _sse_event("error", f"STT Failed: {str(e)}")
                    return

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
            
            # Determine last AI message for analysis context (before appending new user msg)
            last_ai_message = ""
            if len(history) > 1 and history[-1]["role"] == "assistant":
                last_ai_message = history[-1]["content"]

            # Save User Message to DB (Fire & Forget)
            asyncio.create_task(_save_message(session_id, "user", user_text))
            
            # Append current user message to history for LLM
            history.append({"role": "user", "content": user_text})

            # 3. Analyze User Input (Async)
            # We can do this now or later. Let's fire it now.
            if last_ai_message:
                asyncio.create_task(_analyze_behavior(session_id, user_text, last_ai_message))

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

            yield _sse_event("status", "done")
            yield _sse_event("done", "[DONE]")

        except Exception as e:
            logger.error(f"Interaction Error: {e}")
            yield _sse_event("error", str(e))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# --- Helpers ---

def _sse_event(event_type: str, data: str) -> str:
    # SSE Format:
    # event: type\n
    # data: ...\n\n
    return f"event: {event_type}\ndata: {data}\n\n"

def _is_sentence_complete(text: str) -> bool:
    text = text.strip()
    if not text: return False
    return text[-1] in [".", "?", "!", "\n"] and len(text) > 3

async def _fetch_history(session_id: int) -> List[Dict[str, str]]:
    history = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages")
            if resp.status_code == 200:
                messages = resp.json()
                for m in messages:
                    # Map 'ai' role to 'assistant' for LLM
                    role = "assistant" if m["role"] == "ai" else m["role"]
                    history.append({"role": role, "content": m["content"]})
    except Exception as e:
        logger.error(f"History Fetch Error: {e}")
    return history

async def _save_message(session_id: int, role: str, content: str):
    if not session_id or not content: return
    try:
        db_role = "ai" if role == "assistant" else role
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/chat/sessions/{session_id}/messages",
                json={"role": db_role, "content": content}
            )
    except Exception as e:
        logger.error(f"DB Save Error: {e}")

async def _analyze_behavior(session_id: int, user_text: str, context: str):
    try:
        results = await asyncio.to_thread(llm_service.analyze_behavior, user_text, context)
        for metric_name, metric_value in results.items():
            if isinstance(metric_value, (int, float)):
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                        json={"name": metric_name, "value": metric_value, "context": user_text[:50]}
                    )
    except Exception as e:
        logger.error(f"Analysis Error: {e}")
