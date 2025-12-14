import logging
import json
import asyncio
import base64
import numpy as np
import httpx
import time # Import time module
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional

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

# --- Global State for Latency Tracking ---
last_ai_end_time: Optional[float] = None

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

# --- WebSocket Endpoint ---

@router.websocket("/ai/stream")
async def conversation_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket for Voice/Text Chat.
    """
    await websocket.accept()
    logger.info("🔌 Client Connected")

    # --- Config ---
    system_prompt = (
        "You are a supportive, patient soft skills trainer for people with HFASD. "
        "Provide a safe environment. Be encouraging. "
        "If a social mistake occurs, gently offer feedback."
    )
    
    # State
    history: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    session_id: Optional[int] = None

    # --- VAD Settings ---
    speech_buffer = bytearray()
    silence_counter = 0
    SILENCE_THRESHOLD = 20
    AMP_THRESHOLD = 0.002

    try:
        while True:
            try:
                msg = await websocket.receive()
                
                if msg["type"] == "websocket.disconnect":
                    logger.info("🔌 Client Disconnected (Clean)")
                    break

            except WebSocketDisconnect:
                logger.info("🔌 Client Disconnected (Socket Closed)")
                break
            except RuntimeError as re:
                if "disconnect" in str(re).lower():
                    logger.info("🔌 Client Disconnected (Runtime)")
                    break
                logger.error(f"🚨 Runtime Error: {re}")
                break
            except Exception as e:
                logger.error(f"🚨 Error receiving WebSocket message: {e}")
                break

            # Process Message
            if "text" in msg:
                # Handle configuration / initialization
                data = json.loads(msg["text"])
                
                # Update Prompt
                if "system_prompt" in data:
                    system_prompt = data["system_prompt"]
                    history[0]["content"] = system_prompt

                # Set Session ID
                if "session_id" in data:
                    session_id = data["session_id"]
                    logger.info(f"🔗 Associated with Session ID: {session_id}")
                    
                    # Fetch History from Backend
                    await _load_history(session_id, history)

                # Initialize History (if provided in payload, append it)
                if "history" in data:
                    for item in data["history"]:
                        # Avoid duplicates if we just loaded from DB
                        # Simple check: if not last item
                        if not history or history[-1]["content"] != item["content"]:
                             history.append(item)
                    
                    # If this is an audio-mode init, trigger response
                    if data.get("mode") == "audio":
                        await _gen_response(websocket, history, session_id)

            elif "bytes" in msg:
                data = msg["bytes"]
                is_speech, _ = _vad(data, AMP_THRESHOLD)
                
                if is_speech:
                    speech_buffer.extend(data)
                    silence_counter = 0
                elif len(speech_buffer) > 0:
                    silence_counter += 1
                
                if len(speech_buffer) > 0 and silence_counter >= SILENCE_THRESHOLD:
                    if len(speech_buffer) > 10000:
                        await _process_speech(websocket, speech_buffer, history, session_id)
                    else:
                        logger.debug(f"Ignored short noise ({len(speech_buffer)} bytes)")
                    
                    speech_buffer = bytearray()
                    silence_counter = 0

    except Exception as e:
        logger.error(f"🚨 Connection Error: {e}")
    finally:
        logger.info("👋 Connection handler cleanup")


# --- Helpers ---

async def _analyze_and_save_metrics(session_id: int, user_text: str, latency: float, last_ai_message: str):
    """
    Analyzes user speech and saves metrics to the backend.
    """
    if not session_id:
        logger.warning("Attempted to analyze metrics without a session ID.")
        return

    try:
        # Save Latency metric
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "response_latency", "value": latency, "context": f"User responded after AI message: '{last_ai_message}'"}
            )
        logger.info(f"📊 Latency ({latency:.2f}s) saved for session {session_id}")

        # Analyze sentiment, topic adherence, clarity using LLM
        analysis_results = await asyncio.to_thread(
            llm_service.analyze_behavior, user_text, last_ai_message
        )
        logger.debug(f"🧠 Analysis Results: {analysis_results}")

        for metric_name, metric_value in analysis_results.items():
            if isinstance(metric_value, (int, float)):
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                        json={"name": metric_name, "value": metric_value, "context": f"Analyzed user text: '{user_text}'"}
                    )
                logger.info(f"📊 Metric '{metric_name}' ({metric_value:.2f}) saved for session {session_id}")

    except Exception as e:
        logger.error(f"❌ Error during metric analysis or saving: {e}")

async def _load_history(session_id: int, history: List[dict]):
    """Fetch previous chat messages from Backend API"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages")
            if resp.status_code == 200:
                messages = resp.json()
                logger.info(f"📜 Loaded {len(messages)} past messages from DB.")
                for m in messages:
                    # Map 'ai' role to 'assistant' for LLM
                    role = "assistant" if m["role"] == "ai" else m["role"]
                    history.append({"role": role, "content": m["content"]})
            else:
                logger.warning(f"⚠️ Failed to load history: {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ DB Load Error: {e}")

