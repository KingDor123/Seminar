# SoftSkill v2: AI-Driven Social Skills Training Platform

**SoftSkill v2** is an advanced, real-time simulation platform designed to help individuals with High-Functioning Autism Spectrum Disorder (HFASD) practice social interactions. It leverages a custom Fine-Tuned Large Language Model (LLM), real-time voice synthesis, and a responsive 3D avatar to create a safe, adaptive learning environment.

---

## 🚀 Quick Start

### Prerequisites
*   **Hardware:** Apple Silicon Mac (M1/M2/M3) recommended for MLX acceleration.
*   **Software:** Docker Desktop, Python 3.11+, Git.

### Installation
1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/KingDor/Seminar.git
    cd Seminar
    ```

2.  **Start the Application:**
    Use the provided start script. It handles everything: downloading the model, starting the AI brain, and launching the Docker stack.
    ```bash
    ./start.sh
    ```

3.  **Access:**
    *   **Frontend:** [http://localhost:3000](http://localhost:3000)
    *   **API Docs:** [http://localhost:5001/api-docs](http://localhost:5001/api-docs) (Backend)

---

## 🧠 AI Brain (The Core)

The heart of SoftSkill v2 is a custom-trained AI model designed to act as a "Soft Skills Coach."

*   **Model:** `SoftSkillSensei` (Fine-tuned Llama 3.2 3B).
*   **Training:** Trained using **LoRA (Low-Rank Adaptation)** on Apple Silicon via `mlx-lm`.
*   **Dataset:** Custom-generated synthetic dataset focusing on:
    *   **Theory of Mind (ToM):** Explaining hidden intentions.
    *   **Video Modeling + Feedback:** Acting, then pausing to critique.
    *   **Cognitive Flexibility:** Introducing gentle plot twists.
    *   **Neurodiversity Affirming:** Using functional, non-judgmental language.
*   **Hosting:** Runs natively on the Host Machine (macOS) via `mlx_lm.server` to leverage the Neural Engine (GPU), exposed on port `8081`.

---

## 🏗 Architecture

The system uses a **Hybrid Architecture** to maximize performance on Mac hardware while keeping services isolated.

### 1. Frontend (`/frontend`)
*   **Tech:** Next.js 14 (React), TypeScript, Tailwind CSS.
*   **Features:**
    *   **Real-Time Audio:** Uses `AudioContext` to stream raw PCM (Float32) audio.
    *   **3D Avatar:** Visualizes the AI persona (Three.js / React Three Fiber).
    *   **WebSocket:** Manages full-duplex state (Listening -> Thinking -> Speaking).

### 2. Backend API (`/backend`)
*   **Tech:** Node.js, Express.
*   **Role:** User management, Session tracking, Database persistence (PostgreSQL).
*   **Port:** 5001.

### 3. AI Service (`/ai_service`)
*   **Tech:** Python (FastAPI).
*   **Role:** The Orchestrator.
*   **Pipeline:**
    1.  **STT:** `Faster-Whisper` (local) converts user speech to text.
    2.  **VAD:** Voice Activity Detection buffers audio to ensure complete sentences.
    3.  **LLM:** Forwards prompt to the Host MLX Server (`http://10.0.0.14:8081`).
    4.  **TTS:** `Edge-TTS` converts AI text response to audio bytes.
    5.  **Stream:** Sends audio + transcripts back to Frontend via WebSocket.

### 4. Infrastructure
*   **Docker Compose:** Orchestrates the containers (Frontend, Backend, AI Service, DB).
*   **Start Script (`start.sh`):**
    *   Checks for the custom model (`models/softskill-llama3.2-3b`).
    *   Auto-downloads it from Hugging Face (`KingDor/softskill-llama3.2-3b`) if missing.
    *   Launches the MLX Server in the background.
    *   Starts Docker containers.
    *   Handles cleanup (SIGINT).

---

## 🛠 Development & Training

### How to Re-Train the Brain
If you want to improve the model:

1.  **Update Data:** Edit `ai_engine/training/data/train_enhanced.jsonl`.
2.  **Run Training:**
    ```bash
    python3 ai_engine/training/scripts/train_mlx.py
    ```
    This will run 600 iterations and save the new model to `ai_engine/models/`.

### How to Upload to Cloud
To sync your model changes to Hugging Face:
```bash
python3 ai_engine/upload_model.py
```

---

## 🧪 Testing
*   **Unit Tests (AI Service):**
    ```bash
    cd ai_service
    pytest
    ```
*   **Frontend Tests:**
    ```bash
    cd frontend
    npm test
    ```

---

## 👥 Credits
**Students:** Dor Israeli, Or Yona
**Advisor:** Dr. Hadas Hasidim
**College:** SCE - Sami Shamoon College of Engineering
