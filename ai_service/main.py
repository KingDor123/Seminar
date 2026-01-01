from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import conversation, analytics
from app.core.lifespan import lifespan

app = FastAPI(
    title="SoftSkill AI Service",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversation.router, prefix="/ai")
app.include_router(analytics.router, prefix="/analytics")

@app.get("/ai/health")
def health_check():
    return {
        "status": "ok",
        "service": "ai_service",
        "config": {
            "whisper": settings.WHISPER_MODEL_SIZE,
            "llm": settings.OLLAMA_MODEL
        }
    }
