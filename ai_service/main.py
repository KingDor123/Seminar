from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
import ollama
from avatar_engine import AvatarEngine
from video_gen import video_generator
import json
import edge_tts
import tempfile
import os
import uuid

app = FastAPI()
avatar_engine = AvatarEngine()
# Load the real avatar image
avatar_engine.load_avatar("avatar.png")

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

@app.post("/ai/video")
async def generate_video(request: TTSRequest):
    """
    Generates a Lip-Synced Video from text.
    1. TTS -> Audio
    2. Wav2Lip -> Video
    """
    try:
        # 1. Generate Audio
        communicate = edge_tts.Communicate(request.text, request.voice)
        audio_filename = f"/tmp/{uuid.uuid4()}.mp3"
        await communicate.save(audio_filename)
        
        # 2. Generate Video
        video_path = video_generator.generate_lip_sync(audio_filename)
        
        # Return Video
        return FileResponse(video_path, media_type="video/mp4", filename="response.mp4")

    except Exception as e:
        print(f"Video Generation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/tts")
async def generate_speech(request: TTSRequest):
    try:
        communicate = edge_tts.Communicate(request.text, request.voice)
        
        # Generate a unique filename
        filename = f"/tmp/{uuid.uuid4()}.mp3"
        await communicate.save(filename)
        
        # Return audio file
        return FileResponse(filename, media_type="audio/mpeg", filename="speech.mp3")
    except Exception as e:
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

@app.websocket("/ai/avatar_stream")
async def avatar_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Expecting a float value as text (amplitude 0.0 - 1.0)
            data = await websocket.receive_text()
            try:
                amplitude = float(data)
                # Generate frame
                frame_base64 = avatar_engine.process_audio_frame(amplitude)
                if frame_base64:
                    await websocket.send_text(frame_base64)
            except ValueError:
                pass # Ignore non-float messages
    except WebSocketDisconnect:
        print("Avatar Stream Client disconnected")
    except Exception as e:
        print(f"Avatar Stream Error: {e}")

@app.websocket("/ai/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Wait for the user to send a prompt
            prompt = await websocket.receive_text()
            print(f"Received prompt: {prompt}")
            
            # Stream response from Ollama
            stream = client.chat(
                model='llama3',
                messages=[
                    {
                        'role': 'system',
                        'content': (
                            "You are a roleplay partner designed to help people practice social skills. "
                            "You are simulating a realistic human interaction. "
                            "1. Stay in character at all times. "
                            "2. Reply in the SAME language the user speaks (English, Hebrew, etc.). "
                            "3. Keep your responses concise (1-3 sentences) like a real conversation. "
                            "4. Do not act like an AI assistant. Act like the person in the scenario."
                        ),
                    },
                    {'role': 'user', 'content': prompt}
                ],
                stream=True,
            )

            for chunk in stream:
                content = chunk['message']['content']
                if content:
                    await websocket.send_text(content)
            
            # Optional: Send a special token or message to indicate done, 
            # but for now we just wait for the next prompt.
            
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")

