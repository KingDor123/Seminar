---
title: UI Blueprint - my-safe-space to Seminar
reference_repo: /Users/dortheking/code/ui-reference/my-safe-space
target_repo: /Users/dortheking/Code/Seminar
---

## Reference Discovery (my-safe-space)

### Stack and Styling
- Framework: Vite + React + TypeScript
- Routing: react-router-dom
- Styling: Tailwind CSS 3.4 with CSS variables in `src/index.css`
- UI kit: shadcn/ui components + Radix primitives in `src/components/ui`
- Icons: lucide-react
- Utilities: `clsx`, `tailwind-merge` via `src/lib/utils.ts`

### Design Tokens (from `src/index.css` and `tailwind.config.ts`)
Fonts:
- Heading: Quicksand (`font-heading`)
- Body: Nunito (`font-body`)
- Google Fonts import in `src/index.css`

CSS variables (HSL):
```
--background: 150 20% 98%
--foreground: 200 15% 25%
--card: 150 25% 97%
--card-foreground: 200 15% 25%
--popover: 150 25% 97%
--popover-foreground: 200 15% 25%
--primary: 150 30% 45%
--primary-foreground: 150 20% 98%
--secondary: 35 25% 93%
--secondary-foreground: 200 15% 25%
--muted: 150 15% 92%
--muted-foreground: 200 10% 50%
--accent: 220 25% 92%
--accent-foreground: 220 20% 35%
--destructive: 0 50% 60%
--destructive-foreground: 0 0% 100%
--border: 150 15% 88%
--input: 150 15% 90%
--ring: 150 30% 45%
--radius: 1rem

--calm: 175 35% 50%
--calm-soft: 175 35% 95%
--support: 220 40% 55%
--support-soft: 220 40% 95%
--social: 35 60% 55%
--social-soft: 35 60% 95%
--focus: 280 30% 55%
--focus-soft: 280 30% 95%

--chat-user: 150 30% 92%
--chat-bot: 0 0% 100%

--stat-positive: 150 40% 45%
--stat-neutral: 220 25% 55%
--stat-accent: 35 50% 55%

--sidebar-background: 0 0% 98%
--sidebar-foreground: 240 5.3% 26.1%
--sidebar-primary: 240 5.9% 10%
--sidebar-primary-foreground: 0 0% 98%
--sidebar-accent: 240 4.8% 95.9%
--sidebar-accent-foreground: 240 5.9% 10%
--sidebar-border: 220 13% 91%
--sidebar-ring: 217.2 91.2% 59.8%
```

Tailwind config highlights (`tailwind.config.ts`):
- `fontFamily.heading`: Quicksand
- `fontFamily.body`: Nunito
- Container: centered, `padding: 2rem`, `2xl` = 1400px
- Radii map: `lg` = `var(--radius)` (1rem), `md` = radius - 2px, `sm` = radius - 4px
- Custom color groups: sidebar, calm/support/social/focus, chat, stat

Motion utilities (from `src/index.css`):
- `animate-fade-in` (0.4s ease-out, slight translateY)
- `animate-soft-pulse` (2s ease-in-out)
- `hover-lift` (transition + translateY + shadow on hover)
- `chat-bubble-enter` (0.3s ease-out, translateY + scale)

Spacing and shape:
- Heavy use of `rounded-2xl` and `rounded-xl` for cards and icon containers.
- Buttons and inputs use `rounded-xl` or `rounded-md` with soft borders.
- Paddings: `p-4`, `p-6`, `px-4`, `py-3`, `gap-4`, `gap-6` dominate.
- Subtle shadows: `shadow-lg`, `shadow-xl`, and tinted shadows on hover.

### Reference Component Inventory
Layout and navigation:
- `src/components/layout/Layout.tsx`: page shell, `Navigation` + main padding.
- `src/components/layout/Navigation.tsx`: fixed bottom nav on mobile, fixed top on desktop, blurred background, pill nav items.

Home:
- `src/components/home/WelcomeHeader.tsx`
- `src/components/home/ConversationCard.tsx`: rounded-2xl card, colored variant styles and hover lift.

Chat:
- `src/components/chat/ChatMessage.tsx`
- `src/components/chat/ChatInput.tsx`
- `src/components/chat/TypingIndicator.tsx`

Sessions:
- `src/components/sessions/StatCard.tsx`
- `src/components/sessions/SessionCard.tsx`

Shared UI primitives (shadcn):
- `src/components/ui/*` (button, input, textarea, card, badge, tabs, select, dialog, toast, etc.)

Page shells:
- `src/pages/Index.tsx` (Home)
- `src/pages/Chat.tsx`
- `src/pages/Sessions.tsx`

### Reference Patterns to Match
- Soft sage primary with muted neutral surfaces.
- Consistent `rounded-2xl` cards + light borders (`border-border`).
- Mobile-first navigation: bottom nav (mobile), top bar (md+).
- Typography: heading font for titles, body font for body text.
- Gentle motion: fade-in on entry, hover-lift on cards, chat bubble enter.
- Focus rings use `ring` token (primary).

## Target Discovery (Seminar / frontend)

### Stack and Styling
- Framework: Next.js 16 + React 19 + TypeScript
- Styling: Tailwind CSS v4 via `@import "tailwindcss"` in `app/globals.css`
- Fonts: Inter via `next/font/google` in `app/layout.tsx`
- Icons: lucide-react

### Pages (App Router)
- `/` -> redirect to `/login`
- `/login`
- `/register`
- `/home`
- `/sessions`
- `/profile`
- `/meeting/[scenarioId]`

### Key Components
- Layout shell: `frontend/app/layout.tsx`, `frontend/components/Navbar.tsx`
- Home flow: `frontend/components/LobbyView.tsx`
- Meeting UI: `frontend/components/FaceTimeView.tsx`, `frontend/components/Avatar3D.tsx`
- Sessions analytics: `frontend/components/dashboard/MetricCard.tsx` (plus unused helpers)

### UI Primitives Needed (Target)
- Button (variants: primary, secondary, ghost, outline)
- Input / Textarea
- Card (surface, stat, chat bubble)
- Badge / Pill
- Tabs / Segmented control (if needed)
- Modal / Dialog (optional)
- Toast / Alert
- Table styling

## Migration Plan (Target)
1) Global tokens and typography:
   - Port reference CSS variables and fonts into `frontend/app/globals.css`.
   - Add utility classes for `font-heading`, `font-body`, `animate-fade-in`, `hover-lift`, `chat-bubble-enter`.
2) UI primitives:
   - Create `frontend/components/ui` with Button, Input, Textarea, Card, Badge, etc., matching reference styles.
3) Layout shell and navigation:
   - Refactor `Navbar` into a reference-style nav (fixed bottom on mobile, fixed top on desktop).
4) Page-by-page:
   - `/login`, `/register` -> reference-like centered card + muted background.
   - `/home` -> reference card grid layout and stat cards.
   - `/sessions` -> reference `StatCard` + `SessionCard` layout.
   - `/meeting/[scenarioId]` -> soften palette and align to reference surfaces while keeping layout/functionality.
   - `/profile` -> align to reference card styles and typography.
