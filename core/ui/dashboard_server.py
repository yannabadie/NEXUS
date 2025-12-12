import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from core.agents.unified_registry import get_registry, AgentDescriptor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.dashboard")

app = FastAPI(title="NEXUS Singularity Dashboard")

# CORS (Allow all for prototype)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

manager = ConnectionManager()

# --- API Endpoints ---

@app.get("/")
async def get_dashboard():
    """Serve the main dashboard HTML."""
    index_path = STATIC_DIR / "nexus_dashboard.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>NEXUS Dashboard Loading... (Please build frontend)</h1>")

@app.get("/api/agents")
async def get_agents():
    """Get all registered agents."""
    registry = get_registry()
    agents = registry.list_available()
    return [
        {
            "id": a.id,
            "name": a.display_name,
            "provider": a.provider.value,
            "capabilities": [c.value for c in a.capabilities],
            "dylan_scores": a.dylan_scores,
            "is_spawned": a.provider.value == "spawned"
        }
        for a in agents
    ]

@app.get("/api/files")
async def get_files(path: str = ""):
    """Recursive file scan of workspace/."""
    root = Path("workspace")
    target = root / path
    
    if not target.exists():
        return {"error": "Path not found"}
        
    def scan(p: Path) -> Dict[str, Any]:
        name = p.name
        is_dir = p.is_dir()
        return {
            "name": name,
            "path": str(p.relative_to(root)).replace("\\", "/"),
            "type": "directory" if is_dir else "file",
            "children": [scan(child) for child in p.iterdir()] if is_dir else []
        }
        
    try:
        return scan(target)
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/telemetry")
async def receive_telemetry(event: Dict[str, Any]):
    """Receive telemetry from NEXUS Core and broadcast to UI."""
    # event = {"type": "...", "data": ...}
    await manager.broadcast(json.dumps(event))
    return {"status": "ok"}

@app.get("/api/dependencies")
async def get_dependencies():
    """Get the Neural Code Map (dependencies)."""
    try:
        from core.ui.code_mapper import code_mapper
        return code_mapper.scan()
    except ImportError:
        return {"nodes": [], "edges": []}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- File Watcher (V9.1) ---
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    class NexusFileHandler(FileSystemEventHandler):
        def on_any_event(self, event):
            if event.is_directory:
                return
            
            # Filter for workspace/
            path = Path(event.src_path)
            try:
                rel_path = path.relative_to(Path("workspace"))
                # Broadcast event
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(json.dumps({
                        "type": "FILE_EVENT",
                        "event": event.event_type,
                        "path": str(rel_path).replace("\\", "/")
                    })),
                    loop
                )
            except ValueError:
                pass # Not in workspace

    observer = Observer()
    observer.schedule(NexusFileHandler(), path="workspace", recursive=True)
    observer.start()
except ImportError:
    logger.warning("Watchdog not installed. File watching disabled.")

# --- Log Streaming Hook ---
# In a real app, we'd hook into the logging handler.
# For prototype, we'll simulate or expose a method to push logs.

async def push_log(message: str):
    await manager.broadcast(json.dumps({"type": "log", "content": message}))

if __name__ == "__main__":
    import uvicorn
    # Need to capture loop for threadsafe calls
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    uvicorn.run(app, host="0.0.0.0", port=8000)
