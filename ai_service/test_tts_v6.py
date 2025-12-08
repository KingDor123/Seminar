import asyncio
import edge_tts

VOICE = "en-US-AriaNeural"
TEXT = "Testing downgrade to version 6."

async def main():
    communicate = edge_tts.Communicate(TEXT, VOICE)
    try:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                print(f"Received audio chunk: {len(chunk['data'])} bytes")
                break # Success!
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
