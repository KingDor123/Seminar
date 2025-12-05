import logging
import ollama
from app.core.config import settings
from typing import Generator, List, Dict
import httpx

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Using standard Ollama Client (compatible with OpenAI-like servers)
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Streams the response from the LLM token by token.
        """
        try:
            logger.info(f"Sending request to LLM ({self.model})...")
            # Note: mlx-lm server uses OpenAI format, but Ollama client is compatible 
            # IF the server endpoints match. 
            # If mlx-lm server is purely OpenAI, we might need the `openai` client instead.
            # But let's try standard Ollama client first as it's simpler.
            # Actually, standard Ollama client expects /api/chat. MLX server exposes /v1/chat/completions.
            # We should use the OpenAI client or raw requests.
            
            # Using OpenAI client is safer for MLX server compatibility.
            from openai import OpenAI
            client = OpenAI(base_url=settings.OLLAMA_HOST, api_key="lm-studio")
            
            # Dynamic Model Resolution
            # We ask the server what model it is running to avoid "Repository Not Found" errors
            try:
                models_response = client.models.list()
                # Pick the first available model
                model_id = models_response.data[0].id
                logger.info(f"Detected Server Model ID: {model_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch models list: {e}. Fallback to 'default'.")
                model_id = "default"

            stream = client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"LLM Error: {e}")
            yield f"I'm having trouble thinking right now. Error: {e}"
