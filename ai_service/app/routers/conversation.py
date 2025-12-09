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

# --- Service Initialization ---
# We initialize services globally to persist models across connections.
try:
    stt_service = STTService()
    llm_service = LLMService()
    tts_service = TTSService()
except Exception as e:
    logger.critical(f"🔥 Critical: Failed to initialize AI Services: {e}")

@router.websocket("/ai/stream")
async def conversation_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time conversation. 
    
    Handles:
    1. Text Chat: Receives JSON text, streams back tokens.
    2. Voice Chat: Receives raw audio bytes, performs VAD (Voice Activity Detection),
       STT (Speech-to-Text), LLM generation, and TTS (Text-to-Speech) streaming.
    """
    await websocket.accept()
    logger.info("🔌 Conversation WebSocket connected.")

    # --- Conversation State ---
    
    # Default System Prompt
    system_prompt_content = (
        "You are a helpful, empathetic, and professional conversational partner. "
        "Keep your responses concise and natural, like a real phone call."
    )
    
    # Conversation History (Context Window)
    history: List[Dict[str, str]] = [
        {"role": "system", "content": system_prompt_content}
    ]

    # --- VAD (Voice Activity Detection) Parameters ---
    speech_buffer = bytearray()
    silence_counter = 0
    SILENCE_THRESHOLD_CHUNKS = 6  # ~200-300ms of silence to trigger end-of-speech
    AMPLITUDE_THRESHOLD = 0.02    # RMS threshold to distinguish speech from background noise

    try:
        while True:
            # Polymorphic Receive: Can be JSON (Text) or Bytes (Audio)
            message = await websocket.receive()
            
            # ------------------------------------------------------------------
            # Case 1: Text Payload (Chat Interface & Control Messages)
            # ------------------------------------------------------------------
            if "text" in message:
                await _handle_text_message(
                    websocket, 
                    message["text"], 
                    history, 
                    system_prompt_content
                )

            # ------------------------------------------------------------------
            # Case 2: Audio Payload (Real-time Voice/Video Call)
            # ------------------------------------------------------------------
            elif "bytes" in message:
                data = message["bytes"]
                
                # Check for voice activity
                is_speech = _detect_voice_activity(data, AMPLITUDE_THRESHOLD)
                
                if is_speech:
                    speech_buffer.extend(data)
                    silence_counter = 0
                else:
                    # Increment silence counter if we have data in the buffer
                    if len(speech_buffer) > 0:
                        silence_counter += 1
                
                # Process the buffered speech if silence threshold is reached
                if len(speech_buffer) > 0 and silence_counter >= SILENCE_THRESHOLD_CHUNKS:
                    await _process_speech_segment(websocket, speech_buffer, history)
                    
                    # Reset buffer
                    speech_buffer = bytearray()
                    silence_counter = 0

    except WebSocketDisconnect:
        logger.info("🔌 Client disconnected.")
    except RuntimeError as e:
        if "disconnect" in str(e).lower():
            logger.info("🔌 Client disconnected (RuntimeError).")
        else:
            logger.error(f"🚨 WebSocket Runtime Error: {e}", exc_info=True)
    except Exception as e:
        logger.error(f"🚨 WebSocket Error: {e}", exc_info=True)


# ==============================================================================
# Helper Functions
# ==============================================================================

async def _handle_text_message(websocket: WebSocket, text_data: str, history: List[dict], system_prompt: str):
    """
    Parses and processes text messages from the client.
    Handles 'system_prompt' updates and standard chat flow.
    """
    try:
        payload = json.loads(text_data)
        logger.info(f"📨 Received Text Payload: {text_data[:100]}...")

        # Update System Prompt
        if "system_prompt" in payload:
            system_prompt = payload["system_prompt"]
            # Update history's first element
            if history and history[0]["role"] == "system":
                history[0]["content"] = system_prompt
            else:
                history.insert(0, {"role": "system", "content": system_prompt})

        # Process Chat Request
        if "history" in payload:
            input_history = payload["history"]
            # Reconstruct history with current system prompt
            full_history = [{"role": "system", "content": system_prompt}] + input_history
            
            response_mode = payload.get("mode", "text")
            
            if response_mode == "audio":
                # Generate text AND audio (for simulated voice response)
                await _generate_response_with_audio(websocket, full_history, history_ref=history)
            else:
                # Standard text stream
                await _generate_text_stream(websocket, full_history, history_ref=history)
                
        elif "user_text" in payload:
            # Simple injection (used in some test cases)
            user_text = payload["user_text"]
            history.append({"role": "user", "content": user_text})
            # (Note: This branch doesn't trigger generation in the current logic, mostly for state updates)

    except json.JSONDecodeError:
        logger.warning("Received invalid JSON text.")


def _detect_voice_activity(audio_chunk: bytes, threshold: float) -> bool:
    """
    Simple Energy-based VAD (Voice Activity Detection).
    Returns True if RMS amplitude exceeds threshold.
    """
    chunk_np = np.frombuffer(audio_chunk, dtype=np.float32)
    rms = np.sqrt(np.mean(chunk_np**2))
    return rms > threshold


async def _process_speech_segment(websocket: WebSocket, audio_buffer: bytearray, history: List[dict]):
    """
    Orchestrates the pipeline: STT -> LLM -> TTS
    """
    logger.info(f"🎙️  Processing speech segment: {len(audio_buffer)} bytes")
    
    # 1. Speech-to-Text
    # Run in thread to avoid blocking the event loop
    user_text = await asyncio.to_thread(stt_service.transcribe, bytes(audio_buffer))
    
    if not user_text or len(user_text.strip()) < 2:
        logger.debug("Ignored empty/noise transcription.")
        return

    # Send transcript back to UI
    await websocket.send_json({"type": "transcript", "role": "user", "text": user_text})
    
    # Update History
    history.append({"role": "user", "content": user_text})

    # 2. & 3. LLM Generation & TTS Streaming
    await _generate_response_with_audio(websocket, history, history_ref=history)


async def _generate_response_with_audio(websocket: WebSocket, messages: List[dict], history_ref: List[dict]):
    """
    Generates LLM response and streams Audio (TTS) sentence-by-sentence.
    """
    await websocket.send_json({"type": "status", "status": "processing"})
    
    full_ai_response = ""
    current_sentence = ""
    token_generator = llm_service.chat_stream(messages)
    
    try:
        for token in token_generator:
            current_sentence += token
            full_ai_response += token

            # Check for sentence boundaries to trigger TTS
            if token in [".", "?", "!", "\n"] and len(current_sentence.strip()) > 1:
                sentence_to_speak = current_sentence.strip()
                logger.debug(f"🗣️  Speaking: {sentence_to_speak}")
                
                # Send text transcript for UI
                await websocket.send_json({
                    "type": "transcript", 
                    "role": "assistant", 
                    "text": sentence_to_speak, 
                    "partial": True
                })
                
                # Stream Audio
                await _stream_tts_audio(websocket, sentence_to_speak)
                
                current_sentence = ""

        # Process any remaining text in the buffer
        if current_sentence.strip():
            await websocket.send_json({
                "type": "transcript", 
                "role": "assistant", 
                "text": current_sentence.strip(), 
                "partial": True
            })
            await _stream_tts_audio(websocket, current_sentence.strip())

        # Update History with full response
        history_ref.append({"role": "assistant", "content": full_ai_response})
        await websocket.send_json({"type": "status", "status": "listening"})
        
    except Exception as e:
        logger.error(f"Error during response generation: {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


async def _stream_tts_audio(websocket: WebSocket, text: str):
    """
    Helper to generate and send TTS audio chunks.
    """
    try:
        # Buffer audio for the entire sentence to ensure smooth playback
        sentence_audio = bytearray()
        async for audio_chunk in tts_service.stream_audio(text):
            sentence_audio.extend(audio_chunk)
        
        if len(sentence_audio) > 0:
            await websocket.send_bytes(bytes(sentence_audio))
    except Exception as e:
        logger.error(f"TTS Stream Error: {e}")


async def _generate_text_stream(websocket: WebSocket, messages: List[dict], history_ref: List[dict]):
    """
    Standard text-only streaming (ChatGPT style).
    """
    full_ai_response = ""
    token_generator = llm_service.chat_stream(messages)
    
    for token in token_generator:
        full_ai_response += token
        await websocket.send_text(token)
    
    history_ref.append({"role": "assistant", "content": full_ai_response})