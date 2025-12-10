import asyncio
import websockets

async def test_chat():
    uri = "ws://localhost:8000/ai/stream"
    async with websockets.connect(uri) as websocket:
        prompt = "Count from 1 to 5 quickly."
        print(f"Sent: {prompt}")
        await websocket.send(prompt)

        print("Received stream:", end=" ", flush=True)
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                print(response, end="", flush=True)
        except asyncio.TimeoutError:
            print("\nStream finished (timeout).")

if __name__ == "__main__":
    asyncio.run(test_chat())

