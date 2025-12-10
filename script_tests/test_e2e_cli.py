import asyncio
import websockets
import json
import base64

async def test_full_pipeline():
    uri = "ws://localhost:8000/ai/stream"
    print(f"Connecting to {uri}...")
    
    async with websockets.connect(uri) as websocket:
        print("Connected.")
        
        # 1. Send Configuration
        config = {
            "mode": "audio", 
            "system_prompt": "You are a helpful test assistant. Say 'Test successful' and nothing else.",
            "history": []
        }
        await websocket.send(json.dumps(config))
        print("Sent Config.")
        
        # 2. Send User Input (simulated text injection to bypass STT/Microphone issues)
        # We need to see if the backend accepts "user_text" to trigger the flow.
        # Looking at conversation.py: 
        # elif "user_text" in payload: ...
        
        msg = {
            "user_text": "Hello, is this working?"
        }
        await websocket.send(json.dumps(msg))
        print("Sent Text Message.")

        # 3. Listen for responses
        print("Listening for response...")
        audio_bytes_received = 0
        transcript_received = False
        
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                
                if isinstance(response, bytes):
                    audio_bytes_received += len(response)
                    print(f"Received Audio Chunk: {len(response)} bytes")
                else:
                    try:
                        data = json.loads(response)
                        print(f"Received JSON: {data}")
                        if data.get("type") == "transcript" and data.get("role") == "assistant":
                            transcript_received = True
                    except:
                        print(f"Received Text: {response}")
                        
                if transcript_received and audio_bytes_received > 10000:
                    print("\nSUCCESS: Received both transcript and audio!")
                    break
                    
        except asyncio.TimeoutError:
            print("\nTimeout waiting for response.")
            if audio_bytes_received == 0:
                print("FAILURE: No audio received.")
            if not transcript_received:
                print("FAILURE: No transcript received.")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
