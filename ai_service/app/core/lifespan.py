import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from mlx_lm import load
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global Model Variables
mlx_model = None
mlx_tokenizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global mlx_model, mlx_tokenizer
    
    model_path = "/app/models/softskill-llama3.2-3b"
    logger.info(f"🔥 Loading MLX Model from {model_path}...")
    
    try:
        # Load the model directly into memory
        mlx_model, mlx_tokenizer = load(model_path)
        logger.info("✅ MLX Model Loaded Successfully!")
    except Exception as e:
        logger.error(f"❌ Failed to load MLX model: {e}")
        # Fallback or exit? We'll log it.
        
    yield
    
    # Cleanup if needed
    logger.info("Shutting down...")
