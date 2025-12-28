import os
import logging
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application Configuration
    """

    # --- AI ---
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434/v1")
    OLLAMA_MODEL: str = os.getenv("MODEL_NAME", "aya:8b")

    # --- Whisper (STT) ---
    WHISPER_MODEL_SIZE: str = "medium"
    # On Mac M1/M2/M3, 'cpu' + 'int8' is usually the sweet spot for faster-whisper
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"

    # --- Logging ---
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"

settings = Settings()

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("SoftSkillAI")