async def _save_message(session_id: int, role: str, content: str):
    """Save message to Backend API"""
    if not session_id: return
    try:
        # Map 'assistant' back to 'ai' for DB
        db_role = "ai" if role == "assistant" else role
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/chat/sessions/{session_id}/messages",
                json={"role": db_role, "content": content}
            )
    except Exception as e:
        logger.error(f"❌ DB Save Error: {e}")


def _vad(audio: bytes, threshold: float) -> (bool, float):
    chunk = np.frombuffer(audio, dtype=np.float32)
    if len(chunk) == 0: return False, 0.0
    rms = np.sqrt(np.mean(chunk**2))
    return rms > threshold, rms


async def _process_speech(ws: WebSocket, buffer: bytearray, history: List[dict], session_id: Optional[int]):
    global last_ai_end_time # Declare global to modify it
    logger.info(f"🎙️  Processing {len(buffer)} bytes...")
    
    user_speech_start_time = time.time() # Capture start time of user's speech processing

    latency = 0.0
    if last_ai_end_time is not None:
        latency = user_speech_start_time - last_ai_end_time
        logger.debug(f"Calculated Latency: {latency:.2f}s")
    else:
        logger.debug("last_ai_end_time not set, cannot calculate latency.")

    text = await asyncio.to_thread(stt_service.transcribe, bytes(buffer))
    logger.debug(f"STT Raw Text: '{text}' (length: {len(text.strip())})")
    
    if not text or len(text.strip()) < 5: return

    # Send transcript to UI
    await ws.send_json({"type": "transcript", "role": "user", "text": text})
    
    # Update Memory
    history.append({"role": "user", "content": text})
    
    # Save to DB
    asyncio.create_task(_save_message(session_id, "user", text))

    # Trigger async analysis and save
    if session_id and history and len(history) >= 2: # Ensure there's a previous AI message
        last_ai_message = history[-2]["content"] if history[-2]["role"] == "assistant" else ""
        if last_ai_message:
            asyncio.create_task(
                _analyze_and_save_metrics(session_id, text, latency, last_ai_message)
            )

    await _gen_response(ws, history, session_id)


async def _gen_response(ws: WebSocket, msgs: List[dict], session_id: Optional[int]):
    global last_ai_end_time # Declare global to modify it
    await ws.send_json({"type": "status", "status": "processing"})
    
    full_resp = ""
    curr_sent = ""
    
    try:
        for token in llm_service.chat_stream(msgs):
            curr_sent += token
            full_resp += token

            is_punctuated = token in [".", "?", "!", "\n"]
            is_phrase_break = token in [",", ";"] and len(curr_sent.strip()) > 15
            
            if (is_punctuated or is_phrase_break) and len(curr_sent.strip()) > 2:
                sent = curr_sent.strip()
                await ws.send_json({"type": "transcript", "role": "assistant", "text": sent, "partial": True})
                await _stream_tts(ws, sent)
                curr_sent = ""

        if curr_sent.strip():
            sent = curr_sent.strip()
            await ws.send_json({"type": "transcript", "role": "assistant", "text": sent, "partial": True})
            await _stream_tts(ws, sent)

        # Update Memory
        msgs.append({"role": "assistant", "content": full_resp})
        
        # Save to DB
        asyncio.create_task(_save_message(session_id, "assistant", full_resp))

        last_ai_end_time = time.time() # Mark the time AI finishes responding
        await ws.send_json({"type": "status", "status": "listening"})
        
    except Exception as e:
        logger.error(f"Gen Error: {e}")


async def _stream_tts(ws: WebSocket, text: str):
    async for chunk in tts_service.stream_audio(text):
        await ws.send_bytes(chunk)