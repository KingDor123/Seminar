# SoftSkill v2: AI-Driven Social Skills Training Platform

**SoftSkill v2** is an advanced, real-time simulation platform designed to help individuals with High-Functioning Autism Spectrum Disorder (HFASD) practice social interactions. It leverages a modern Full-Stack architecture, containerized AI services, and a responsive 3D avatar to create a safe, adaptive learning environment.

---

## 🚀 Quick Start

### Prerequisites
*   **Software:** Docker Desktop, Git.

### Installation & Running

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/KingDor/Seminar.git
    cd Seminar
    ```

2.  **Start the Application:**
    Use the provided start script. It builds all containers, sets up the database, and initializes the AI models (Ollama & Whisper).
    ```bash
    ./start.sh
    ```
    *Note: The first run may take a few minutes as it downloads the Llama 3.2 model inside the Ollama container.*

3.  **Access:**
    *   **Frontend:** [http://localhost:3000](http://localhost:3000)
    *   **Backend API:** [http://localhost:5001](http://localhost:5001)

---

## 🧠 AI Architecture

SoftSkill v2 uses a containerized microservices approach for its AI capabilities.

*   **LLM (Brain):** **Llama 3.2 (3B)** running via **Ollama**.
    *   Hosted in a dedicated Docker container.
    *   Provides low-latency, conversational intelligence.
*   **STT (Ears):** **Faster-Whisper** (running locally in `ai_service`).
    *   Converts user speech to text with high accuracy.
*   **TTS (Voice):** **gTTS (Google Text-to-Speech)**.
    *   Synthesizes natural-sounding speech for the avatar.
    *   *Note: Switched from Edge-TTS to gTTS for robust container connectivity.*

---

## 🏗 System Architecture

The project follows a modular **Microservices** pattern orchestrated via Docker Compose.

### 1. Frontend (`/frontend`)
*   **Tech:** Next.js 16 (React), TypeScript, Tailwind CSS.
*   **Features:**
    *   **Authentication:** Secure Login/Register with JWT & HTTP-Only Cookies.
    *   **Dashboard:** Personalized user home with session history.
    *   **Real-Time Audio:** WebSocket-based full-duplex audio streaming.
    *   **3D Avatar:** Interactive avatar (React Three Fiber) that lipsyncs to AI speech.

### 2. Backend API (`/backend`)
*   **Tech:** Node.js, Express, TypeScript.
*   **Database:** PostgreSQL 16.
*   **Role:**
    *   User Management (Auth, Profiles).
    *   Session Tracking (History, Analytics).
    *   Secure API endpoints.

### 3. AI Service (`/ai_service`)
*   **Tech:** Python (FastAPI).
*   **Role:** The Central Intelligence Hub.
*   **Pipeline:**
    1.  **WebSocket** receives raw audio chunks.
    2.  **VAD (Voice Activity Detection)** filters silence.
    3.  **STT** transcribes speech.
    4.  **LLM** (Ollama) generates a context-aware response.
    5.  **TTS** converts text to audio.
    6.  **Response** sent back to Frontend (Text + Audio) in real-time.

### 4. Infrastructure
*   **Docker Compose:** Manages all services (`frontend`, `backend`, `ai_service`, `db`, `ollama`) and their networking.
*   **Hot-Reloading:** All services (Frontend, Backend, AI) are configured with volume mounts for active local development.

---

## 🛠 Development

### Active Development
The project is configured for **Hot-Reloading**.
*   **Frontend:** Edit files in `/frontend` -> Next.js updates instantly.
*   **Backend:** Edit files in `/backend` -> Server restarts automatically.
*   **AI Service:** Edit files in `/ai_service` -> FastAPI reloads.

### Database
*   **ORM:** None (Raw SQL via `pg` driver for performance/control).
*   **Migrations:** `backend/db/init.sql` initializes the schema on first run.

---

## 🧪 Testing
*   **Frontend:** Jest + React Testing Library.
    ```bash
    cd frontend
    npm test
    ```
*   **Backend:** Jest.
    ```bash
    cd backend
    npm test
    ```
*   **AI Service:** Pytest.
    ```bash
    docker-compose exec ai_service pytest
    ```

---

## 👥 Credits
**Students:** Dor Israeli, Or Yona
**Advisor:** Dr. Hadas Hasidim
**College:** SCE - Sami Shamoon College of Engineering