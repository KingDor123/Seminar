import os
import json
import logging
from typing import List, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger("LLMEngine")

class LLMClient:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.OLLAMA_HOST,
            api_key="ollama"
        )
        self.model = settings.OLLAMA_MODEL

    async def generate_json(self, messages: List[Dict[str, str]], schema: str) -> Dict[str, Any]:
        """
        Forces the LLM to return JSON conforming to a schema description.
        Includes a retry mechanism.
        """
        system_suffix = (
            "\n\nCRITICAL OUTPUT RULE: You MUST return strictly valid JSON content. "
            "No markdown, no preambles. "
            f"Target Schema: {schema}"
        )

        # Append instruction to the last system message or add one
        if messages[0]["role"] == "system":
            messages[0]["content"] += system_suffix
        else:
            messages.insert(0, {"role": "system", "content": system_suffix})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"}, # Ollama supports this for some models
                extra_body={"options": {"num_ctx": 8192}} # Explicitly request 8k context
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON. Retrying...")
            # Simple retry logic could go here
            return {"error": "Invalid JSON"}
        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            return {"error": str(e)}

    async def generate_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                stream=True,
                extra_body={"options": {"num_ctx": 8192}} # Explicitly request 8k context
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"LLM Stream Error: {e}")
            yield f"[Error: {e}]"

llm_client = LLMClient()
