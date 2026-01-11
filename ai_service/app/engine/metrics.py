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
    imperative_form: bool = False
    mitigation_present: bool = False
    
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

class MetricsEngine:
    
    # Heuristics (Hebrew)
    GREETINGS = r"(שלום|היי|בוקר טוב|ערב טוב|אהלן|מה נשמע|ברכות)"
    # Imperatives or Future-as-Imperative (Partial List)
    IMPERATIVES = r"\b(תביא|תן|לך|בוא|תעשה|תגיד|תבדוק|שלח|תשלח|תכין)\b"
    MITIGATIONS = r"(בבקשה|אפשר|תוכל|אולי|סליחה|תודה|נא)"

    @staticmethod
    def compute_metrics(raw_text: str, stt_data: Dict[str, Any]) -> TurnMetrics:
        m = TurnMetrics()
        
        # 1. Raw Text Metrics (Regex)
        regex_imperative = False
        if raw_text:
            m.greeting_present = bool(re.search(MetricsEngine.GREETINGS, raw_text))
            regex_imperative = bool(re.search(MetricsEngine.IMPERATIVES, raw_text))
            m.mitigation_present = bool(re.search(MetricsEngine.MITIGATIONS, raw_text))

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
                has_subject = False
                for word in sentence.words:
                    if word.upos != 'PUNCT':
                        total_lemmas += 1
                        unique_lemmas.add(word.lemma)
                    if word.upos == 'VERB':
                        verb_found = True
                        
                        # Hebrew Imperative Detection Logic
                        feats = word.feats if word.feats else ""
                        
                        # Case A: Explicit Morphological Imperative (Mood=Imp)
                        if "Mood=Imp" in feats:
                            stanza_imperative = True
                        
                        # Case B: Future/Present tense used as command (Person=2)
                        # e.g., "תביא" (Tavi) often parsed as Future, 2nd Person, Masc, Sing
                        # We trigger this if it's 2nd person verb.
                        # Refinement: Only if NO subject is present in the sentence?
                        # "אתה תביא" (You will bring) is less imperative than "תביא" (Bring).
                        if "Person=2" in feats:
                             # This is a strong signal in this context (short commands)
                             # We check if there's an explicit PRON subject linked? 
                             # For simplicity/robustness in this "soft skills" context:
                             # 2nd person verb is usually a directive.
                             stanza_imperative = True
                    
                    if word.upos in ('PRON', 'PROPN', 'NOUN') and 'nsubj' in (word.deprel or ""):
                        has_subject = True
                        
                    token_count += 1
                
                # Refinement: If it was Person=2 but had a subject "אתה", maybe it's less command-y?
                # But "אתה תביא לי" is still directive.
                # We stick to the simpler signal for now.

            # Repetition (Higher = more repetition)
            if total_lemmas > 0:
                m.lemma_repetition_ratio = round(1.0 - (len(unique_lemmas) / total_lemmas), 2)
            
            m.has_main_verb = verb_found
            
            # Fragmentation: No verb and short (heuristic)
            if not verb_found and total_lemmas < 4:
                m.sentence_fragmentation = True
                
            # Quick Avg Dependency Depth
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

        # Combined Imperative Logic
        m.imperative_form = regex_imperative or stanza_imperative

        logger.info(f"[METRICS] greeting={m.greeting_present} imperative={m.imperative_form} (regex={regex_imperative}, stanza={stanza_imperative}) mitigation={m.mitigation_present}")
        logger.info(f"[METRICS] starts_with_verb={m.starts_with_verb} repetition={m.lemma_repetition_ratio} fragmentation={m.sentence_fragmentation}")

        return m

