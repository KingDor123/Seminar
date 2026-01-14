# GEMINI.md - Project Overview & Quick Start

## Project Overview
**SoftSkill v2** (Seminar / AI Coaching) is a full-stack platform designed for social skills training. It allows users to engage in role-play scenarios with AI personas to improve their communication skills. The system features real-time chat, voice interaction (TTS/STT), 3D avatars, and post-session analytics.

## Tech Stack Summary
- **Frontend:** Next.js 16, React 19, Tailwind CSS, Three.js (3D Avatars).
- **Backend:** Node.js (Express), TypeScript, PostgreSQL.
- **AI Engine:** Ollama (running locally via Docker) serving the `aya:8b` model.
- **Infrastructure:** Docker & Docker Compose.

## Quick Start

### Prerequisites
- Docker & Docker Compose
- `npm` (optional, for local development outside Docker)

### Running the Full Stack
The project is orchestrated via Docker Compose.

1.  **Environment Setup:**
    Ensure a `.env` file exists in the root (or is sourced by the containers). Key variables include `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `LLM_MODEL` (default: `aya:8b`).

2.  **Start the Application:**
    Run the provided helper script:
    ```bash
    ./start.sh
    ```
    This script builds the images and starts all services (`frontend`, `backend`, `db`, `ollama`).

    *Alternatively, run manually:*
    ```bash
    docker-compose up --build
    ```

3.  **Access the App:**
    - **Frontend:** [http://localhost:3000](http://localhost:3000)
    - **Backend API:** [http://localhost:5001](http://localhost:5001)
    - **Ollama:** [http://localhost:11434](http://localhost:11434)

## System Architecture

The system consists of four main containers:

| Service | Internal Port | External Port | Description |
| :--- | :--- | :--- | :--- |
| **frontend** | 3000 | 3000 | Next.js App Router application (Hebrew UI). |
| **backend** | 5001 | 5001 | Express.js API, handles business logic & DB. |
| **db** | 5432 | 5432 | PostgreSQL 16 database. |
| **ollama** | 11434 | 11434 | Local LLM inference server (default: `aya:8b`). |

## Directory Structure

- **`backend/`**: Node.js/Express API server.
    - See [`backend/GEMINI.md`](backend/GEMINI.md) for detailed backend architecture, commands, and conventions.
- **`frontend/`**: Next.js React application.
    - See [`frontend/GEMINI.md`](frontend/GEMINI.md) for frontend component structure, hooks, and UI details.
- **`docs/`**: Project documentation (UI blueprints, migration checklists).
- **`UML/`**: Architecture and sequence diagrams (`.puml`).
- **`db/`**: Database initialization scripts (mounted to `db` container).

## Development Notes

- **Ollama Model:** The `ollama` container is configured to pull the model specified in `LLM_MODEL` (default `aya:8b`) on startup.
- **Database Persistence:** Data is persisted in the `db_data` Docker volume.
- **Shared Configuration:** Review `.env` usage across `docker-compose.yml` to ensure consistency between services.
