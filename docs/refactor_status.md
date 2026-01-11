# AI Pipeline Refactor Status

## Implemented Components
1. **Input Handling**: 
   - Updated `POST /interact` in `ai_service/app/routers/conversation.py` to accept `audio` (UploadFile) and `text`.
   - Integrated `STTService` global initialization.

2. **STT & Preprocessing**:
   - Restored `ai_service/app/services/preprocessor.py` for text normalization and filler counting.
   - `STTService` preserves `raw_text` and provides `clean_text` (analysis_text) + timestamps.

3. **NLP Service**:
   - Created `ai_service/app/services/nlp.py` implementing `StanzaNLP` singleton with Hebrew support.
   - Extracts: tokens, lemmas, POS, dependency tree.

4. **Metrics Engine**:
   - Created `ai_service/app/engine/metrics.py`.
   - Computes:
     - **Raw Text**: Greeting, Imperative, Mitigation (Regex).
     - **STT**: WPM, Pauses.
     - **Stanza**: Lemma Repetition, Main Verb, Fragmentation, Dependency Depth.

5. **Decision Engine**:
   - Created `ai_service/app/engine/decision.py`.
   - Implements strict rule-based gating:
     - `UNCLEAR`: If sentence fragmentation detected.
     - `INAPPROPRIATE_FOR_CONTEXT`: If imperative used without mitigation.
     - `GATE_PASSED`: Otherwise.

6. **Orchestrator**:
   - Modified `ai_service/app/engine/orchestrator.py` to remove `EvaluatorAgent` (LLM).
   - Now uses `MetricsEngine` -> `DecisionEngine`.
   - Passes decision results (gate passed, reasons) to `RolePlayAgent` for response generation.
   - Yields structured `analysis` event containing raw metrics and decision label.

## Verification
- **Target Architecture**: Matches the diagram [User -> STT -> Preprocess -> Stanza -> Metrics -> Rules -> Orchestrator -> LLM -> SSE].
- **Constraints**:
  - `raw_text` preserved.
  - No new LLM calls for decision.
  - No embeddings/HeBERT.
  - Minimal schema changes.
