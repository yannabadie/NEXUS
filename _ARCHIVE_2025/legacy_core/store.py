import sqlite3
import json
import os
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from .contracts import NexusState, TaskRequest, TaskResult, create_initial_state

# --- JSON Helpers ---

class NexusJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Pydantic models have a .dict() or .model_dump()
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return super().default(obj)

def nexus_json_serializer(obj: Any) -> str:
    return json.dumps(obj, cls=NexusJSONEncoder)

def nexus_json_deserializer(json_str: str) -> Any:
    return json.loads(json_str)

# --- Store Implementation ---

class NexusStore:
    def __init__(self, db_path: str = "20_NEXUS/nexus.db"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL;")
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_conn() as conn:
            # Table unique pour l'état global (Singleton)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS nexus_state (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    json_data TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Table pour l'historique des tâches
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_log (
                    task_id TEXT PRIMARY KEY,
                    status TEXT,
                    priority TEXT,
                    request_json TEXT NOT NULL,
                    result_json TEXT,
                    created_at TIMESTAMP,
                    completed_at TIMESTAMP
                );
            """)
            conn.commit()

    def save_state(self, state: NexusState):
        """Persist the full state object."""
        state.update_timestamp()
        json_data = nexus_json_serializer(state)
        
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO nexus_state (id, json_data, updated_at)
                VALUES (1, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    json_data=excluded.json_data,
                    updated_at=excluded.updated_at;
            """, (json_data, datetime.now().isoformat()))
            conn.commit()

    def load_state(self) -> NexusState:
        """Load the state or create a new one if empty."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT json_data FROM nexus_state WHERE id = 1")
            row = cursor.fetchone()
            
            if row:
                data = nexus_json_deserializer(row[0])
                return NexusState(**data)
            else:
                # Bootstrapping new state
                initial_state = create_initial_state(
                    session_id="boot_" + datetime.now().strftime("%Y%m%d"),
                    project_root=os.getcwd()
                )
                self.save_state(initial_state)
                return initial_state

    def log_task(self, request: TaskRequest, result: Optional[TaskResult] = None):
        """Log a task transaction (Request + optional Result)."""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO task_log (
                    task_id, status, priority, 
                    request_json, result_json, 
                    created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    status=excluded.status,
                    result_json=excluded.result_json,
                    completed_at=excluded.completed_at;
            """, (
                str(request.id),
                result.status.value if result else "pending",
                request.priority.value,
                nexus_json_serializer(request),
                nexus_json_serializer(result) if result else None,
                request.created_at.isoformat(),
                result.completed_at.isoformat() if result else None
            ))
            conn.commit()

    def get_recent_history(self, limit: int = 10) -> List[Dict]:
        """Get raw dicts of recent tasks."""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT task_id, status, request_json, result_json 
                FROM task_log 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "task_id": row[0],
                    "status": row[1],
                    "request": nexus_json_deserializer(row[2]),
                    "result": nexus_json_deserializer(row[3]) if row[3] else None
                })
            return history

    def reset(self):
        """Danger: Wipes the DB."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self._init_db()
