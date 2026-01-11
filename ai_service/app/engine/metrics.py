import re
import logging
from typing import Dict, Any, List
from pydantic import BaseModel
from app.services.nlp import nlp_service
from app.services.preprocessor import Preprocessor

logger = logging.getLogger(__name__)

class TurnMetrics(BaseModel):
    # From raw_text
    greeting_present: bool = False
    mitigation_present: bool = False
    
    # Imperative Metrics (Layered)
    imperative_raw: bool = False    # Pure linguistic detection
    imperative_social: bool = False # Contextualized (Raw + No Mitigation)
    
    # NLU / Slots
    extracted_slots: Dict[str, Any] = {}

    # From STT
    wpm: float = 0.0
    pause_count: int = 0
    total_pause_time: float = 0.0
    
    # From Stanza
    lemma_repetition_ratio: float = 0.0
    has_main_verb: bool = False
    starts_with_verb: bool = False
    sentence_fragmentation: bool = False
    avg_dependency_depth: float = 0.0
    
    # Deprecated / Legacy mappings (for backward compatibility if needed)
    @property
    def imperative_form(self) -> bool:
        return self.imperative_raw

class MetricsEngine:
    
    # Heuristics (Hebrew)
    GREETINGS = r"(שלום|היי|בוקר טוב|ערב טוב|אהלן|מה נשמע|ברכות)"
    # Imperatives or Future-as-Imperative (Partial List)
    IMPERATIVES = r"\b(תביא|תן|לך|בוא|תעשה|תגיד|תבדוק|שלח|תשלח|תכין)\b"
    MITIGATIONS = r"(בבקשה|אפשר|תוכל|אולי|סליחה|תודה|נא)"
    
    # Slot Regexes
    REGEX_AMOUNT = r"(\d+(?:,\d{3})*(?: אלף| מיליון)?)"

    @staticmethod
    def compute_metrics(raw_text: str, stt_data: Dict[str, Any]) -> TurnMetrics:
        m = TurnMetrics()
        
        # 1. Raw Text Metrics (Regex)
        regex_imperative = False
        if raw_text:
            m.greeting_present = bool(re.search(MetricsEngine.GREETINGS, raw_text))
            regex_imperative = bool(re.search(MetricsEngine.IMPERATIVES, raw_text))
            m.mitigation_present = bool(re.search(MetricsEngine.MITIGATIONS, raw_text))
            
            # Simple Slot Extraction (Amount)
            amount_match = re.search(MetricsEngine.REGEX_AMOUNT, raw_text)
            if amount_match:
                # Try to parse or just store string
                m.extracted_slots["amount"] = amount_match.group(0) # Keep string with "alf" etc.

        # 2. STT Metrics
        m.wpm = stt_data.get("speech_rate_wpm", 0.0)
        m.pause_count = stt_data.get("pause_count", 0)
        m.total_pause_time = stt_data.get("pause_total_time_sec", 0.0)

        # 3. Determine Analysis Text (Normalized)
        if "clean_text" in stt_data:
            analysis_text = stt_data["clean_text"]
        else:
            _, analysis_text, _ = Preprocessor.process_text(raw_text)

        # 4. Stanza Metrics (on Analysis Text)
        doc = nlp_service.analyze(analysis_text)
        
        stanza_imperative = False
        
        if doc and doc.sentences:
            total_lemmas = 0
            unique_lemmas = set()
            verb_found = False
            total_depth = 0
            token_count = 0
            
            # Check first word POS for imperative heuristic
            first_sentence = doc.sentences[0]
            if first_sentence.words:
                m.starts_with_verb = (first_sentence.words[0].upos == 'VERB')

            for sentence in doc.sentences:
                for word in sentence.words:
                    if word.upos != 'PUNCT':
                        total_lemmas += 1
                        unique_lemmas.add(word.lemma)
                    if word.upos == 'VERB':
                        verb_found = True
                        
                        feats = word.feats if word.feats else ""
                        if "Mood=Imp" in feats:
                            stanza_imperative = True
                        if "Person=2" in feats:
                             stanza_imperative = True
                    
                    token_count += 1
            
            if total_lemmas > 0:
                m.lemma_repetition_ratio = round(1.0 - (len(unique_lemmas) / total_lemmas), 2)
            
            m.has_main_verb = verb_found
            
            if not verb_found and total_lemmas < 4:
                m.sentence_fragmentation = True
                
            depths = []
            for sentence in doc.sentences:
                heads = {w.id: w.head for w in sentence.words}
                for w in sentence.words:
                    d = 0
                    curr = w.id
                    while curr != 0 and d < 20: 
                        curr = heads.get(curr, 0)
                        d += 1
                    depths.append(d)
            
            if depths:
                m.avg_dependency_depth = round(sum(depths) / len(depths), 2)

        # --- Layered Imperative Logic ---
        m.imperative_raw = regex_imperative or stanza_imperative
        m.imperative_social = m.imperative_raw and not m.mitigation_present
        
        logger.info(f"[METRICS] greeting={m.greeting_present} imperative_raw={m.imperative_raw} imperative_social={m.imperative_social} mitigation={m.mitigation_present}")
        logger.info(f"[METRICS] slots={m.extracted_slots}")

        return m

