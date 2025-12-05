import logging
import ollama
from app.core.config import settings
from typing import Generator, List, Dict

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Streams the response from the LLM token by token.
        """
        try:
            logger.info(f"Sending request to LLM ({self.model})...")
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )

            for chunk in stream:
                content = chunk['message']['content']
                if content:
                    yield content

        except Exception as e:
            logger.error(f"LLM Error: {e}")
            yield f"I'm having trouble thinking right now. Error: {e}"

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Non-streaming chat.
        """
        try:
            response = self.client.chat(model=self.model, messages=messages)
            return response['message']['content']
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return "Sorry, I couldn't process that."
