import asyncio
import websockets
import numpy as np
import soundfile as sf
import io
import base64
import time

# Configuration
WEBSOCKET_URL = "ws://localhost:8000/ai/avatar_stream"
SAMPLE_RATE = 16000 # Must match the SAMPLE_RATE in avatar_engine.py
CHUNK_SIZE_SECONDS = 0.1 # Send 100ms chunks
DURATIONS_SECONDS = 2 # Total duration of dummy audio

async def simulate_audio_stream():
    # Generate a dummy sine wave audio for testing
    num_samples = int(SAMPLE_RATE * DURATIONS_SECONDS)
    t = np.linspace(0, DURATIONS_SECONDS, num_samples, endpoint=False)
    # Simple sine wave, changing frequency
    audio_data = 0.5 * (np.sin(2 * np.pi * 440 * t) + np.sin(2 * np.pi * 880 * t * (1 + t/DURATIONS_SECONDS)))
    audio_data = audio_data.astype(np.float32)

    # Convert numpy array to bytes in WAV format
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, SAMPLE_RATE, format='WAV')
    full_audio_bytes = buffer.getvalue()

    # Split into chunks
    chunk_size_bytes = int(SAMPLE_RATE * CHUNK_SIZE_SECONDS * audio_data.itemsize) # Assuming float32
    
    print(f"Connecting to {WEBSOCKET_URL}...")
    async with websockets.connect(WEBSOCKET_URL) as websocket:
        print("Connected. Sending audio chunks...")
        
        # We need to send actual WAV formatted chunks, not just raw audio data
        # For simplicity, let's just send the raw float32 samples as bytes
        # The backend expects raw audio samples, so we'll simulate that
        
        # Loop through audio data and send chunks
        for i in range(0, len(audio_data), int(SAMPLE_RATE * CHUNK_SIZE_SECONDS)):
            chunk_samples = audio_data[i:i + int(SAMPLE_RATE * CHUNK_SIZE_SECONDS)]
            if len(chunk_samples) == 0:
                break
            
            # Convert float32 numpy array chunk to bytes
            audio_chunk_bytes = chunk_samples.tobytes()
            
            await websocket.send(audio_chunk_bytes)
            print(f"Sent chunk {i // int(SAMPLE_RATE * CHUNK_SIZE_SECONDS) + 1} with {len(audio_chunk_bytes)} bytes.")
            
            try:
                # Receive response (base64 image)
                response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                print(f"Received frame (first 50 chars): {response[:50]}...")
                # You can decode base64 and save as an image here if needed for visual inspection
            except asyncio.TimeoutError:
                print("No frame received for this chunk (timeout).")
            except Exception as e:
                print(f"Error receiving response: {e}")

            await asyncio.sleep(CHUNK_SIZE_SECONDS / 2) # Simulate real-time by waiting less than chunk duration

    print("Audio stream finished.")

if __name__ == "__main__":
    asyncio.run(simulate_audio_stream())
