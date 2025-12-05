from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel
import ollama
import edge_tts
import uuid
import logging
import json

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize the client to talk to the docker container 'ollama'
client = ollama.Client(host='http://ollama:11434')

class GenerateRequest(BaseModel):
    prompt: str

class TTSRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural" 

@app.get("/ai/ping")
def ping():
    return {"status": "ai ok"}

import base64

# ... (imports)

@app.post("/ai/tts")
async def generate_speech(request: TTSRequest):
    try:
        communicate = edge_tts.Communicate(request.text, request.voice)
        
        audio_data = b""
        word_timings = []

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                # chunk is dict: {"offset": 123, "duration": 456, "text": "hello"}
                # offset and duration are in 100ns units (ticks)
                # Convert to seconds: ticks / 10,000,000
                word_timings.append({
                    "start": chunk["offset"] / 1e7,
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                    "word": chunk["text"]
                })

        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
        
        return {"audio": audio_base64, "visemes": word_timings}
    except Exception as e:
        logger.error(f"TTS Generation Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/generate")
def generate_text(request: GenerateRequest):
    try:
        response = client.chat(model='llama3.2', messages=[
          {
            'role': 'user',
            'content': request.prompt,
          },
        ])
        return {"response": response['message']['content']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ai/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("Chat WebSocket connected")
    try:
        while True:
            # Wait for the user to send a JSON payload
            data_text = await websocket.receive_text()
            
            try:
                data = json.loads(data_text)
                system_prompt = data.get("system_prompt", "You are a helpful assistant.")
                history = data.get("history", []) # List of {role, content}
                
                # Construct messages for Ollama
                messages = [{'role': 'system', 'content': system_prompt}]
                messages.extend(history)
                
                logger.info(f"Received request with history length: {len(history)}")

                # Stream response from Ollama
                stream = client.chat(
                    model='llama3',
                    messages=messages,
                    stream=True,
                )

                for chunk in stream:
                    content = chunk['message']['content']
                    if content:
                        await websocket.send_text(content)

            except json.JSONDecodeError:
                # Fallback for legacy plain text prompts (if any)
                logger.warning("Received non-JSON prompt, falling back to simple chat.")
                stream = client.chat(
                    model='llama3',
                    messages=[{'role': 'user', 'content': data_text}],
                    stream=True,
                )
                for chunk in stream:
                    if chunk['message']['content']:
                        await websocket.send_text(chunk['message']['content'])
            
    except WebSocketDisconnect:
        logger.info("Client disconnected")
    except Exception as e:
        logger.error(f"Chat WebSocket Error: {e}", exc_info=True)
        await websocket.send_text(f"Error: {str(e)}")