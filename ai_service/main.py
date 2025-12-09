from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import conversation
from app.core.lifespan import lifespan

# Initialize the FastAPI application
app = FastAPI(
    title="SoftSkill AI Service",
    description="Microservice for AI-driven soft skills training (LLM, STT, TTS).",
    version="2.0.0",
    lifespan=lifespan # Hooks up startup/shutdown logic
)

# --- CORS Configuration ---
# Allow all origins for development ease. 
# In production, restrict this to the frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Router Registration ---
app.include_router(conversation.router)

@app.get("/ai/health")
def health_check():
    """
    Health check endpoint.
    Returns status and current configuration summary.
    """
    return {
        "status": "ok",
        "service": "ai_service",
        "config": {
            "whisper_model": settings.WHISPER_MODEL_SIZE,
            "llm_host": settings.OLLAMA_HOST,
            "tts_voice": settings.TTS_VOICE
        }
    }