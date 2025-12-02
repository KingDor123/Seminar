import asyncio
import websockets

async def test_proxy():
    uri = "ws://localhost:5001/api/chat"
    print(f"Connecting to {uri}...")
    async with websockets.connect(uri) as websocket:
        prompt = "Tell me a joke about proxies."
        print(f"Sent: {prompt}")
        await websocket.send(prompt)

        print("Received stream:", end=" ", flush=True)
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                if isinstance(response, bytes):
                     response = response.decode('utf-8')
                print(response, end="", flush=True)
        except asyncio.TimeoutError:
            print("\nStream finished (timeout).")
        except websockets.exceptions.ConnectionClosed:
            print("\nConnection closed by server.")

if __name__ == "__main__":
    asyncio.run(test_proxy())
