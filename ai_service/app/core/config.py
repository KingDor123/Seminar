import os
import logging

class Settings:
    # AI Configuration
    # Pointing to Host Machine MLX Server (port 8081 due to Jenkins on 8080)
    # 'host.docker.internal' works on Mac Docker Desktop to reach localhost
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://host.docker.internal:8081/v1")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "models/softskill-llama3.2-3b") 
    
    # Whisper Configuration
    # 'tiny', 'base', 'small', 'medium', 'large-v2'
    # On M2 Pro, 'small' or 'base' is a good trade-off for latency vs accuracy.
    WHISPER_MODEL_SIZE: str = "base.en" 
    WHISPER_DEVICE: str = "cpu" # faster-whisper on Mac uses CPU with CTranslate2 (optimized)
    WHISPER_COMPUTE_TYPE: str = "int8" # int8 is faster on CPU
    
    # TTS Configuration
    TTS_VOICE: str = "en-US-AriaNeural"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()

# Configure Global Logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SoftSkillAI")