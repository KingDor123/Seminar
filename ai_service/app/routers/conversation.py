import logging
import json
import asyncio
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict

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
    
    history: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

    # --- VAD Settings ---
    speech_buffer = bytearray()
    silence_counter = 0
    SILENCE_THRESHOLD = 5   # Increased to prevent cutting off words
    AMP_THRESHOLD = 0.01   # Sensitivity (increased to reduce false positives)

    try:
        while True:
            try:
                msg = await websocket.receive()
            except WebSocketDisconnect:
                logger.info("🔌 Client Disconnected")
                break # Exit the loop gracefully on disconnect
            except Exception as e:
                logger.error(f"🚨 Error receiving WebSocket message: {e}")
                break # Also break on other receive errors

            # 1. Text Control Messages
            if "text" in msg:
                await _handle_text(websocket, msg["text"], history, system_prompt)

            # 2. Audio Stream
            elif "bytes" in msg:
                data = msg["bytes"]
                is_speech, _ = _vad(data, AMP_THRESHOLD)
                
                if is_speech:
                    speech_buffer.extend(data)
                    silence_counter = 0
                elif len(speech_buffer) > 0:
                    silence_counter += 1
                
                # Trigger Processing
                if len(speech_buffer) > 0 and silence_counter >= SILENCE_THRESHOLD:
                    if len(speech_buffer) > 10000:
                        await _process_speech(websocket, speech_buffer, history)
                    else:
                        logger.debug(f"Ignored short noise ({len(speech_buffer)} bytes)")
                    
                    speech_buffer = bytearray()
                    silence_counter = 0

    except Exception as e:
        logger.error(f"🚨 Socket Error (outside receive loop): {e}")


# --- Helpers ---

async def _handle_text(ws: WebSocket, text: str, history: List[dict], sys_prompt: str):
    try:
        data = json.loads(text)
        
        # Update Prompt
        if "system_prompt" in data:
            sys_prompt = data["system_prompt"]
            history[0]["content"] = sys_prompt

        # Chat Request
        if "history" in data:
            full_hist = [{"role": "system", "content": sys_prompt}] + data["history"]
            
            if data.get("mode") == "audio":
                await _gen_response(ws, full_hist, history)
            else:
                await _gen_text(ws, full_hist, history)

    except Exception:
        pass


def _vad(audio: bytes, threshold: float) -> (bool, float):
    chunk = np.frombuffer(audio, dtype=np.float32)
    if len(chunk) == 0: return False, 0.0
    rms = np.sqrt(np.mean(chunk**2))
    return rms > threshold, rms


async def _process_speech(ws: WebSocket, buffer: bytearray, history: List[dict]):
    logger.info(f"🎙️  Processing {len(buffer)} bytes...")
    
    text = await asyncio.to_thread(stt_service.transcribe, bytes(buffer))
    logger.debug(f"STT Raw Text: '{text}' (length: {len(text.strip())})")
    
    if not text or len(text.strip()) < 5: return

    await ws.send_json({"type": "transcript", "role": "user", "text": text})
    history.append({"role": "user", "content": text})

    await _gen_response(ws, history, history)


async def _gen_response(ws: WebSocket, msgs: List[dict], history: List[dict]):
    await ws.send_json({"type": "status", "status": "processing"})
    
    full_resp = ""
    curr_sent = ""
    
    try:
        for token in llm_service.chat_stream(msgs):
            curr_sent += token
            full_resp += token

            # Split sentences/phrases for fluid TTS (more aggressive splitting)
            # Trigger on: . ? ! \n OR , ; (if length > 15 chars)
            is_punctuated = token in [".", "?", "!", "\n"]
            is_phrase_break = token in [",", ";"] and len(curr_sent.strip()) > 15
            
            if (is_punctuated or is_phrase_break) and len(curr_sent.strip()) > 2:
                sent = curr_sent.strip()
                await ws.send_json({"type": "transcript", "role": "assistant", "text": sent, "partial": True})
                await _stream_tts(ws, sent)
                curr_sent = ""

        # Flush remaining
        if curr_sent.strip():
            sent = curr_sent.strip()
            await ws.send_json({"type": "transcript", "role": "assistant", "text": sent, "partial": True})
            await _stream_tts(ws, sent)

        history.append({"role": "assistant", "content": full_resp})
        await ws.send_json({"type": "status", "status": "listening"})
        
    except Exception as e:
        logger.error(f"Gen Error: {e}")


async def _stream_tts(ws: WebSocket, text: str):
    async for chunk in tts_service.stream_audio(text):
        await ws.send_bytes(chunk)


async def _gen_text(ws: WebSocket, msgs: List[dict], history: List[dict]):
    full_resp = ""
    for token in llm_service.chat_stream(msgs):
        full_resp += token
        await ws.send_text(token)
    history.append({"role": "assistant", "content": full_resp})