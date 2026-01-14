# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` holds the Next.js 16 UI (App Router in `frontend/app`, tests in `frontend/__tests__`, hooks in `frontend/hooks`).
- `backend/` contains the Node/Express API (TypeScript in `backend/src`, with `routes/`, `controllers/`, `services/`, and tests under `backend/src/**/__tests__/`).
- `ai_service/` is the FastAPI AI service (Python in `ai_service/app` with `routers/`, `services/`, `engine/`; tests in `ai_service/tests`).
- `docs/`, `UML/`, `traefik/`, and `script_tests/` store documentation, diagrams, infra config, and helper scripts.
- Root `docker-compose.yml` orchestrates services; `start.sh` is a convenience runner.

## Build, Test, and Development Commands
- `docker compose up --build` or `./start.sh`: run the full stack (frontend, backend, ai_service, Postgres, Ollama).
- `cd frontend && npm run dev`: start the Next.js dev server on `localhost:3000`.
- `cd frontend && npm run build` / `npm run start`: build and run the production frontend.
- `cd frontend && npm run lint`: run ESLint with `eslint-config-next`.
- `cd backend && npm run dev`: run the Express API in TSX watch mode.
- `cd backend && npm run build` / `npm run start`: compile to `dist/` and run the server.
- `cd ai_service && uvicorn main:app --reload`: run the FastAPI service locally.
- `cd ai_service && pytest`: execute AI service tests.

## Coding Style & Naming Conventions
- Frontend TS/TSX uses 2-space indentation; backend TS uses 4-space indentation; Python uses 4 spaces.
- TypeScript uses ESM imports with `.js` suffixes in source (example: `../services/user.service.js`).
- Backend file naming follows `*.controller.ts`, `*.service.ts`, `*.route.ts`; tests use `*.test.ts`.
- Python modules use snake_case and docstrings; keep logging via `logging`.

## Testing Guidelines
- Frontend: Jest + Testing Library; tests live in `frontend/__tests__/` or `frontend/**/__tests__/`.
- Backend: Jest (ts-jest, ESM); tests are under `backend/src/**/__tests__/`.
- AI service: Pytest; tests are in `ai_service/tests` with `test_*.py`.
- No coverage thresholds are configured; add focused tests for new behavior.

## Commit & Pull Request Guidelines
- Commit history favors imperative, capitalized summaries (examples: "Fix Analyzer signal generation", "Implement Financial Ineligibility state").
- Keep commits scoped; avoid mixing unrelated changes.
- PRs should include a short summary, testing notes, and screenshots for UI changes; link relevant issues when available.

## Configuration Tips
- Environment values live in `.env` and `frontend/.env.local`.
- Service ports are documented in `README.md`.
