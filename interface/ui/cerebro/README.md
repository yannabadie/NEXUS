# NEXUS CEREBRO Interface

**Status**: Active (Cycle 011)
**Stack**: React, Vite, TailwindCSS (v4), TypeScript

## Overview
CEREBRO is the visual cortex of NEXUS. It provides a real-time window into the AI's operations and a canvas for Generative UI.

## Key Areas

### Generative Canvas (`src/pages/GenerativeCanvas.tsx`)
The primary interface for the "UX Singularity".
- **Dynamic Loading**: Uses `import.meta.glob` to hot-load generated components without server restarts.
- **Feedback Loop**: Displays real-time status from the generation engine.
- **Interaction**: "Regenerate" button triggers the Core API.

### Quantum Loader
A signature UI element (`QuantumLoader`) that provides visual feedback during the asynchronous generation process (5-15s latency).

## Development

```bash
# Start Dev Server
npm run dev
```

**Port**: 3000
**Proxy**: Requests to `/api` are proxied to `localhost:8080` (Interface Server).
