from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import conversation

app = FastAPI(title="SoftSkill AI Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(conversation.router)

@app.get("/ai/health")
def health_check():
    return {
        "status": "ok",
        "config": {
            "whisper": settings.WHISPER_MODEL_SIZE,
            "llm": settings.OLLAMA_MODEL
        }
    }
