import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for the FastAPI application.
    Handles startup and shutdown events.
    """
    
    logger.info("🚀 Starting SoftSkill AI Service...")
    logger.info(f"   - LLM Host: {settings.OLLAMA_HOST}")
    logger.info(f"   - Whisper Model: {settings.WHISPER_MODEL_SIZE}")
    logger.info(f"   - TTS Voice: {settings.TTS_VOICE}")
        
    yield
    
    # --- Shutdown Phase ---
    logger.info("🛑 Shutting down SoftSkill AI Service...")