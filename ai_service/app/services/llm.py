import logging
from typing import AsyncGenerator, List, Dict, Any
from openai import AsyncOpenAI
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
        # Initialize AsyncOpenAI client pointing to our local Ollama instance
        self.client = AsyncOpenAI(base_url=self.host, api_key="ollama")

    async def chat_stream(self, messages: List[Dict[str, str]], metadata: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """
        Streams the LLM response token by token asynchronously.
        Injects behavioral context if the user is struggling.
        """
        try:
            logger.info(f"🧠 Thinking with {self.model_name}...")
            
            # --- Behavioral Injection Logic ---
            if metadata and messages and messages[-1]["role"] == "user":
                wpm = metadata.get("wpm", 0.0)
                latency = metadata.get("latency", 0.0)
                fillers = metadata.get("filler_count", 0)
                
                # Thresholds
                notes = []
                if wpm > 160:
                    notes.append(f"speaking very fast ({int(wpm)} WPM)")
                elif wpm < 100 and wpm > 0:
                    notes.append(f"speaking slowly ({int(wpm)} WPM)")
                
                if latency > 5.0: # Seconds
                    notes.append(f"took a long time to respond ({int(latency)}s)")
                
                if fillers > 2:
                    notes.append(f"is using many filler words ({fillers})")

                if notes:
                    observation = f"[SYSTEM OBSERVER: User is {', '.join(notes)}. Acknowledge this gently/implicitly.]"
                    # Prepend to the last user message
                    last_content = messages[-1]["content"]
                    messages[-1]["content"] = f"{observation}\nUser: {last_content}"
                    logger.info(f"💉 Injected Context: {observation}")

            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                stream=True,
                stop=["<|start_header_id|>", "<|eot_id|>", "user:", "User:"]
            )

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"❌ LLM Error: {e}")
            yield " ... (My brain connection timed out)."

    async def analyze_behavior(
        self, 
        user_text: str, 
        context: str, 
        behavior_context: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Analyzes the user's response including behavioral metrics.
        Returns a dictionary with 'sentiment', 'topic_adherence', 'confidence', etc.
        """
        if behavior_context is None:
            behavior_context = {}
            
        latency = behavior_context.get("latency", 0.0)
        wpm = behavior_context.get("wpm", 0.0)
        fillers = behavior_context.get("fillers", 0)
        pauses = behavior_context.get("pauses", 0)

        # --- Deterministic Calculation (No LLM) ---
        
        # Clarity Score: Penalize for fillers and pauses
        # Base 1.0
        clarity_penalty = (fillers * 0.1) + (pauses * 0.05)
        clarity = max(0.0, 1.0 - clarity_penalty)

        # Confidence Score: Penalize for latency, low WPM, and fillers
        # Base 1.0
        confidence_penalty = 0.0
        if latency > 2.0: confidence_penalty += 0.2
        if wpm < 100: confidence_penalty += 0.2
        confidence_penalty += (fillers * 0.05)
        confidence = max(0.0, 1.0 - confidence_penalty)

        # --- LLM Analysis (Subjective Metrics) ---

        prompt = (
            f"Analyze the user's response in this conversation context.\n"
            f"Context (AI said): \"{context}\"\n"
            f"User replied: \"{user_text}\"\n\n"
            f"Provide a JSON object with these metrics:\n"
            f"1. 'sentiment': float -1.0 (negative) to 1.0 (positive).\n"
            f"2. 'topic_adherence': float 0.0 (off-topic) to 1.0 (on-topic).\n"
            f"Only return the JSON object, nothing else."
        )

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )
            content = response.choices[0].message.content.strip()
            
            # Robust JSON extraction
            # 1. Strip Markdown code blocks
            if "```" in content:
                content = content.replace("```json", "").replace("```", "")
            
            import re
            # 2. Find the first valid JSON object
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            
            import json
            llm_metrics = json.loads(content)
        except Exception as e:
            logger.error(f"❌ Analysis Error: {e} | Content was: {content if 'content' in locals() else 'Unknown'}")
            llm_metrics = {
                "sentiment": 0.0, 
                "topic_adherence": 0.0
            }

        # Merge Deterministic and LLM Metrics
        return {
            "sentiment": float(llm_metrics.get("sentiment", 0.0)),
            "topic_adherence": float(llm_metrics.get("topic_adherence", 0.0)),
            "clarity": round(clarity, 2),
            "confidence_estimate": round(confidence, 2)
        }
