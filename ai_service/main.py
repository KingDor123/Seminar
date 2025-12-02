from fastapi import FastAPI

app = FastAPI()

@app.get("/ai/ping")
def ping():
    return {"status": "ai ok"}
