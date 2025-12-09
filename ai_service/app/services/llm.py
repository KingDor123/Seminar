import logging
import ollama
from typing import Generator, List, Dict
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Large Language Models (LLMs).
    
    Supports:
    - Ollama (via OpenAI-compatible API)
    - MLX-LM Server (via OpenAI-compatible API)
    """

    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model_name = settings.OLLAMA_MODEL
        # We use the OpenAI client because it is the standard for 
        # MLX-LM and modern Ollama endpoints.
        self.client = OpenAI(base_url=self.host, api_key="lm-studio")

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Streams the response from the LLM token by token.
        
        Args:
            messages: A list of message dictionaries (e.g., {"role": "user", "content": "..."})
            
        Yields:
            str: chunks of generated text.
        """
        try:
            logger.info(f"Initiating chat stream with model: {self.model_name} at {self.host}")
            
            # Dynamic Model Resolution:
            # Some servers (like MLX) require a valid model ID even if they only host one.
            # We fetch the list of available models to ensure we use a valid ID.
            try:
                models_response = self.client.models.list()
                if models_response.data:
                    # Use the first available model from the server
                    model_id = models_response.data[0].id
                    logger.debug(f"Resolved Server Model ID: {model_id}")
                else:
                    logger.warning("Server returned empty model list. Using default.")
                    model_id = "default"
            except Exception as e:
                logger.warning(f"Could not fetch models list ({e}). Fallback to 'default'.")
                model_id = "default"

            # Create the streaming completion request
            stream = self.client.chat.completions.create(
                model=model_id,
                messages=messages,
                stream=True,
                # Stop tokens to prevent the model from hallucinating roles or running indefinitely
                stop=["<|start_header_id|>", "<|eot_id|>", "user:", "User:"]
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"LLM Streaming Error: {e}", exc_info=True)
            yield f" I'm having trouble connecting to my brain right now. Error: {e}"