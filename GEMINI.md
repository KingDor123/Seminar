# SoftSkill v2 Project Context

## Project Overview
**SoftSkill v2** is a microservices-based application designed for soft skills training or assessment. It utilizes a modern full-stack architecture with a clear separation of concerns between the frontend, backend, AI services, and database.

## Architecture

### 1. Frontend (`frontend/`)
*   **Framework:** [Next.js](https://nextjs.org/) (React) with TypeScript.
*   **Styling:** Tailwind CSS (inferred).
*   **Port:** `3000`
*   **Key Components:**
    *   `app/page.tsx`: Main entry point.
    *   `components/User.tsx`: Fetches and displays user data.

### 2. Backend (`backend/`)
*   **Framework:** Node.js with [Express](https://expressjs.com/).
*   **Language:** JavaScript (ES Modules).
*   **Database:** PostgreSQL (`pg` driver).
*   **Architecture:** Layered (Controller -> Service -> Repository).
*   **Port:** `5001` (mapped to container port `5000`).
*   **API Prefix:** `/api`

### 3. AI Service (`ai_service/`)
*   **Framework:** Python [FastAPI](https://fastapi.tiangolo.com/).
*   **Port:** `8000`
*   **Purpose:** Dedicated service for AI/ML operations (currently basic ping endpoint).

### 4. Database (`db`)
*   **Engine:** PostgreSQL 16.
*   **Initialization:** `backend/db/init.sql` handles schema creation (users table, roles enum) and seeding initial dummy data.
*   **Persistence:** Docker volume `db_data`.

### 5. Infrastructure
*   **Orchestration:** Docker Compose.
*   **Proxy:** Traefik configuration exists in `traefik/`, possibly for production or advanced routing (currently not in the main `docker-compose.yml`).

## Getting Started

### Prerequisites
*   [Docker](https://www.docker.com/) and Docker Compose.
*   Node.js and npm (for local development without Docker).

### Installation & Running

1.  **Environment Setup:**
    Ensure you have a `.env` file in the root (or respective service directories if configured differently, `docker-compose.yml` references a root `.env`).
    *   *Note: Check `docker-compose.yml` for required variables like `DB_USER`, `DB_PASSWORD`, `DB_NAME`.*

2.  **Build and Run:**
    ```bash
    docker-compose up --build
    ```

3.  **Accessing Services:**
    *   **Frontend:** [http://localhost:3000](http://localhost:3000)
    *   **Backend API:** [http://localhost:5001/api/health](http://localhost:5001/api/health)
    *   **AI Service:** [http://localhost:8000/ai/ping](http://localhost:8000/ai/ping)

## Development Conventions

*   **Backend:**
    *   Follow the **Controller-Service-Repository** pattern.
    *   Use **ES Modules** (`import`/`export`).
    *   Database logic resides strictly in repositories.
*   **Frontend:**
    *   Use **Next.js App Router** structure (`app/`).
    *   Components reside in `components/`.
    *   API calls are currently made via `axios`.
*   **Database:**
    *   Schema changes should be reflected in `backend/db/init.sql` for initialization consistency.

## Current Status
*   The application is in a functional prototype state.
*   The backend serves user data from a seeded Postgres database.
*   The frontend fetches and displays a specific user's data (hardcoded ID `2`).
*   The AI service is initialized but minimal.

## Domain Requirements (Derived from Project Book)

### Target Audience
*   **High-Functioning Autism Spectrum Disorder (HFASD)**
*   **Age:** 15+ (Teens and Adults)
*   **Core Needs:** Improving social skills, emotional regulation, and cognitive flexibility.

### Core Features
1.  **AI-Based Social Simulations:**
    *   Interactive scenarios (e.g., "Job Interview," "Grocery Store," "Date").
    *   **Real-time Interaction:** Users converse with an AI avatar.
    *   **Unpredictability:** Simulations must include surprise elements (e.g., sudden topic change) to train cognitive flexibility.

2.  **Real-Time Feedback System:**
    *   Analysis of user's tone, speech content, and potentially non-verbal cues.
    *   Immediate positive reinforcement and constructive suggestions.
    *   Based on "Video Modeling + Feedback" principles.

3.  **Adaptive Learning:**
    *   The system learns from user performance.
    *   Difficulty adjusts dynamically (scaffolding).
    *   Focus on **Transferability** (FIELD model): ensuring skills learned in the sim apply to real life.

### Scientific Basis
*   **DSM-5:** Used for defining ASD characteristics.
*   **Theory of Mind & Central Coherence:** The AI should challenge users to understand others' perspectives and see the "big picture."
*   **SEL (Social-Emotional Learning):** Integrating emotional awareness into the training.