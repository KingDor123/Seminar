```mermaid
flowchart TD
    %% Global Styles
    classDef client fill:#f9f9f9,stroke:#333,stroke-width:2px,rx:10,ry:10;
    classDef service fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,rx:5,ry:5;
    classDef storage fill:#fff9c4,stroke:#fbc02d,stroke-width:2px,rx:5,ry:5;
    classDef external fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,rx:5,ry:5;
    classDef process fill:#fff,stroke:#333,stroke-width:1px,stroke-dasharray: 5 5;

    %% Nodes
    Client([👤 Frontend Client])

    subgraph AI_Service_Container [AI Service Architecture]
        direction TB
        Router["📡 Router / Controller<br/>POST /ai/interact"]

        subgraph Preprocessing_Layer [Layer 1: Normalization & Safety]
            AudioNorm["🔊 Preprocessor.normalize_audio<br/>(FFmpeg)"]
            TextClean["🧹 Preprocessor.process_text<br/>(Regex Filter)"]
        end

        subgraph Perception_Layer [Layer 2: Perception]
            STT["🗣️ STT Service<br/>(Faster-Whisper)"]
        end

        subgraph Cognition_Layer [Layer 3: Cognition]
            LLM["🧠 LLM Service<br/>(Ollama Llama 3.2)"]
            TTS["🔈 TTS Service<br/>(gTTS)"]
        end
    end

    subgraph Backend_Container [Backend Infrastructure]
        DB[(🗄️ Database)]
        HistoryAPI[📜 History API]
        AnalyticsAPI[📊 Analytics API]
    end

    %% Data Flow Connections
    Client -- "1. Audio / Text (HTTP Stream)" --> Router

    %% Audio Path
    Router -- "2. Raw Bytes (WebM)" --> AudioNorm
    AudioNorm -- "3. 16kHz WAV" --> STT
    STT -- "4. Raw Text" --> TextClean

    %% Text Path
    TextClean -- "5. Clean Text & Filler Count" --> Router

    %% Context & Inference
    Router -. "6. GET Context (Auth Key)" .-> HistoryAPI
    HistoryAPI -. "Prior Messages" .-> Router

    Router -- "7. Prompt + Context" --> LLM
    LLM -- "8. Token Stream" --> Router

    %% Output Generation
    Router -- "9. Sentence Boundary" --> TTS
    TTS -- "10. Audio Chunk (Base64)" --> Router
    Router -- "11. SSE Stream" --> Client

    %% Analytics (Async)
    Router -.->|"12. POST Metrics (Async)"| AnalyticsAPI
    AnalyticsAPI --- DB

    %% Applying Styles
    class Client client;
    class Router,AudioNorm,TextClean,STT,LLM,TTS service;
    class DB,HistoryAPI,AnalyticsAPI storage;
