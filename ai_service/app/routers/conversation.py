import logging
import json
import asyncio
import base64
import numpy as np
import httpx
import time 
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any

from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService

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

# --- WebSocket Endpoint ---

@router.websocket("/ai/stream")
async def conversation_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket for Voice/Text Chat.
    """
    await websocket.accept()
    logger.info("🔌 Client Connected")
    
    # Initialize services for this session
    try:
        stt_service, llm_service, tts_service = get_services()
    except Exception as e:
        logger.error(f"Failed to load AI services: {e}")
        await websocket.close(code=1011)
        return

    # --- Config ---
    system_prompt = (
        "You are a supportive, patient soft skills trainer for people with HFASD. "
        "Provide a safe environment. Be encouraging. "
        "If a social mistake occurs, gently offer feedback."
    )
    
    # State
    history: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    session_id: Optional[int] = None
    
    # Latency Tracking (Client-Side Timestamps)
    client_last_ai_end_ts: float = 0.0
    client_user_start_ts: float = 0.0

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
                data = json.loads(msg["text"])
                
                # Handle Protocol Messages
                if data.get("type") == "ai_stopped_speaking":
                    client_last_ai_end_ts = data.get("timestamp", 0) / 1000.0
                    logger.debug(f"⏱️ AI Stopped Speaking at (Client Time): {client_last_ai_end_ts}")
                    continue
                
                if data.get("type") == "user_started_speaking":
                    client_user_start_ts = data.get("timestamp", 0) / 1000.0
                    logger.debug(f"⏱️ User Started Speaking at (Client Time): {client_user_start_ts}")
                    continue

                # Handle Init / Config
                if "system_prompt" in data:
                    system_prompt = data["system_prompt"]
                    history[0]["content"] = system_prompt

                if "session_id" in data:
                    session_id = data["session_id"]
                    logger.info(f"🔗 Associated with Session ID: {session_id}")
                    await _load_history(session_id, history)

                if "history" in data:
                    for item in data["history"]:
                        if not history or history[-1]["content"] != item["content"]:
                             history.append(item)
                    
                    if data.get("mode") == "audio":
                        await _gen_response(websocket, history, session_id, llm_service, tts_service)

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
                        # Calculate latency based on caught timestamps
                        latency = 0.0
                        if client_last_ai_end_ts > 0 and client_user_start_ts > 0:
                            latency = max(0.0, client_user_start_ts - client_last_ai_end_ts)
                        
                        await _process_speech(
                            websocket, 
                            speech_buffer, 
                            history, 
                            session_id, 
                            latency,
                            stt_service,
                            llm_service,
                            tts_service
                        )
                    else:
                        logger.debug(f"Ignored short noise ({len(speech_buffer)} bytes)")
                    
                    speech_buffer = bytearray()
                    silence_counter = 0
                    # Reset user start time for next turn to ensure fresh capture
                    client_user_start_ts = 0.0 

    except Exception as e:
        logger.error(f"🚨 Connection Error: {e}")
    finally:
        logger.info("👋 Connection handler cleanup")


# --- Helpers ---

async def _analyze_and_save_metrics(
    session_id: int, 
    stt_result: Dict[str, Any], 
    latency: float, 
    last_ai_message: str,
    llm_service: LLMService
):
    """
    Analyzes user speech behavior and saves metrics.
    """
    if not session_id: return

    try:
        user_text = stt_result.get("clean_text", "")
        
        # 1. Save Latency
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "response_latency", "value": latency, "context": f"Response to: '{last_ai_message}'"}
            )
        
        # 2. Save Speech Rate
        wpm = stt_result.get("speech_rate_wpm", 0.0)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "speech_rate_wpm", "value": wpm, "context": user_text}
            )
            
        # 3. Save Pauses
        pause_count = stt_result.get("pause_count", 0)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "pause_count", "value": float(pause_count), "context": user_text}
            )

        # 4. Save Fillers
        filler_count = stt_result.get("filler_word_count", 0)
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                json={"name": "filler_word_count", "value": float(filler_count), "context": user_text}
            )

        # 5. Semantic Analysis (LLM) with Behavioral Context
        behavior_context = {
            "latency": latency,
            "wpm": wpm,
            "pauses": pause_count,
            "fillers": filler_count
        }
        
        analysis_results = await asyncio.to_thread(
            llm_service.analyze_behavior, 
            user_text, 
            last_ai_message,
            behavior_context
        )
        
        for metric_name, metric_value in analysis_results.items():
            if isinstance(metric_value, (int, float)):
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{BACKEND_URL}/analytics/sessions/{session_id}/metrics",
                        json={"name": metric_name, "value": metric_value, "context": f"Analysis of: '{user_text}'"}
                    )

    except Exception as e:
        logger.error(f"❌ Error during metric analysis: {e}")

async def _load_history(session_id: int, history: List[dict]):
    """Fetch previous chat messages from Backend API"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BACKEND_URL}/chat/sessions/{session_id}/messages")
            if resp.status_code == 200:
                messages = resp.json()
                logger.info(f"📜 Loaded {len(messages)} past messages from DB.")
                for m in messages:
                    role = "assistant" if m["role"] == "ai" else m["role"]
                    history.append({"role": role, "content": m["content"]})
    except Exception as e:
        logger.error(f"❌ DB Load Error: {e}")

