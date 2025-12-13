# NEXUS Dashboard Frontend

Modern real-time dashboard for NEXUS multi-agent orchestration system.

## Tech Stack

- **Framework**: Next.js 16 (App Router, TypeScript)
- **Styling**: Tailwind CSS + shadcn/ui
- **State**: React hooks + Zustand (optional)
- **Real-time**: WebSocket to FastAPI backend

## Quick Start

```bash
# Install dependencies
npm install

# Create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Backend Requirements

The dashboard connects to the FastAPI backend at `http://localhost:8000`:

```bash
# From project root
cd core/ui
python dashboard_server.py
```

## Features

| Panel | Description |
|-------|-------------|
| **FSM State** | Current orchestrator state |
| **HiveMind Tracker** | 7-phase progress visualization |
| **Agent Constellation** | Gemini, Claude, spawned agents |
| **Budget Monitor** | Token usage and limits |
| **WebSocket Feed** | Real-time telemetry |

## Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx    # NEXUS branding, dark mode
│   │   └── page.tsx      # Main dashboard
│   ├── hooks/
│   │   └── useNexusWebSocket.ts  # WebSocket hook
│   └── lib/
│       ├── api.ts        # Typed API client
│       └── utils.ts      # shadcn utilities
```

## API Endpoints Used

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/self-awareness` | GET | Metacognition panel |
| `/api/orchestration` | GET | FSM/Swarm/HiveMind state |
| `/api/budget` | GET | Budget status |
| `/api/agents` | GET | Agent list |
| `/ws` | WS | Real-time telemetry |
