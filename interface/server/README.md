# NEXUS Interface Server

**Status**: Active (Cycle 011)
**Tech**: FastAPI, Uvicorn

## Overview
This directory contains the lightweight API bridge that connects external interfaces (like the React Frontend) to the NEXUS Core.

## Components

### `app.py`
The main entry point for the API server. It exposes endpoints that trigger NEXUS Core functionality.

- **Port**: 8080 (Default)
- **CORS**: Enabled for `localhost:3000` (Frontend)

## Endpoints

### `POST /api/generate`
Triggers the Generative UI engine.

**Request:**
```json
{
  "prompt": "Create a login page"
}
```

**Response:**
```json
{
  "status": "success",
  "file": "path/to/generated/file.tsx",
  "message": "Component generated successfully"
}
```

### `GET /health`
Health check endpoint.

## Architecture
The server imports `core.ui.generator.ComponentGenerator` directly, bridging the HTTP/JSON world of the frontend with the Python class-based world of the Core.

## Usage

**Run from Project Root:**
```bash
# Important: Run as module or ensure PYTHONPATH includes project root
python interface/server/app.py
```

*Note: The script includes a `sys.path` patch to locate the `core` module.*
