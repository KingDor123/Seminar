import logging
import json
import asyncio
import time
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.stt import STTService
from app.services.llm import LLMService
from app.services.tts import TTSService

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Services
try:
    stt_service = STTService()
    llm_service = LLMService()
    tts_service = TTSService()
except Exception as e:
    logger.critical(f"Failed to initialize AI Services: {e}")

@router.websocket("/ws/conversation")
async def conversation_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Conversation WebSocket connected.")

    history = [
        {"role": "system", "content": "You are a helpful, empathetic, and professional conversational partner. Keep your responses concise and natural, like a real phone call."}
    ]

    # VAD / Buffering State
    speech_buffer = bytearray()
    silence_counter = 0
    SILENCE_THRESHOLD_CHUNKS = 4 
    AMPLITUDE_THRESHOLD = 0.02 

    try:
        while True:
            # 1. Receive Audio from Client (Raw Float32 Bytes)
            data = await websocket.receive_bytes()
            
            if not data:
                continue

            # Convert to numpy to check amplitude
            chunk_np = np.frombuffer(data, dtype=np.float32)
            
            # Calculate RMS (Root Mean Square) amplitude
            rms = np.sqrt(np.mean(chunk_np**2))
            
            if rms > AMPLITUDE_THRESHOLD:
                # Speech detected
                speech_buffer.extend(data)
                silence_counter = 0
            else:
                # Silence
                if len(speech_buffer) > 0:
                    silence_counter += 1
                
            # If we have speech data and silence has persisted for enough chunks, assume end of utterance
            if len(speech_buffer) > 0 and silence_counter >= SILENCE_THRESHOLD_CHUNKS:
                logger.info(f"Processing speech segment: {len(speech_buffer)} bytes")
                
                # 2. Speech to Text
                user_text = stt_service.transcribe(bytes(speech_buffer))
                
                # Reset buffer immediately
                speech_buffer = bytearray()
                silence_counter = 0
                
                if not user_text or len(user_text.strip()) < 2:
                    continue

                logger.info(f"User said: {user_text}")
                
                # Send transcript back to UI
                await websocket.send_json({"type": "transcript", "role": "user", "text": user_text})

                # 3. Update History
                history.append({"role": "user", "content": user_text})

                # 4. LLM & TTS Streaming Pipeline
                full_ai_response = ""
                current_sentence = ""
                
                await websocket.send_json({"type": "status", "status": "processing"})

                token_generator = llm_service.chat_stream(history)
                
                for token in token_generator:
                    current_sentence += token
                    full_ai_response += token

                    if token in [".", "?", "!", "\n"]:
                        sentence_to_speak = current_sentence.strip()
                        if sentence_to_speak:
                            logger.info(f"Generating TTS for: {sentence_to_speak}")
                            await websocket.send_json({"type": "transcript", "role": "assistant", "text": sentence_to_speak, "partial": True})
                            
                            # Buffer audio for the entire sentence
                            sentence_audio = bytearray()
                            async for audio_chunk in tts_service.stream_audio(sentence_to_speak):
                                sentence_audio.extend(audio_chunk)
                            
                            if len(sentence_audio) > 0:
                                await websocket.send_bytes(bytes(sentence_audio))
                                logger.info(f"Sent complete audio for sentence ({len(sentence_audio)} bytes).")
                                
                        current_sentence = ""

                if current_sentence.strip():
                    logger.info(f"Generating TTS for final segment: {current_sentence.strip()}")
                    await websocket.send_json({"type": "transcript", "role": "assistant", "text": current_sentence.strip(), "partial": True})
                    
                    sentence_audio = bytearray()
                    async for audio_chunk in tts_service.stream_audio(current_sentence.strip()):
                        sentence_audio.extend(audio_chunk)
                    
                    if len(sentence_audio) > 0:
                        await websocket.send_bytes(bytes(sentence_audio))

                history.append({"role": "assistant", "content": full_ai_response})
                
                await websocket.send_json({"type": "status", "status": "listening"})

    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Conversation Error: {e}", exc_info=True)