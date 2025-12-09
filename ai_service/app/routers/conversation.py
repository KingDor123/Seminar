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

@router.websocket("/ai/stream")
async def conversation_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Conversation WebSocket connected.")

    system_prompt_content = "You are a helpful, empathetic, and professional conversational partner. Keep your responses concise and natural, like a real phone call."
    history = [
        {"role": "system", "content": system_prompt_content}
    ]

    # VAD / Buffering State
    speech_buffer = bytearray()
    silence_counter = 0
    SILENCE_THRESHOLD_CHUNKS = 6  # Increased from 4 to filter short noise
    AMPLITUDE_THRESHOLD = 0.02 # Adjusted to 0.02 (middle ground)

    try:
        while True:
            # Polymorphic Receive: Handle both Text (Chat) and Bytes (Audio)
            message = await websocket.receive()
            # logger.info(f"WS Received Message Type: {message.keys()}") # Commented out to reduce noise

            if "text" in message:
                logger.info(f"Received Text Payload: {message['text'][:100]}...")
                # --- TEXT MODE (Chat Interface) ---
                try:
                    payload = json.loads(message["text"])
                    
                    # Update System Prompt if provided
                    if "system_prompt" in payload:
                        system_prompt_content = payload["system_prompt"]
                        # Update the first message in history
                        if history and history[0]["role"] == "system":
                            history[0]["content"] = system_prompt_content
                        else:
                            history.insert(0, {"role": "system", "content": system_prompt_content})

                    # Update/Append History if provided
                    if "history" in payload:
                        # Replace history (keeping system prompt) or append?
                        # Usually the client sends the full context or the new message.
                        # For this implementation, let's assume the client sends the *full* history (minus system maybe)
                        # OR just the new user message.
                        # Based on frontend code: `history` is the full array of messages.
                        
                        input_history = payload["history"]
                        # Rebuild history: System Prompt + Input History
                        history = [{"role": "system", "content": system_prompt_content}] + input_history
                        
                        response_mode = payload.get("mode", "text")
                        logger.info(f"Chat Request Mode: {response_mode}. Received {len(input_history)} messages.")
                        
                        if response_mode == "audio":
                            # --- GENERATE AUDIO RESPONSE (Video Call) ---
                            await websocket.send_json({"type": "status", "status": "processing"})
                            
                            full_ai_response = ""
                            current_sentence = ""
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
                                        try:
                                            async for audio_chunk in tts_service.stream_audio(sentence_to_speak):
                                                sentence_audio.extend(audio_chunk)
                                            
                                            if len(sentence_audio) > 0:
                                                await websocket.send_bytes(bytes(sentence_audio))
                                                logger.info(f"Sent complete audio for sentence ({len(sentence_audio)} bytes).")
                                            else:
                                                logger.warning("TTS generated empty audio.")
                                        except Exception as e:
                                            logger.error(f"TTS Generation Error: {e}")
                                    
                                    current_sentence = ""

                            if current_sentence.strip():
                                logger.info(f"Generating TTS for final segment: {current_sentence.strip()}")
                                await websocket.send_json({"type": "transcript", "role": "assistant", "text": current_sentence.strip(), "partial": True})
                                
                                sentence_audio = bytearray()
                                try:
                                    async for audio_chunk in tts_service.stream_audio(current_sentence.strip()):
                                        sentence_audio.extend(audio_chunk)
                                    
                                    if len(sentence_audio) > 0:
                                        await websocket.send_bytes(bytes(sentence_audio))
                                        logger.info(f"Sent complete audio for final segment ({len(sentence_audio)} bytes).")
                                    else:
                                        logger.warning("TTS generated empty audio for final segment.")
                                except Exception as e:
                                    logger.error(f"TTS Generation Error (Final): {e}")

                            history.append({"role": "assistant", "content": full_ai_response})
                            await websocket.send_json({"type": "status", "status": "listening"})

                        else:
                            # --- STREAM TEXT RESPONSE (Chat Interface) ---
                            full_ai_response = ""
                            token_generator = llm_service.chat_stream(history)
                            
                            for token in token_generator:
                                full_ai_response += token
                                await websocket.send_text(token)
                            
                            history.append({"role": "assistant", "content": full_ai_response})

                    elif "user_text" in payload:
                         # Simple text injection
                         user_text = payload["user_text"]
                         history.append({"role": "user", "content": user_text})
                         # ... generate response ...

                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON text")

            elif "bytes" in message:
                # --- AUDIO MODE (Video Call) ---
                data = message["bytes"]
                
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
                    
                    # 2. Speech to Text (Run in thread to avoid blocking loop)
                    user_text = await asyncio.to_thread(stt_service.transcribe, bytes(speech_buffer))
                    
                    # Reset buffer immediately
                    speech_buffer = bytearray()
                    silence_counter = 0
                    
                    if not user_text or len(user_text.strip()) < 2:
                        logger.info(f"Ignored empty/short transcription: '{user_text}'")
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
    except RuntimeError as re:
        if "disconnect" in str(re) or "close" in str(re):
            logger.info(f"Client disconnected (RuntimeError): {re}")
        else:
            logger.error(f"RuntimeError: {re}", exc_info=True)
    except Exception as e:
        logger.error(f"Conversation Error: {e}", exc_info=True)
