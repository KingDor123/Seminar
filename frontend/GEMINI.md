# Frontend Project Overview

This is the frontend application for a Seminar/AI Coaching platform. It is built using **Next.js 16 (App Router)**, **React 19**, and **TypeScript**. The application features an interactive interface with 3D avatars, real-time chat, and text-to-speech (TTS) capabilities, designed for Hebrew-speaking users (`he-IL`).

## Tech Stack

- **Framework:** Next.js 16.0.5 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4, Lucide React (Icons)
- **State Management:** React Context (`AuthContext`), Custom Hooks
- **Data Fetching:** Axios, Native Fetch (in specific hooks)
- **3D/Graphics:** Three.js, React Three Fiber (`@react-three/fiber`, `@react-three/drei`)
- **Validation:** Zod, React Hook Form
- **Testing:** Jest, React Testing Library
- **Charts:** Recharts

## Architecture & Key Concepts

### Directory Structure

- **`app/`**: Contains the application routes and pages.
    - `layout.tsx`: Root layout including `AuthProvider` and `Navbar`. Sets `dir="rtl"` and `lang="he-IL"`.
    - `(routes)`: `login`, `register`, `home`, `meeting`, `sessions`, `profile`.
    - `page.tsx`: Root entry point, currently redirects to `/login`.
- **`components/`**: Reusable UI components.
    - `ui/`: Basic UI building blocks (likely Shadcn UI or similar).
    - `auth/`, `dashboard/`, `home/`, `layout/`: Feature-specific components.
    - `Avatar3D.tsx`, `LivingAvatar.tsx`: 3D Avatar rendering and animation components.
- **`context/`**: Global state providers.
    - `AuthContext.tsx`: Manages user authentication state.
- **`hooks/`**: Custom React hooks.
    - `useApi.ts`: API resolution.
    - `useTTS.ts` (in `useApi.ts`): Manages Text-to-Speech interaction and Visemes.
    - `useChatSession.ts`, `useStreamingConversation.ts`: Logic for chat and real-time interaction.
- **`lib/`**: Utilities and configurations.
    - `api.ts`: Pre-configured Axios instance (`baseURL: '/api'`).
    - `utils.ts`: Helper functions (e.g., `cn` for class merging).
- **`middleware.ts`**: Handles route protection. Redirects unauthenticated users to `/login` and authenticated users to `/home`.
- **`constants/`**:
    - `he.ts`: Hebrew localization strings and constants.

### Key Features

1.  **Authentication:** Protected by Middleware. Uses JWT/Token-based auth managed via cookies and `AuthContext`.
2.  **3D Avatars:** Uses React Three Fiber to render interactive 3D models (`.glb` files in `public/`). Supports viseme-based lip-syncing.
3.  **Real-time Communication:**
    - WebSocket support (implied by `useWebSocketUrl`).
    - TTS integration for voice interaction.
4.  **Localization:** The app is hardcoded for Hebrew (`he-IL`) with RTL layout support.

## Development Workflow

### Scripts

- **Development:** `npm run dev` (Starts server on http://localhost:3000)
- **Build:** `npm run build`
- **Lint:** `npm run lint`
- **Test:** `npm run test` (Runs Jest)

### Conventions

- **Styling:** Use Tailwind utility classes. Use `cn()` for conditional class merging.
- **Components:** Functional components with TypeScript interfaces for props.
- **API Calls:** Use the `api` instance from `@/lib/api` for general requests. Use specific hooks (`useTTS`) for specialized features.
- **Files:** Place assets in `public/`. Place 3D models (GLB/GLTF) in `public/`.

## Setup & Configuration

- **Environment Variables:** Configuration is likely handled via `.env.local` (standard Next.js), though specific variables weren't inspected.
- **Proxy:** API requests to `/api` are expected to be handled by the Next.js server or proxied to a backend service.
