import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from openai import AsyncOpenAI
import torch.nn.functional as F

from app.core.config import settings
from app.schemas import AyaAnalysis

# Configure logger
logger = logging.getLogger("HybridPipeline")

AYA_ANALYSIS_SCHEMA = (
    '{"sentiment":"positive|negative|neutral","confidence":0.0,'
    '"reasoning":"...","detected_intent":"...","social_impact":"..."}'
)

class HybridPipeline:
    """
    A serial processing pipeline designed for High-Performance Computing (HPC) environments.
    
    Architecture:
    1. Text Normalization (Unicode/Whitespace only, preserving Hebraic morphology).
    2. Contextual Analysis (Aya LLM as primary reasoning engine; HeBERT optional fallback).
    3. Context Injection (Dynamic Prompt Enrichment & Persona Mixer).
    4. Generative Response (Aya LLM via Ollama API).
    """

    def __init__(self, device: Optional[str] = None):
        """
        Initialize the pipeline models.
        
        Args:
            device (str, optional): Computation device ('cuda' or 'cpu'). 
                                    Defaults to auto-detection.
        """
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🚀 Initializing HybridPipeline on device: {self.device}")

        # --- Optional HeBERT (Fallback Sentiment) ---
        self.enable_hebert = settings.ENABLE_HEBERT
        self.hebert_model_name = "avichr/heBERT_sentiment_analysis"
        self.tokenizer = None
        self.sentiment_model = None
        if self.enable_hebert:
            try:
                logger.info(f"Loading HeBERT model: {self.hebert_model_name}...")
                self.tokenizer = AutoTokenizer.from_pretrained(self.hebert_model_name)
                self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(self.hebert_model_name)
                self.sentiment_model.to(self.device)
                self.sentiment_model.eval() # Set to evaluation mode
                logger.info("✅ HeBERT loaded successfully.")
            except Exception as e:
                logger.error(f"❌ Failed to load HeBERT: {e}")
                self.tokenizer = None
                self.sentiment_model = None

        # --- Initialize Aya LLM Client (via Ollama) ---
        # Using AsyncOpenAI client as established in the project's LLM service
        # Assumes the Ollama instance is hosting the 'aya' model or similar.
        self.llm_client = AsyncOpenAI(
            base_url=settings.OLLAMA_HOST,
            api_key="ollama" # Required placeholder for local Ollama
        )
        # Use the configured model name from settings
        self.llm_model_name = settings.OLLAMA_MODEL
        logger.info(f"✅ LLM Client initialized for model: {self.llm_model_name} @ {settings.OLLAMA_HOST}")


    def _normalize_text(self, text: str) -> str:
        """
        Step A: Normalization
        Cleans unicode artifacts and excessive whitespace.
        CRITICAL: Preserves Hebrew stop-words and morphological prefixes 
        (unlike standard English cleaning).
        """
        if not text:
            return ""
        
        # Replace non-breaking spaces and other unicode whitespace variants
        text = text.replace("\u00A0", " ")
        
        # Collapse multiple spaces into one
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def _normalize_sentiment_label(self, value: str) -> str:
        normalized = value.strip().lower()
        if normalized.startswith("label_"):
            mapping = {"label_0": "neutral", "label_1": "positive", "label_2": "negative"}
            return mapping.get(normalized, "neutral")
        if normalized in ["positive", "negative", "neutral"]:
            return normalized
        if normalized in ["joy"]:
            return "positive"
        if normalized in ["sadness", "anger", "stress", "fear"]:
            return "negative"
        return "neutral"

    def _extract_json(self, text: str) -> Dict[str, Any]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return {}
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            return {}

    def _coerce_analysis(self, data: Dict[str, Any]) -> AyaAnalysis:
        sentiment = self._normalize_sentiment_label(str(data.get("sentiment", "neutral")))
        confidence_raw = data.get("confidence", 0.0)
        try:
            confidence = float(confidence_raw)
        except Exception:
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))

        return AyaAnalysis(
            sentiment=sentiment,
            confidence=confidence,
            reasoning=str(data.get("reasoning", "No valid analysis returned.")),
            detected_intent=str(data.get("detected_intent", "unknown")),
            social_impact=str(data.get("social_impact", "unknown")),
        )

    def _parse_aya_analysis(self, content: str) -> Optional[AyaAnalysis]:
        data = self._extract_json(content)
        if not data:
            return None
        try:
            return AyaAnalysis(**data)
        except Exception as e:
            logger.warning(f"⚠️ Aya analysis validation failed: {e}")
            return None

    def _fallback_analysis(self) -> AyaAnalysis:
        return self._coerce_analysis(
            {
                "sentiment": "neutral",
                "confidence": 0.35,
                "reasoning": "Fallback analysis used due to invalid Aya output.",
                "detected_intent": "unknown",
                "social_impact": "unknown",
            }
        )

    async def _call_aya(self, messages: List[Dict[str, str]], temperature: float = 0.1, max_tokens: int = 200) -> str:
        response = await self.llm_client.chat.completions.create(
            model=self.llm_model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    async def _analyze_with_aya(
        self,
        history: List[Dict[str, str]],
        last_user_message: str,
        persona: str,
        scenario_goal: str,
    ) -> AyaAnalysis:
        system_prompt = (
            "You are a strict conversational analyst for role-play simulations.\n"
            "Classify the user's last message relative to the conversation context and scenario goal.\n"
            "Return ONLY a single JSON object with keys: sentiment, confidence, reasoning, detected_intent, social_impact.\n"
            "Sentiment must be one of: positive, negative, neutral.\n"
            "Confidence must be a float between 0.0 and 1.0.\n"
            "Reasoning must be short and grounded in context.\n"
            f"Schema: {AYA_ANALYSIS_SCHEMA}\n"
            "Do NOT include extra keys, prose, or markdown."
        )

        payload = {
            "conversation_history": history,
            "last_user_message": last_user_message,
            "role_persona": persona,
            "scenario_goal": scenario_goal,
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]

        try:
            content = await self._call_aya(messages, temperature=0.0, max_tokens=200)
            logger.info(f"🔎 Aya analysis raw output: {content}")
            analysis = self._parse_aya_analysis(content)
            if analysis:
                logger.info(
                    f"✅ Aya analysis parsed: sentiment={analysis.sentiment} "
                    f"confidence={analysis.confidence:.2f}"
                )
                return analysis

            logger.warning("⚠️ Aya analysis invalid JSON; retrying with corrective prompt.")
            retry_prompt = (
                "Fix the following output to valid JSON ONLY that matches the schema:\n"
                f"{AYA_ANALYSIS_SCHEMA}\n"
                "Return ONLY JSON, no extra text."
            )
            retry_messages = [
                {"role": "system", "content": retry_prompt},
                {"role": "user", "content": content},
            ]
            retry_content = await self._call_aya(retry_messages, temperature=0.0, max_tokens=200)
            logger.info(f"🔁 Aya analysis retry output: {retry_content}")
            retry_analysis = self._parse_aya_analysis(retry_content)
            if retry_analysis:
                logger.info(
                    f"✅ Aya analysis parsed after retry: sentiment={retry_analysis.sentiment} "
                    f"confidence={retry_analysis.confidence:.2f}"
                )
                return retry_analysis
            logger.error("❌ Aya analysis failed after retry; using fallback.")
        except Exception as e:
            logger.error(f"⚠️ Aya analysis failed: {e}")

        if self.enable_hebert:
            fallback = self._analyze_sentiment_hebert(last_user_message)
            return self._coerce_analysis(
                {
                    "sentiment": fallback.get("sentiment", "neutral"),
                    "confidence": fallback.get("confidence", 0.0),
                    "reasoning": "Fallback sentiment from HeBERT on user text.",
                    "detected_intent": "unknown",
                    "social_impact": "unknown",
                }
            )

        return self._fallback_analysis()

    def _analyze_sentiment_hebert(self, text: str) -> Dict[str, Any]:
        """
        Optional fallback: HeBERT sentiment inference (not the primary reasoning engine).
        """
        if not self.sentiment_model or not self.tokenizer:
            return {"sentiment": "unknown", "confidence": 0.0}
        try:
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            ).to(self.device)

            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)

            probs = F.softmax(outputs.logits, dim=-1)
            confidence, predicted_class_idx = torch.max(probs, dim=-1)

            labels = self.sentiment_model.config.id2label
            if not labels:
                labels = {0: "neutral", 1: "positive", 2: "negative"}

            sentiment_label = labels.get(predicted_class_idx.item(), "unknown")
            score = confidence.item()

            return {
                "sentiment": sentiment_label,
                "confidence": score,
                "logits": outputs.logits.cpu().numpy().tolist()
            }

        except Exception as e:
            logger.error(f"⚠️ HeBERT Inference Failed: {e}")
            return {"sentiment": "unknown", "confidence": 0.0}

    def _get_contextual_instruction(self, sentiment: str, difficulty: str) -> str:
        """
        Generates dynamic instructions based on contextual sentiment and difficulty.
        """
        sentiment = sentiment.lower()
        difficulty = difficulty.lower()
        is_negative = sentiment in ["negative", "stress", "fear", "anger"]

        if sentiment in ["joy", "positive"]:
            return (
                "\n[DYNAMIC INSTRUCTION: User is happy/positive.]\n"
                "ACTION: Match their energy, be encouraging and positive."
            )
        if sentiment in ["sadness"]:
            return (
                "\n[DYNAMIC INSTRUCTION: User is sad/distressed.]\n"
                "ACTION: Be empathetic, use a softer tone, and validate their feelings before solving the problem."
            )
        if is_negative:
            if difficulty == "hard":
                return (
                    "\n[DYNAMIC INSTRUCTION: User is angry/negative.]\n"
                    "ACTION: De-escalate. Be professional, calm, and concise. Do not argue."
                )
            return (
                "\n[DYNAMIC INSTRUCTION: User is angry/negative.]\n"
                "ACTION: De-escalate. Be professional, calm, and concise. Do not argue."
            )
        if sentiment in ["neutral"]:
            return (
                "\n[DYNAMIC INSTRUCTION: User is neutral.]\n"
                "ACTION: Be clear, direct, and helpful."
            )

        return (
            "\n[DYNAMIC INSTRUCTION: User sentiment unclear.]\n"
            "ACTION: Be professional, calm, and supportive. Prioritize clarity and safety."
        )

    def _get_sentiment_instruction(self, sentiment: str, difficulty: str) -> str:
        """
        Backward-compatible alias for contextual instruction.
        """
        return self._get_contextual_instruction(sentiment, difficulty)

    def _construct_messages(
        self,
        base_system_prompt: str,
        user_text: str,
        history: List[Dict[str, str]],
        analysis: AyaAnalysis,
        difficulty: str,
        scenario_goal: str,
    ) -> List[Dict[str, str]]:
        """
        Constructs the list of messages using the 'Sandwich Strategy'.
        1. Immutable System Header (Hidden Rules)
        2. User's Persona (base_system_prompt)
        3. Dynamic Instructions (Contextual Analysis + Guardrails)
        """
        
        # 1. Global Functional Rules (Hidden from user, enforced by system)
        system_header = (
            "SYSTEM INSTRUCTIONS:\n"
            "1. Output Language: Hebrew.\n"
            "2. Response Length: Short, concise sentences.\n"
            "3. Roleplay Adherence: Stay in character.\n"
        )

        # 2. Dynamic Contextual Adjustment (Aya Analysis)
        sentiment_instruction = self._get_contextual_instruction(analysis.sentiment, difficulty)
        analysis_block = (
            "\nCONTEXTUAL ANALYSIS:\n"
            f"Sentiment: {analysis.sentiment}\n"
            f"Confidence: {analysis.confidence:.2f}\n"
            f"Intent: {analysis.detected_intent}\n"
            f"Social Impact: {analysis.social_impact}\n"
            f"Reasoning: {analysis.reasoning}\n"
            f"Scenario Goal: {scenario_goal}\n"
        )

        # 3. Safety Guardrails (Unicorns/Magic)
        safety_footer = (
            "\nSAFETY PROTOCOL:\n"
            "If user mentions impossible things (unicorns, infinite money, magic), "
            "STOP the role-play immediately.\n"
            "Respond in Hebrew: 'אני חושב שאנחנו גולשים לדמיון. בוא נתמקד במצב האמיתי כאן.'\n"
            "Then restate the current problem clearly."
        )

        # 4. COMBINATION (The Sandwich)
        # We put the User's Persona (persona_prompt) in the middle/most important spot.
        full_system_prompt = f"""{system_header}

--- CHARACTER PERSONA (SERVER-RESOLVED) ---
{base_system_prompt}
-----------------------------------------
{sentiment_instruction}
{analysis_block}
{safety_footer}"""

        messages = [{"role": "system", "content": full_system_prompt}]
        
        # Append history
        for msg in history:
            role = "assistant" if msg.get("role") in ["ai", "assistant"] else "user"
            content = msg.get("content", "")
            if content:
                messages.append({"role": role, "content": content})
        
        # Append current user message
        messages.append({"role": "user", "content": user_text})
        
        return messages

    async def process_user_message_stream(
        self, 
        text: str, 
        base_system_prompt: str, 
        difficulty_level: str = "normal",
        scenario_goal: str = "Infer from persona and conversation flow.",
        history: List[Dict[str, str]] = []
    ) -> AsyncGenerator[Any, None]:
        """
        Streaming version of the pipeline with History.
        Yields tokens from Aya as they are generated.
        IMPORTANT: This is an AsyncGenerator that yields tokens, 
        but we need to expose the sentiment too. 
        Convention: First yield is metadata object, rest are tokens.
        """
        # --- Step A: Normalization ---
        clean_text = self._normalize_text(text)
        if not clean_text:
            yield "Error: Empty input."
            return

        # --- Step B: Contextual Analysis (Aya) ---
        analysis = await self._analyze_with_aya(history, clean_text, base_system_prompt, scenario_goal)
        logger.debug(
            f"🧠 Aya Analysis: {analysis.sentiment} ({analysis.confidence:.2f}) intent={analysis.detected_intent}"
        )

        # Yield Metadata first (Custom Protocol)
        yield {"type": "analysis", **analysis.dict()}

        # --- Step C: Prompt Engineering (The Sandwich) ---
        messages = self._construct_messages(
            base_system_prompt, clean_text, history, analysis, difficulty_level, scenario_goal
        )

        # --- Step D: Generation (Aya - Streaming) ---
        try:
            stream = await self.llm_client.chat.completions.create(
                model=self.llm_model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=150,
                stream=True
            )
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            logger.error(f"❌ Aya Generation Failed: {e}")
            yield "סליחה, נתקלתי בבעיה בעיבוד התשובה."

    async def process_user_message(
        self, 
        text: str, 
        base_system_prompt: str, 
        difficulty_level: str = "normal",
        scenario_goal: str = "Infer from persona and conversation flow.",
        history: List[Dict[str, str]] = []
    ) -> Tuple[str, str]:
        """
        Non-streaming version with History (for testing/legacy).
        Returns: (response_text, sentiment_label)
        """
        # --- Step A: Normalization ---
        clean_text = self._normalize_text(text)
        if not clean_text:
            return "Error: Empty input.", "neutral"

        # --- Step B: Contextual Analysis (Aya) ---
        analysis = await self._analyze_with_aya(history, clean_text, base_system_prompt, scenario_goal)
        logger.debug(
            f"🧠 Aya Analysis: {analysis.sentiment} ({analysis.confidence:.2f}) intent={analysis.detected_intent}"
        )

        # --- Step C: Prompt Engineering (The Sandwich) ---
        messages = self._construct_messages(
            base_system_prompt, clean_text, history, analysis, difficulty_level, scenario_goal
        )

        # --- Step D: Generation (Aya) ---
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            generated_text = response.choices[0].message.content
            return generated_text, analysis.sentiment

        except Exception as e:
            logger.error(f"❌ Aya Generation Failed: {e}")
            return "סליחה, נתקלתי בבעיה בעיבוד התשובה.", "unknown"
