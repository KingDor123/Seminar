import stanza
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class StanzaService:
    def __init__(self, lang: str = "he"):
        """
        Initializes the Stanza NLP service for Hebrew.
        """
        self.lang = lang
        try:
            logger.info(f"Initializing Stanza for language: {self.lang}")
            # Ensure the language pack is downloaded
            stanza.download(self.lang)
            self.nlp = stanza.Pipeline(lang=self.lang, processors='tokenize,pos,lemma,depparse,ner')
            logger.info("Stanza initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Stanza: {e}")
            raise

    def analyze_text(self, text: str) -> Dict[str, Any]:
        """
        Analyzes the given text and returns NLP metrics.
        """
        if not text.strip():
            return {}

        try:
            doc = self.nlp(text)
            
            analysis = {
                "sentences": [],
                "entities": [],
                "metrics": {
                    "word_count": doc.num_words,
                    "sentence_count": len(doc.sentences)
                }
            }

            for sentence in doc.sentences:
                sent_data = {
                    "text": sentence.text,
                    "words": []
                }
                for word in sentence.words:
                    sent_data["words"].append({
                        "text": word.text,
                        "lemma": word.lemma,
                        "pos": word.pos,
                        "deprel": word.deprel
                    })
                analysis["sentences"].append(sent_data)

            for ent in doc.entities:
                analysis["entities"].append({
                    "text": ent.text,
                    "type": ent.type
                })

            return analysis
        except Exception as e:
            logger.error(f"Error during Stanza analysis: {e}")
            return {"error": str(e)}
