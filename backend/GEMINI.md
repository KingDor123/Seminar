# GEMINI.md - Project Context and Instructions

## Project Overview
This project is the **Backend** for a Social Skills Training application. It provides a chat interface where users interact with AI personas in specific role-play scenarios (e.g., Job Interview, Grocery Store, First Date). The system analyzes these interactions to provide feedback, sentiment analysis, and social skills scoring.

## Technology Stack
- **Runtime:** Node.js (v20+)
- **Language:** TypeScript (ES2022, NodeNext)
- **Framework:** Express.js
- **Database:** PostgreSQL (using `pg` driver)
- **AI/LLM:** Ollama (default model: `aya:8b`)
- **Media:** `fluent-ffmpeg` (audio processing), `google-tts-api` (Text-to-Speech)
- **Authentication:** JWT & Cookie-based auth
- **Testing:** Jest, Supertest
- **Containerization:** Docker

## Architecture
The application follows a layered architecture:
1.  **Routes:** Define API endpoints (`src/routes/`).
2.  **Controllers:** Handle HTTP requests/responses (`src/controllers/`).
3.  **Services:** Implement business logic (`src/services/`).
    *   `LlmService`: Handles communication with the local Ollama instance.
    *   `ScenarioService`: Manages role-play scenarios.
4.  **Data/Repositories:** Direct database access (`src/repositories/`, `src/config/databaseConfig.ts`).
5.  **Data Models:** Defined in PostgreSQL schema (`db/init.sql`) and TypeScript interfaces.

## Key Features
- **Scenario-Based Chat:** Users select a scenario (defined in `src/data/scenarios.ts`) and chat with a specific persona.
- **Real-time AI Response:** Supports both streaming and synchronous text generation via Ollama.
- **Voice Interaction:** Supports audio uploads (`/interact`) and Text-to-Speech (`/tts`).
- **Analytics:** Tracks sentiment, turn-by-turn analysis, and generates post-session reports (`src/services/analytics.service.ts`).

## Development & Usage

### Prerequisites
- Node.js & npm
- PostgreSQL
- Ollama (running locally or accessible via network)
- ffmpeg (installed on the system for audio processing)

### Environment Variables (.env)
Create a `.env` file with the following keys (inferred):
- `PORT` (default: 5000)
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DB_PORT`
- `JWT_SECRET`
- `OLLAMA_BASE_URL` (default: `http://ollama:11434`)
- `LLM_MODEL` (default: `aya:8b`)
- `LOG_LEVEL` (default: `info`)
- `NODE_ENV` (`development`, `production`, `test`)

### Commands
- **Development:** `npm run dev` (uses `tsx` for watch mode)
- **Start:** `npm start` (runs built JS from `dist/`)
- **Build:** `npm run build` (runs `tsc`)
- **Test:** `npm test` (runs Jest)
- **Test Watch:** `npm run test:watch`

### Docker
The project includes a `Dockerfile` for production-ready images.
- **Build:** `docker build -t backend .`
- **Run:** `docker run -p 5000:5000 --env-file .env backend`

## Project Structure
- `src/config/`: Configuration (DB connection).
- `src/controllers/`: Request handlers.
- `src/data/`: Static data (e.g., `scenarios.ts`).
- `src/middleware/`: Express middleware (Auth, Error handling).
- `src/routes/`: API route definitions.
- `src/services/`: Business logic (AI, Chat, User, Analytics).
- `src/utils/`: Utilities (Logger, Custom Errors, Validation).
- `db/`: Database initialization scripts (`init.sql`).
- `test/`: Integration tests.

## Development Conventions
- **Logging:** Use the `logger` from `src/utils/logger.js` (Winston). Do not use `console.log` in production code.
- **Error Handling:** Use `AppError` for operational errors. Pass errors to `next(err)` to be caught by the global error handler (`src/middleware/error.middleware.ts`).
- **Async/Await:** Use `async/await` for all asynchronous operations.
- **Strict Typing:** TypeScript `strict` mode is enabled. Ensure all types are defined.
- **Scenarios:** New scenarios should be added to `src/data/scenarios.ts` following the `Scenario` interface.
