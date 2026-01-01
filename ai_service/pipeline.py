import logging
import re
import torch
from typing import Dict, Any, Optional, List, Tuple, AsyncGenerator
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from openai import AsyncOpenAI
import torch.nn.functional as F
from app.core.config import settings

# Configure logger
logger = logging.getLogger("HybridPipeline")

class HybridPipeline:
    """
    A serial processing pipeline designed for High-Performance Computing (HPC) environments.
    
    Architecture:
    1. Text Normalization (Unicode/Whitespace only, preserving Hebraic morphology).
    2. Sentiment Analysis (HeBERT - Finetuned Transformer).
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

        # --- Load HeBERT (Sentiment Analysis) ---
        self.hebert_model_name = "avichr/heBERT_sentiment_analysis"
        try:
            logger.info(f"Loading HeBERT model: {self.hebert_model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.hebert_model_name)
            self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(self.hebert_model_name)
            self.sentiment_model.to(self.device)
            self.sentiment_model.eval() # Set to evaluation mode
            logger.info("✅ HeBERT loaded successfully.")
        except Exception as e:
            logger.critical(f"❌ Failed to load HeBERT: {e}")
            raise e

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

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Step B: HeBERT Inference
        Runs the text through the fine-tuned Hebrew BERT model.
        """
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
            
            # Get probabilities
            probs = F.softmax(outputs.logits, dim=-1)
            confidence, predicted_class_idx = torch.max(probs, dim=-1)
            
            # Map label ID to string (assuming standard HeBERT config)
            # Check model config id2label if available, otherwise default standard sentiment mapping
            labels = self.sentiment_model.config.id2label
            if not labels:
                 # Fallback for standard 3-class sentiment models (neutral, pos, neg)
                 # Note: avichr/heBERT_sentiment_analysis specific mapping might vary.
                 # Usually: 0: neutral, 1: positive, 2: negative or similar.
                 # For robust code, we rely on the config.
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

    def _get_sentiment_instruction(self, sentiment: str, difficulty: str) -> str:
        """
        Generates dynamic instructions based on HeBERT sentiment and difficulty.
        """
        sentiment = sentiment.lower()
        difficulty = difficulty.lower()
        is_negative = sentiment in ["negative", "stress", "fear", "anger"]

        if is_negative:
            if difficulty == "easy":
                return (
                    "\n[DYNAMIC INSTRUCTION: User detected as stressed/negative.]\n"
                    "ACTION: While staying in character, soften your tone significantly.\n"
                    "ACTION: Acknowledge the difficulty indirectly and offer a helping cue."
                )
            elif difficulty == "hard":
                return (
                    "\n[DYNAMIC INSTRUCTION: User detected as stressed/negative.]\n"
                    "ACTION: Maintain a strict and professional persona.\n"
                    "ACTION: Do not soften your tone. Simulate real-world pressure."
                )
            else: # Normal
                return (
                    "\n[DYNAMIC INSTRUCTION: User detected as stressed/negative.]\n"
                    "ACTION: Remain professional but clear. Ensure your response is unambiguous."
                )
        return ""

    def _construct_messages(self, base_system_prompt: str, user_text: str, history: List[Dict[str, str]], sentiment: str, difficulty: str) -> List[Dict[str, str]]:
        """
        Constructs the list of messages using the 'Sandwich Strategy'.
        1. Immutable System Header (Hidden Rules)
        2. User's Persona (base_system_prompt)
        3. Dynamic Instructions (Sentiment + Guardrails)
        """
        
        # 1. Global Functional Rules (Hidden from user, enforced by system)
        system_header = (
            "SYSTEM INSTRUCTIONS:\n"
            "1. Output Language: Hebrew.\n"
            "2. Response Length: Short, concise sentences.\n"
            "3. Roleplay Adherence: Stay in character.\n"
        )

        # 2. Dynamic Sentiment Adjustment (HeBERT)
        sentiment_instruction = self._get_sentiment_instruction(sentiment, difficulty)

        # 3. Safety Guardrails (Unicorns/Magic)
        safety_footer = (
            "\nSAFETY PROTOCOL:\n"
            "If user mentions impossible things (unicorns, infinite money, magic), "
            "STOP the role-play immediately.\n"
            "Respond in Hebrew: 'אני חושב שאנחנו גולשים לדמיון. בוא נתמקד במצב האמיתי כאן.'\n"
            "Then restate the current problem clearly."
        )

        # 4. COMBINATION (The Sandwich)
        # We put the User's Persona (base_system_prompt) in the middle/most important spot.
        full_system_prompt = f"""{system_header}

--- CHARACTER PERSONA (FROM FRONTEND) ---
{base_system_prompt}
-----------------------------------------
{sentiment_instruction}
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

        # --- Step B: HeBERT Analysis ---
        sentiment_data = self._analyze_sentiment(clean_text)
        sentiment_label = sentiment_data["sentiment"]
        logger.debug(f"🧠 HeBERT Analysis: {sentiment_label} ({sentiment_data['confidence']:.2f})")

        # Yield Metadata first (Custom Protocol)
        yield {"type": "metadata", "sentiment": sentiment_label, "confidence": sentiment_data["confidence"]}

        # --- Step C: Prompt Engineering (The Sandwich) ---
        messages = self._construct_messages(base_system_prompt, clean_text, history, sentiment_label, difficulty_level)

        # --- DEBUG: INSPECT PROMPT STRUCTURE ---
        print("\n🔍 🔍 🔍 DEBUG: FULL PROMPT SENT TO LLM 🔍 🔍 🔍")
        print(f"📌 SYSTEM PROMPT (Full Sandwich):\n{messages[0]['content']}")
        print(f"📌 HISTORY LENGTH: {len(history) if history else 0}")
        print("📌 FULL MESSAGES PAYLOAD:")
        import json
        print(json.dumps(messages, indent=2, ensure_ascii=False))
        print("🔍 🔍 🔍 END DEBUG 🔍 🔍 🔍\n")
        # ---------------------------------------

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

        # --- Step B: HeBERT Analysis ---
        sentiment_data = self._analyze_sentiment(clean_text)
        sentiment_label = sentiment_data["sentiment"]
        logger.debug(f"🧠 HeBERT Analysis: {sentiment_label} ({sentiment_data['confidence']:.2f})")

        # --- Step C: Prompt Engineering (The Sandwich) ---
        messages = self._construct_messages(base_system_prompt, clean_text, history, sentiment_label, difficulty_level)

        # --- Step D: Generation (Aya) ---
        try:
            response = await self.llm_client.chat.completions.create(
                model=self.llm_model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            
            generated_text = response.choices[0].message.content
            return generated_text, sentiment_label

        except Exception as e:
            logger.error(f"❌ Aya Generation Failed: {e}")
            return "סליחה, נתקלתי בבעיה בעיבוד התשובה.", "unknown"
