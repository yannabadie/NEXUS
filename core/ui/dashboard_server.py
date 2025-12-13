import os
import json
import sys
from pathlib import Path

# Add project root to sys.path
root_path = Path(__file__).resolve().parents[2]
sys.path.append(str(root_path))

import asyncio
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil

# --- App Initialization ---

from core.agents.unified_registry import get_registry, AgentDescriptor
from core.workspace.manager import WorkspaceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nexus.dashboard")

# app instantiation moved to lifespan section

# CORS (Allow all for prototype)
# Middleware and Static Files moved below app instantiation

# --- Lifespan Events (Startup/Shutdown) ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    observer = None
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        
        # Capture the running loop from the main thread
        main_loop = asyncio.get_running_loop()

        class NexusFileHandler(FileSystemEventHandler):
            def __init__(self, loop):
                self.loop = loop

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
                        self.loop
                    )
                except ValueError:
                    pass # Not in workspace

        # Use absolute path for workspace
        workspace_path = root_path / "workspace"
        observer = Observer()
        observer.schedule(NexusFileHandler(main_loop), path=str(workspace_path), recursive=True)
        observer.start()
        logger.info("Watchdog observer started.")
    except ImportError:
        logger.warning("Watchdog not installed. File watching disabled.")
    except Exception as e:
        logger.error(f"Failed to start watchdog: {e}")

    yield

    # Shutdown
    if observer:
        observer.stop()
        observer.join()

app = FastAPI(title="NEXUS Singularity Dashboard", lifespan=lifespan)

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

@app.get("/")
async def read_root():
    return FileResponse(STATIC_DIR / "nexus_dashboard.html")

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

# --- Cockpit Endpoints (Phase 35) ---

@app.post("/api/agents")
async def create_agent(agent_data: Dict[str, Any]):
    """Create a new agent (Spawn)."""
    try:
        workspace = Path("workspace")
        agents_dir = workspace / "agents"
        agents_dir.mkdir(exist_ok=True)
        
        agent_id = agent_data.get("name", "unnamed").lower().replace(" ", "_")
        file_path = agents_dir / f"{agent_id}.json"
        
        if file_path.exists():
            return {"error": "Agent already exists"}
            
        # Create agent definition
        agent_def = {
            "id": agent_id,
            "name": agent_data.get("name"),
            "provider": "spawned",
            "capabilities": agent_data.get("capabilities", []),
            "system_prompt": agent_data.get("system_prompt", ""),
            "memory_paths": []
        }
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(agent_def, f, indent=2)
            
        return {"status": "created", "id": agent_id}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/memory/upload")
async def upload_memory(file: UploadFile = File(...)):
    """Upload a document to workspace memory."""
    try:
        workspace = Path("workspace")
        incoming_dir = workspace / "documents" / "incoming"
        incoming_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = incoming_dir / file.filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        return {"status": "uploaded", "path": str(file_path)}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/chat")
async def send_chat(message: Dict[str, str]):
    """
    V10: Send a chat message to NEXUS Core via embedded orchestrator.
    
    This invokes real Gemini/Claude agents, not a mock.
    Agent responses are streamed via EventBus → WebSocket.
    """
    try:
        from core.ui.dashboard_orchestrator import get_dashboard_orchestrator
        
        content = message.get("content", "")
        if not content:
            return {"error": "Empty message"}
        
        # Get orchestrator and process message
        orchestrator = get_dashboard_orchestrator()
        
        # Process through real NEXUS agents
        result = await orchestrator.process_message(content)
        
        if "error" in result:
            return {"error": result["error"], "response": f"Error: {result['error']}"}
        
        return {
            "response": result.get("response", ""),
            "agent": result.get("agent", "NEXUS"),
            "state": result.get("state", "IDLE"),
            "finished": result.get("finished", False)
        }
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return {"error": str(e), "response": f"Error: {str(e)}"}

# --- Control Endpoints (Phase 41) ---

@app.post("/api/evolve/trigger")
async def trigger_evolve():
    """Trigger evolution via IPC."""
    return await send_ipc_command("/evolve")

@app.post("/api/swarm/trigger")
async def trigger_swarm(data: Dict[str, str]):
    """Trigger swarm via IPC."""
    task = data.get("task", "")
    return await send_ipc_command(f"/swarm {task}")

@app.post("/api/stop")
async def trigger_stop():
    """Trigger stop via IPC."""
    return await send_ipc_command("/stop")

