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
    

    # No pre-loading needed for state-machine engine as it's purely API-based (Ollama)

    yield

    logger.info("🛑 Service Shutting Down...")
