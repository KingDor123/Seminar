import ollama
import logging
from typing import List, Dict, Any, AsyncGenerator

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model: str = "aya:8b"):
        """
        Initializes the LLM service with a specific model.
        Default model is aya:8b as per project requirements.
        """
        self.model = model
        self.client = ollama.AsyncClient()

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Generates a full response from the LLM for a given list of messages.
        """
        try:
            logger.info(f"Generating response with model {self.model}")
            response = await self.client.chat(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Error generating response from LLM: {e}")
            raise

    async def stream_response(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Streams response tokens from the LLM for a given list of messages.
        """
        try:
            logger.info(f"Streaming response with model {self.model}")
            # The ollama-python client's chat method with stream=True returns an AsyncIterator
            async for part in await self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                **kwargs
            ):
                content = part.get('message', {}).get('content', '')
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Error streaming response from LLM: {e}")
            raise