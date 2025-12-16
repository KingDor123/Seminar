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

    def analyze_behavior(self, user_text: str, context: str) -> Dict[str, float]:
        """
        Analyzes the user's response for soft skills metrics.
        Returns a dictionary with 'sentiment', 'topic_adherence', etc.
        """
        prompt = (
            f"Analyze the user's response in this conversation context.\n"
            f"Context (AI said): \"{context}\"\n"
            f"User replied: \"{user_text}\"\n\n"
            f"Provide a JSON object with:\n"
            f"1. 'sentiment': float between -1.0 (negative) and 1.0 (positive).\n"
            f"2. 'topic_adherence': float between 0.0 (off-topic) and 1.0 (on-topic).\n"
            f"3. 'clarity': float between 0.0 (confusing) and 1.0 (clear).\n"
            f"Only return the JSON object, nothing else."
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            content = response.choices[0].message.content.strip()
            
            # Robust JSON extraction
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"❌ Analysis Error: {e} | Content was: {content if 'content' in locals() else 'Unknown'}")
            return {"sentiment": 0.0, "topic_adherence": 0.0, "clarity": 0.0}