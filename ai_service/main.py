from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import ollama

app = FastAPI()

# Initialize the client to talk to the docker container 'ollama'
client = ollama.Client(host='http://ollama:11434')

class GenerateRequest(BaseModel):
    prompt: str

@app.get("/ai/ping")
def ping():
    return {"status": "ai ok"}

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

