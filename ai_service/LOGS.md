# AI Service Logs

## Viewing Logs
To view the decision tree and NLP logs in real-time:
```bash
docker compose logs -f ai_service
```

## Log Structure

### 1. NLP Analysis
Before the decision tree, you will see raw NLP extraction logs:
```
[NLP] tokens=4
[NLP] lemmas=['תביא', 'לי', '20', 'אלף']
[NLP] pos=['VERB', 'PRON', 'NUM', 'NOUN']
[NLP] feats_sample=['1:Gender=Masc|Mood=Imp|Number=Sing|Person=2', ...]
```

### 2. Decision Tree
For every user turn, a structured block explains the logic:
```
[DECISION_TREE] ──────────────────────────────────────────────
[DECISION_TREE] Session: 123
[DECISION_TREE] State: ask_amount
[DECISION_TREE] Input: "תביא לי כסף"
[DECISION_TREE] Metrics:
  - greeting: False
  - imperative: True (Stanza/Regex detected)
  - mitigation: False
  - starts_with_verb: True
  ...
[DECISION_TREE] Rules Evaluation:
[DECISION_TREE] Rule: State-Specific Behavioral Expectations (ask_amount)
  Conditions:
    state == ask_amount (forbidden: ['imperative']) -> CHECK
    is_imperative: True -> FAIL
  Result: FAIL
[DECISION_TREE] Final Decision:
  - label: INAPPROPRIATE_FOR_CONTEXT
  - reason: Imperative forbidden in ask_amount
[DECISION_TREE] ──────────────────────────────────────────────
```

## Hebrew Imperative Detection
The system now detects imperatives using a hybrid approach:
1.  **Regex**: Matches known command verbs (e.g., "תביא", "תן").
2.  **Stanza NLP**:
    *   **Mood=Imp**: Explicit morphological imperative.
    *   **Person=2 (VERB)**: Future/Present tense used as a command (e.g., "תביא" detected as 2nd person future).
