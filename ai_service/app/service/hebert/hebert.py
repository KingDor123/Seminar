import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class HeBERTService:
    def __init__(self, model_name: str):
        """
        Initializes the HeBERT sentiment analysis service.
        """
        self.model_name = model_name
        try:
            logger.info(f"Loading HeBERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer
            )
            logger.info("HeBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load HeBERT model: {e}")
            raise

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyzes the sentiment of the given Hebrew text.
        Returns a dictionary with 'label' and 'score'.
        """
        if not text.strip():
            return {"label": "neutral", "score": 1.0}

        try:
            results = self.sentiment_pipeline(text)
            # HeBERT usually returns labels like 'neutral', 'positive', 'negative'
            # or 'LABEL_0', 'LABEL_1', 'LABEL_2' depending on how it was loaded.
            # We might need to map them if they are indexed.
            result = results[0]

            # Map labels to human-readable format if necessary
            # For avichayel/hebert, it usually has 'natural', 'positive', 'negative'
            label = result['label'].lower()
            if 'natural' in label:
                label = 'neutral'
            elif 'positive' in label:
                label = 'positive'
            else:
                label = 'negative'
            return {
                "label": label,
                "score": result['score']
            }
        except Exception as e:
            logger.error(f"Error during sentiment analysis: {e}")
            return {"label": "neutral", "score": 0.0, "error": str(e)}
