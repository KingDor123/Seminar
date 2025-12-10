import logging
from typing import Generator, List, Dict
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for interacting with Large Language Models (LLMs) via OpenAI-compatible API.
    Target: Ollama (running Llama 3.2)
    """

    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.model_name = settings.OLLAMA_MODEL
        # Initialize OpenAI client pointing to our local Ollama instance
        self.client = OpenAI(base_url=self.host, api_key="ollama")

    def chat_stream(self, messages: List[Dict[str, str]]) -> Generator[str, None, None]:
        """
        Streams the LLM response token by token.
        """
        try:
            logger.info(f"🧠 Thinking with {self.model_name}...")

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                stop=["<|start_header_id|>", "<|eot_id|>", "user:", "User:"]
            )

            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"❌ LLM Error: {e}")
            yield " ... (My brain connection timed out)."