async def send_ipc_command(command: str):
    """Helper to send IPC command."""
    try:
        workspace = Path("workspace")
        buffer_dir = workspace / "_IO_BUFFER"
        buffer_dir.mkdir(exist_ok=True)
        
        ipc_file = buffer_dir / "chat_input.json"
        
        payload = {
            "sender": "User (Dashboard)",
            "content": command,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        # Atomic write
        temp_file = ipc_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        
        temp_file.replace(ipc_file)
        return {"status": "sent", "command": command}
    except Exception as e:
        return {"error": str(e)}

# --- Workspace Management (Phase 42) ---

@app.get("/api/workspaces")
async def list_workspaces():
    """List all workspaces."""
    try:
        wm = WorkspaceManager(Path(".")) # Root is CWD
        workspaces = wm.list_workspaces()
        return [
            {
                "name": ws.name,
                "is_current": ws.is_current,
                "last_used": ws.last_used.isoformat() if ws.last_used else None,
                "created_at": ws.created_at.isoformat() if ws.created_at else None,
                "files_count": ws.metrics.files_count
            }
            for ws in workspaces
        ]
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/workspaces")
async def create_workspace(data: Dict[str, str]):
    """Create a new workspace."""
    try:
        name = data.get("name")
        wm = WorkspaceManager(Path("."))
        info = wm.create_workspace(name=name, archive_current=True)
        return {"status": "created", "name": info.name}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/workspaces/switch")
async def switch_workspace(data: Dict[str, str]):
    """Switch to another workspace."""
    try:
        name = data.get("name")
        if not name:
            return {"error": "Name required"}
            
        wm = WorkspaceManager(Path("."))
        info = wm.switch_workspace(name, save_current=True)
        
        # Trigger file refresh via watchdog implicitly, but let's force a broadcast
        await manager.broadcast(json.dumps({
            "type": "WORKSPACE_SWITCHED",
            "name": info.name
        }))
        
        return {"status": "switched", "name": info.name}
    except Exception as e:
        return {"error": str(e)}

# --- End Cockpit Endpoints ---

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

    except ImportError:
        return {"nodes": [], "edges": []}

@app.get("/api/memory/vectors")
async def get_memory_vectors():
    """Get semantic memory vectors for visualization."""
    try:
        from core.memory.project_memory import ProjectMemory
        # Initialize memory (read-only mode effectively)
        memory = ProjectMemory(Path("workspace")) # FIX: Use workspace path
        vectors = memory.get_all_vectors()
        
        data = []
        for v in vectors:
            vec = v["vector"]
            # Naive 3D projection: Use first 3 components (or averages)
            x = vec[0] * 10
            y = vec[1] * 10
            z = vec[2] * 10
            
            data.append({
                "id": v["id"],
                "pos": [x, y, z],
                "content": v["metadata"].get("content", "")[:100] + "..."
            })
            
        return data
    except Exception as e:
        return {"error": str(e)}

# --- New Endpoints (Phase 34) ---

@app.get("/api/evolve/status")
async def get_evolution_status():
    """Get evolution lineage statistics."""
    try:
        from core.evolution.lineage import load_lineage, get_evolution_stats
        workspace = Path("workspace")
        if not (workspace / "LINEAGE.json").exists():
             return {"status": "no_lineage", "stats": {}}
             
        lineage = load_lineage(workspace)
        stats = get_evolution_stats(lineage)
        parent = lineage.get("current_parent", {})
        
        return {
            "status": "active",
            "generation": lineage.get("generation", 1),
            "parent": {
                "id": parent.get("id", "unknown"),
                "score": parent.get("fitness_score", 0.0),
                "created_at": parent.get("created_at", "")
            },
            "stats": stats
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/budget")
async def get_budget_status():
    """Get current budget status."""
    try:
        from core.telemetry import BudgetTracker
        tracker = BudgetTracker(Path("workspace"))
        return tracker.get_stats()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/doctor")
async def run_doctor():
    """Run system diagnostics (read-only checks)."""
    try:
        from core.meta.cli_inspector import CLIInspector
        inspector = CLIInspector()
        
        # We can't easily check API keys from here without env vars, 
        # but we can check workspace health.
        workspace = Path("workspace")
        
        return {
            "workspace": {
                "exists": workspace.exists(),
                "agents": len(list((workspace / "agents").glob("*.json"))) if (workspace / "agents").exists() else 0,
                "memory": (workspace / "memory").exists()
            },
            "system": {
                "python": "3.13+", # Mock for now
                "os": os.name
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Subscribe to Event Bus (if we were in same process, but we are not)
        # For now, we rely on /api/telemetry to push events to us
        
        # Send initial connection message
        await websocket.send_json({
            "type": "LOG",
            "timestamp": asyncio.get_event_loop().time(),
            "data": {"message": "Connected to NEXUS Dashboard Server"}
        })

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Lifespan Events (Startup/Shutdown) ---
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    observer = None
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
                    # Need to use the loop that the app is running in
                    loop = asyncio.get_running_loop()
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
        logger.info("Watchdog observer started.")
    except ImportError:
        logger.warning("Watchdog not installed. File watching disabled.")
    except Exception as e:
        logger.error(f"Failed to start watchdog: {e}")

    yield

    # Shutdown
    if observer:
        observer.stop()
        observer.join()

# --- Phase A: Self-Awareness & Foundation Endpoints (UI Vision V10) ---

@app.get("/api/self-awareness")
async def get_self_awareness():
    """
    Return NEXUS's self-awareness: capabilities, current state, and reasoning.
    This powers the Metacognition Panel in the UI.
    """
    try:
        # Tools available
        tools = [
            "bash", "read", "write", "edit", "list_dir", "git",
            "web_search", "web_fetch", "glob", "grep", "todo_write",
            "create_tool", "delete_tool", "list_dynamic_tools", "run_dynamic_tool",
            "swarm_delegate"
        ]
        
        # Swarm modes
        swarm_modes = [
            "PARALLEL", "SEQUENTIAL", "LEAD_SUPPORT",
            "PING_PONG", "SPECIALIST", "RED_BLUE"
        ]
        
        # FSM States
        fsm_states = [
            "IDLE", "BRAINSTORMING", "EXECUTING_TOOL", "VALIDATING_CFL",
            "EVOLUTION_BRAINSTORM", "ADAPTATION"
        ]
        
        # Get agents from registry
        registry = get_registry()
        agents = []
        for agent in registry.list_available():
            agents.append({
                "id": agent.id,
                "name": agent.display_name,
                "provider": agent.provider.value,
                "domains": [c.value for c in agent.capabilities] if agent.capabilities else []
            })
        
        # Memory backends available
        memory_backends = ["tfidf", "bm25", "dense"]
        
        # HiveMind phases
        hive_phases = [
            "1. Parse", "2. Plan", "3. Assign", "4. Execute",
            "5. Validate", "6. Aggregate", "7. Report"
        ]
        
        # Current state (defaults - would need IPC to get live state)
        current_state = {
            "fsm": "IDLE",
            "hive_mind_phase": None,
            "swarm_mode": None,
            "active_task": None
        }
        
        return {
            "capabilities": {
                "tools": tools,
                "tool_count": len(tools),
                "swarm_modes": swarm_modes,
                "fsm_states": fsm_states,
                "memory_backends": memory_backends,
                "hive_phases": hive_phases
            },
            "agents": agents,
            "current_state": current_state,
            "version": "10.0-alpha",
            "self_description": "I am NEXUS, a self-evolving collaborative intelligence that combines Gemini and Claude to generate specialized agents."
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/rag/query")
async def rag_query(data: Dict[str, Any]):
    """
    Query semantic memory (RAG).
    POST body: {"query": "string", "top_k": 5, "backend": "dense|bm25|tfidf"}
    """
    try:
        query = data.get("query", "")
        top_k = data.get("top_k", 5)
        backend = data.get("backend", "bm25")  # Default to lightweight backend
        
        if not query:
            return {"error": "Query is required"}
        
        # Try to import project memory
        try:
            from core.memory.project_memory import ProjectMemory
            workspace = Path("workspace")
            memory = ProjectMemory(workspace)
            
            results = memory.search(query, top_k=top_k)
            
            return {
                "query": query,
                "backend": backend,
                "results": [
                    {
                        "content": r.get("content", "")[:500],
                        "score": r.get("score", 0),
                        "source": r.get("source", "unknown")
                    }
                    for r in results
                ]
            }
        except ImportError:
            return {"error": "ProjectMemory not available", "results": []}
        except Exception as e:
            return {"error": f"RAG query failed: {str(e)}", "results": []}
            
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/specialize/trigger")
async def trigger_specialize(data: Dict[str, str]):
    """
    Trigger specialization via IPC.
    POST body: {"mission": "Expert for this FastAPI project"}
    """
    mission = data.get("mission", "")
    if not mission:
        return {"error": "Mission is required"}
    return await send_ipc_command(f"/specialize {mission}")


@app.post("/api/rag/learn")
async def rag_learn(data: Dict[str, str]):
    """
    Learn a new pattern via IPC.
    POST body: {"pattern": "description of pattern to learn"}
    """
    pattern = data.get("pattern", "")
    if not pattern:
        return {"error": "Pattern is required"}
    return await send_ipc_command(f"/learn {pattern}")


@app.get("/api/orchestration/state")
async def get_orchestration_state():
    """
    Get current orchestration state for live visualization.
    Returns FSM state, Swarm mode, HiveMind phase.
    """
    try:
        # Read from blackboard if available
        blackboard_path = Path("workspace/.nexus/blackboard.json")
        if blackboard_path.exists():
            with open(blackboard_path, "r", encoding="utf-8") as f:
                blackboard = json.load(f)
                return {
                    "fsm_state": blackboard.get("current_state", "IDLE"),
                    "swarm_mode": blackboard.get("swarm_mode", None),
                    "hive_phase": blackboard.get("hive_phase", None),
                    "current_task": blackboard.get("current_task", None),
                    "last_agent": blackboard.get("last_agent", None)
                }
        else:
            return {
                "fsm_state": "IDLE",
                "swarm_mode": None,
                "hive_phase": None,
                "current_task": None,
                "last_agent": None
            }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
