import os
import logging
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application Configuration
    
    Manages environment variables and application settings.
    Default values are provided for local development (Docker).
    """

    # --- AI Configuration ---
    # Host for the MLX/Ollama Server. 
    # 'host.docker.internal' allows the container to access the host machine's localhost.
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://host.docker.internal:8081/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "models/softskill-llama3.2-3b") 
    
    # --- Whisper (STT) Configuration ---
    # Model size options: 'tiny', 'base', 'small', 'medium', 'large-v2'
    # 'base.en' is chosen for a balance of latency and accuracy on CPU.
    WHISPER_MODEL_SIZE: str = "base.en" 
    
    # Device configuration for faster-whisper.
    # On macOS (Apple Silicon), 'cpu' with 'int8' quantization is often 
    # the most optimized path when using CTranslate2 (backend of faster-whisper).
    WHISPER_DEVICE: str = "cpu" 
    WHISPER_COMPUTE_TYPE: str = "int8"
    
    # --- TTS Configuration ---
    # Voice identifier for EdgeTTS (Microsoft Azure Speech).
    TTS_VOICE: str = "en-US-AriaNeural"

    # --- System Configuration ---
    # Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"

settings = Settings()

# --- Global Logging Setup ---
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SoftSkillAI")
