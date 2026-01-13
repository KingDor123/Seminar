import logging
import time
import os
from typing import Dict, Any, List
from app.engine.schema import InteractionFeatures

logger = logging.getLogger("FeatureExtractor")

# 3. Add a single DEBUG_MODE flag (environment variable or constant)
# Default: true
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

try:
    import stanza
    _STANZA_AVAILABLE = True
except ImportError:
    _STANZA_AVAILABLE = False
    # Log Stanza unavailable warning (Phase 1)
    if DEBUG_MODE:
        logger.warning("[FEATURES] Stanza not installed. Feature extraction will be limited.")

class FeatureExtractor:
    _pipeline = None

    @classmethod
    def _get_pipeline(cls):
        if not _STANZA_AVAILABLE:
            return None
        
        if cls._pipeline is None:
            try:
                # Initialize Hebrew pipeline. 
                # Note: In a real deployment, ensure models are downloaded during build/startup.
                # stanza.download('he') 
                cls._pipeline = stanza.Pipeline(lang='he', processors='tokenize,pos,lemma,depparse,ner,sentiment', logging_level='WARN')
                if DEBUG_MODE:
                    logger.info("[FEATURES] Stanza Hebrew pipeline initialized.")
            except Exception as e:
                logger.error(f"[FEATURES] Failed to initialize Stanza pipeline: {e}")
                cls._pipeline = None
        return cls._pipeline

    @classmethod
    def extract(cls, text: str, audio_meta: Dict[str, Any] = {}) -> InteractionFeatures:
        """
        Deterministic extraction of features from text and audio metadata.
        NO LLM calls here.
        """
        start_time = time.time()
        
        # Log raw user text (Phase 1)
        if DEBUG_MODE:
            logger.info(f"[FEATURES] Raw User Text: '{text}'")

        features = InteractionFeatures(
            text=text,
            wpm=audio_meta.get("wpm", 0.0),
            silence_duration=audio_meta.get("silence_duration", 0.0),
            filler_word_count=audio_meta.get("filler_count", 0)
        )

        pipeline = cls._get_pipeline()
        
        if pipeline and text.strip():
            try:
                doc = pipeline(text)
                
                # 1. Sentiment (Stanza provides 0, 1, 2. We map to -1, 0, 1 approx)
                # Note: Stanza sentiment is often sentence-level. We'll average.
                total_sentiment = 0
                count = 0
                for sent in doc.sentences:
                    # sentiment: 0 = negative, 1 = neutral, 2 = positive
                    val = sent.sentiment - 1 
                    total_sentiment += val
                    count += 1
                
                if count > 0:
                    features.sentiment_score = total_sentiment / count
                    if features.sentiment_score > 0.3:
                        features.sentiment_label = "positive"
                    elif features.sentiment_score < -0.3:
                        features.sentiment_label = "negative"
                    else:
                        features.sentiment_label = "neutral"

                # 2. POS Tags & Dependency Root
                # We'll just grab the root verb of the first sentence for "action"
                all_pos = []
                for sent in doc.sentences:
                    for word in sent.words:
                        if word.upos in ["VERB", "NOUN", "ADJ"]:
                            all_pos.append(word.upos)
                        if word.deprel == "root":
                            features.dependency_root = word.lemma
                
                features.pos_tags = list(set(all_pos)) # Unique tags present

                # 3. Named Entities
                ents = []
                for sent in doc.sentences:
                    for ent in sent.ents:
                        ents.append(f"{ent.text} ({ent.type})")
                features.named_entities = ents

            except Exception as e:
                logger.error(f"[FEATURES] Error during Stanza processing: {e}")
        
        # Fallback/heuristic for sentiment if Stanza failed or missing
        if not _STANZA_AVAILABLE or pipeline is None:
            # Very dumb heuristic just to have *something*
            negatives = ["לא", "רע", "עצוב", "כועס", "די"]
            positives = ["כן", "טוב", "שמח", "תודה", "נהדר"]
            score = 0
            for w in text.split():
                if w in negatives: score -= 1
                if w in positives: score += 1
            
            features.sentiment_score = float(score)
            if score > 0: features.sentiment_label = "positive"
            elif score < 0: features.sentiment_label = "negative"

        features.processing_latency_ms = (time.time() - start_time) * 1000
        
        # Log extracted features (Phase 1)
        if DEBUG_MODE:
            logger.info(
                f"[FEATURES] Extracted: WPM={features.wpm}, Pauses={features.silence_duration}s, "
                f"Fillers={features.filler_word_count}, Sentiment={features.sentiment_label} ({features.sentiment_score:.2f}), "
                f"Entities={features.named_entities}, Root={features.dependency_root}"
            )
            
        return features