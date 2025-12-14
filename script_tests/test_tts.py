import asyncio
import edge_tts

VOICE = "en-US-AriaNeural"
TEXT = "Hello, this is a test of the edge text to speech system."

async def main():
    print(f"Testing EdgeTTS connection with voice: {VOICE}...")
    try:
        communicate = edge_tts.Communicate(TEXT, VOICE)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                print(f"✅ Received audio chunk ({len(chunk['data'])} bytes)")
                break # Success
        print("🎉 EdgeTTS is working on your host machine!")
    except Exception as e:
        print(f"❌ EdgeTTS Failed on host: {e}")

if __name__ == "__main__":
    asyncio.run(main())