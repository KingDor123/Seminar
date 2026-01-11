import stanza
import logging
import os
from threading import Lock

logger = logging.getLogger(__name__)

class StanzaNLP:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StanzaNLP, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        logger.info("🧠 Initializing Stanza NLP pipeline (Hebrew)...")
        try:
            # Download only if strictly necessary or force via env? 
            # Stanza usually checks automatically.
            # We use a minimal list of processors.
            # 'ner' is explicitly excluded per instructions.
            processors = "tokenize,mwt,pos,lemma,depparse"
            
            # Check if model exists (heuristic) or just let stanza handle it
            self.pipeline = stanza.Pipeline(
                lang='he', 
                processors=processors,
                verbose=False,
                use_gpu=False # Set to True if GPU available/desired
            )
            logger.info("✅ Stanza NLP Ready.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Stanza: {e}")
            self.pipeline = None

    def analyze(self, text: str):
        """
        Runs the Stanza pipeline on the text.
        Returns the Doc object or None if failed.
        """
        if not self.pipeline or not text.strip():
            return None
        
        try:
            doc = self.pipeline(text)
            
            # Logging for observability
            if doc and doc.sentences:
                tokens_count = 0
                lemmas = []
                pos_tags = []
                for sentence in doc.sentences:
                    for word in sentence.words:
                        tokens_count += 1
                        lemmas.append(word.lemma)
                        pos_tags.append(word.upos)
                
                logger.info(f"[NLP] tokens={tokens_count}")
                logger.info(f"[NLP] lemmas={lemmas}")
                logger.info(f"[NLP] pos={pos_tags}")

            return doc
        except Exception as e:
            logger.error(f"❌ Stanza Analysis Failed: {e}")
            return None

# Global instance
nlp_service = StanzaNLP()
