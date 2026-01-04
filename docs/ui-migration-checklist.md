---
title: UI Migration Checklist
---

## Design System
- [x] Port reference tokens and typography into `frontend/app/globals.css`
- [x] Add base utilities (`font-heading`, `font-body`, `animate-fade-in`, `hover-lift`, `chat-bubble-enter`)
- [x] Create UI primitives (`Button`, `Input`, `Textarea`, `Card`, `Badge`)
- [x] Add layout shells (`PageShell`, `AuthShell`)

## Navigation and Shell
- [x] Refactor `frontend/components/Navbar.tsx` to reference-style layout

## Pages
- [x] `/login` (auth card layout + form styling)
- [x] `/register` (auth card layout + form styling)
- [x] `/home` (dashboard shell + scenario grid)
- [x] `/sessions` (analytics overview + session list)
- [x] `/sessions/[sessionId]` (transcript detail)
- [x] `/sessions/[sessionId]/report` (report + charts)
- [x] `/profile` (profile editor)
- [x] `/meeting/[scenarioId]` (meeting experience)

## Key Components
- [x] `frontend/components/LobbyView.tsx`
- [x] `frontend/components/FaceTimeView.tsx`
- [x] `frontend/components/dashboard/MetricCard.tsx`
- [x] `frontend/components/dashboard/TranscriptViewer.tsx`
- [x] `frontend/app/sessions/[sessionId]/report/AICoachSummary.tsx`
- [x] `frontend/app/sessions/[sessionId]/report/EmotionalArcChart.tsx`
