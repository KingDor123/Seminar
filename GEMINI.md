# GEMINI Context: SoftSkill AI Trainer

## Purpose
This file is a high-signal context brief for future AI interactions in this repo. It reflects the current, production-style architecture and data flow.

## Architecture Diagram (Text)
Frontend (Next.js)
  -> FastAPI AI Service (/ai, /analytics)
     -> HybridPipeline (HeBERT sentiment + Aya LLM via Ollama)
        -> PostgreSQL (sessions, messages)

Note: A separate Node/Express backend handles core APIs and DB initialization. The analytics endpoints in `ai_service` query Postgres directly.

## Data Flow (Message Lifecycle)
1. A user sends a message from the React UI.
2. FastAPI receives the request and normalizes text.
3. HeBERT runs sentiment analysis and tags the user message.
4. The Sandwich prompt is assembled (system rules + persona + dynamic safety/sentiment).
5. Aya streams the assistant response token-by-token from Ollama.
6. User message, sentiment label, and assistant reply are persisted to Postgres.
7. Dashboard endpoints aggregate sessions and sentiment trends for the UI.

## The Sandwich Prompt Structure
1. System Rules: global constraints (output language, short replies, stay in character).
2. User Persona: scenario prompt provided by the frontend.
3. Dynamic Safety/Sentiment: HeBERT-based instruction plus guardrails for impossible content.

## Database Schema (High Level)
- sessions: id, scenario_id, start_time, user_id (optional), ...
- messages: id, session_id, role (user/ai), content, sentiment (text), ...
- Relationship: a session has many messages; sentiment is stored per user message and surfaced in analytics.

## Analytics & Dashboard
- `GET /analytics/dashboard` aggregates totals and sentiment distribution from the messages table.
- `GET /analytics/sessions_list` returns recent sessions with message counts and last-known sentiment.
- The sessions page renders overview metrics, sentiment bars, and per-message sentiment badges.

## Current Status
- Docker Compose orchestrates frontend, backend, ai_service, Postgres, and Ollama.
- HeBERT loads on AI service startup; aya:8b is pulled by Ollama.
- Real analytics are live and wired to the dashboard.
