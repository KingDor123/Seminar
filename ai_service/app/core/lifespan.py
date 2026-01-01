import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 SoftSkill AI Service Online")
    logger.info(f"   - LLM: {settings.OLLAMA_MODEL} @ {settings.OLLAMA_HOST}")
    logger.info(f"   - STT: {settings.WHISPER_MODEL_SIZE}")

    # Initialize HybridPipeline Singleton on startup to pre-load models
    try:
        from app.routers.conversation import get_pipeline
        logger.info("📦 Pre-loading HybridPipeline models...")
        get_pipeline()
        logger.info("✅ HybridPipeline models loaded and ready.")
    except Exception as e:
        logger.error(f"❌ Failed to pre-load HybridPipeline: {e}")
        
    yield
    
    logger.info("🛑 Service Shutting Down...")