async def _save_message(session_id: int, role: str, content: str):
    """Save message to Backend API"""
    if not session_id: return
    try:
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


async def _process_speech(
    ws: WebSocket, 
    buffer: bytearray, 
    history: List[dict], 
    session_id: Optional[int],
    latency: float,
    stt_service: STTService,
    llm_service: LLMService,
    tts_service: TTSService
):
    logger.info(f"🎙️  Processing {len(buffer)} bytes... Latency: {latency:.2f}s")
    
    # 1. Structured STT
    stt_result = await asyncio.to_thread(stt_service.transcribe, bytes(buffer))
    
    raw_text = stt_result.get("raw_text", "")
    clean_text = stt_result.get("clean_text", "")
    
    logger.info(f"STT: '{raw_text}' -> Clean: '{clean_text}'")
    
    if not clean_text or len(clean_text) < 2: 
        return

    # Send transcript to UI
    await ws.send_json({"type": "transcript", "role": "user", "text": clean_text})
    
    # Update Memory with CLEAN text
    history.append({"role": "user", "content": clean_text})
    
    # Save to DB
    await _save_message(session_id, "user", clean_text)

    # Trigger async analysis and save
    if session_id and history and len(history) >= 2:
        last_ai_message = history[-2]["content"] if history[-2]["role"] == "assistant" else ""
        if last_ai_message:
            # We can keep analysis async as it doesn't block conversation flow
            asyncio.create_task(
                _analyze_and_save_metrics(session_id, stt_result, latency, last_ai_message, llm_service)
            )

    # Generate Response (passing metrics implicitly via history context if needed, but for now standard chat)
    await _gen_response(ws, history, session_id, llm_service, tts_service)


async def _gen_response(
    ws: WebSocket, 
    msgs: List[dict], 
    session_id: Optional[int],
    llm_service: LLMService,
    tts_service: TTSService
):
    await ws.send_json({"type": "status", "status": "processing"})
    
    full_resp = ""
    curr_sent = ""
    
    try:
        # Stream the response
        for token in llm_service.chat_stream(msgs):
            curr_sent += token
            full_resp += token

            is_punctuated = token in [".", "?", "!", "\n"]
            is_phrase_break = token in [",", ";"] and len(curr_sent.strip()) > 15
            
            if (is_punctuated or is_phrase_break) and len(curr_sent.strip()) > 2:
                sent = curr_sent.strip()
                await ws.send_json({"type": "transcript", "role": "assistant", "text": sent, "partial": True})
                await _stream_tts(ws, sent, tts_service)
                curr_sent = ""

        if curr_sent.strip():
            sent = curr_sent.strip()
            await ws.send_json({"type": "transcript", "role": "assistant", "text": sent, "partial": True})
            await _stream_tts(ws, sent, tts_service)

        msgs.append({"role": "assistant", "content": full_resp})
        
        if session_id:
            asyncio.create_task(_save_message(session_id, "assistant", full_resp))

        await ws.send_json({"type": "status", "status": "listening"})
        
    except Exception as e:
        logger.error(f"🔥 Gen Error: {e}")
        await ws.send_json({"type": "error", "message": "I lost my train of thought."})
        await ws.send_json({"type": "status", "status": "listening"})


async def _stream_tts(ws: WebSocket, text: str, tts_service: TTSService):
    async for chunk in tts_service.stream_audio(text):
        await ws.send_bytes(chunk)
