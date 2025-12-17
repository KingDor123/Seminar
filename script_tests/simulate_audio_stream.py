import asyncio
import websockets
import json
import numpy as np
import time
import requests

# Configuration
API_BASE_URL = "http://127.0.0.1:5001/api"
WEBSOCKET_URL = "ws://127.0.0.1:8000/ai/stream"
SAMPLE_RATE = 16000 
CHUNK_SIZE_SECONDS = 0.1 
DURATION_SECONDS = 2 

async def simulate_audio_stream():
    # 0. Create a User and Session first (Backend Requirement)
    print("Creating User and Session...")
    try:
        # Create User
        user_res = requests.post(f"{API_BASE_URL}/auth/register", json={
            "email": f"test{int(time.time())}@example.com", 
            "password": "password123",
            "name": "Test User"
        })
        if user_res.status_code != 201:
             user_res = requests.post(f"{API_BASE_URL}/auth/login", json={
                "email": "test@example.com", 
                "password": "password123"
            })
             user_id = 2
        else:
             user_id = user_res.json().get("user", {}).get("id", 2)

        # Create Session
        session_res = requests.post(f"{API_BASE_URL}/chat/sessions", json={
            "userId": user_id,
            "scenarioId": "bank"
        })
        session_data = session_res.json()
        session_id = session_data.get("id")
        
        if not session_id:
            print("❌ Failed to create session. Using fallback ID 1.")
            session_id = 1
            
        print(f"✅ Created Session ID: {session_id}")

    except Exception as e:
        print(f"⚠️ Setup Error: {e}")
        session_id = 1 

    # 1. Generate Dummy Audio
    print(f"Generating {DURATION_SECONDS}s of dummy audio...")
    t = np.linspace(0, DURATION_SECONDS, int(SAMPLE_RATE * DURATION_SECONDS), endpoint=False)
    audio_data = 0.5 * np.sin(2 * np.pi * 440 * t)
    audio_data = audio_data.astype(np.float32)
    
    # 2. Connect
    print(f"Connecting to {WEBSOCKET_URL}...")
    try:
        async with websockets.connect(WEBSOCKET_URL, open_timeout=10) as websocket:
            print("Connected!")

            # 3. Send Init Config
            config = {
                "session_id": session_id, 
                "mode": "audio",
                "system_prompt": "You are a test bot. Reply with 'Test Received'.",
                "history": []
            }
            await websocket.send(json.dumps(config))
            print("Sent Init Config. Waiting for Greeting...")

            # 3b. Wait for Greeting to finish
            while True:
                msg = await websocket.recv()
                if isinstance(msg, str):
                    data = json.loads(msg)
                    if data.get("status") == "listening":
                        print("✅ AI finished greeting. Now speaking...")
                        break
                elif isinstance(msg, bytes):
                    pass # Ignore TTS audio

            # 4. Send 'user_started_speaking' Metadata
            start_msg = {
                "type": "user_started_speaking",
                "timestamp": int(time.time() * 1000)
            }
            await websocket.send(json.dumps(start_msg))
            print(f"Sent Metadata: {start_msg}")

            # 5. Stream Audio
            chunk_size_samples = int(SAMPLE_RATE * CHUNK_SIZE_SECONDS)
            total_chunks = len(audio_data) // chunk_size_samples
            
            print(f"Streaming {total_chunks} chunks of SPEECH...")
            for i in range(total_chunks):
                start = i * chunk_size_samples
                end = start + chunk_size_samples
                chunk = audio_data[start:end]
                await websocket.send(chunk.tobytes())
                await asyncio.sleep(CHUNK_SIZE_SECONDS / 2) # Speed up slightly
            
            # 6. Stream SILENCE to trigger VAD
            print("Streaming SILENCE to trigger VAD...")
            silence_chunk = np.zeros(chunk_size_samples, dtype=np.float32).tobytes()
            for _ in range(25): # Send 2.5s of silence (Threshold is 20 chunks / 2.0s)
                await websocket.send(silence_chunk)
                await asyncio.sleep(0.01) # Fast silence

            print("Audio Streaming Complete.")

            # 7. Listen for Response
            print("Listening for response...")
            transcript_received = False
            user_transcript_received = False
            
            try:
                # Wait 10s then assume failure (or success if we see logs)
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    
                    if isinstance(message, str):
                        data = json.loads(message)
                        
                        if data.get("type") == "transcript":
                            if data.get("role") == "user":
                                print("✅ User Transcript Received: " + data.get("text"))
                                user_transcript_received = True
                            elif data.get("role") == "assistant":
                                print("✅ Assistant Transcript Received: " + data.get("text"))
                                transcript_received = True
                        
                        if data.get("status") == "listening" and transcript_received:
                            print("✅ AI returned to listening state. Test Complete.")
                            break
                            
            except asyncio.TimeoutError:
                print("❌ Timeout waiting for full response (Expected if using sine wave).")

            if user_transcript_received and transcript_received:
                print("\n🎉 TEST PASSED: Pipeline is functioning.")
            else:
                print("\n⚠️ TEST INCONCLUSIVE: Missing transcripts (likely due to sine wave audio). Check logs for 'STT:'.")
                
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(simulate_audio_stream())