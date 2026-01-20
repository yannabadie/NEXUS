# Workspace Module

## Synopsis
The Workspace module provides multi-workspace management for NEXUS sessions, allowing users to create, archive, switch between, and manage isolated workspaces. Each workspace maintains its own session data, metrics, and file structure, enabling organization of multiple projects or contexts. Includes workspace discovery, fuzzy name suggestions, and metrics tracking.

## Component Map
| File | Purpose | Key Exports |
|------|---------|-------------|
| `manager.py` | WorkspaceManager for create/switch/archive/list operations | `WorkspaceManager` |
| `models.py` | Data models for workspace info and metrics | `WorkspaceInfo`, `WorkspaceMetrics` |
| `exceptions.py` | Workspace-specific exceptions | `WorkspaceError`, `WorkspaceNotFoundError`, `WorkspaceExistsError`, `WorkspaceCorruptedError` |
| `__init__.py` | Module initialization with public exports | All classes from submodules |

## Key Interfaces

### WorkspaceManager

**`WorkspaceManager`**
- Main interface for workspace operations
- Manages workspace lifecycle and metadata
- Handles archiving and restoration

**Key Methods:**
- `get_current() -> Optional[WorkspaceInfo]`: Get current workspace info
- `has_current() -> bool`: Check if current workspace exists
- `list_workspaces() -> List[WorkspaceInfo]`: List all workspaces (current + archived)
- `find_workspace(name: str) -> Optional[WorkspaceInfo]`: Find workspace by name
- `get_suggestions(name: str, n: int = 3) -> List[str]`: Get fuzzy name suggestions
- `create_workspace(name: Optional[str] = None, archive_current: bool = False) -> WorkspaceInfo`: Create new workspace
- `archive_current(name: Optional[str] = None) -> Path`: Archive current workspace
- `switch_workspace(name: str, save_current: bool = True) -> WorkspaceInfo`: Switch to different workspace
- `update_current_task(task: str)`: Update last task description
- `delete_archive(name: str) -> bool`: Delete archived workspace
- `get_archive_size() -> str`: Get total archive size (human-readable)

**Directory Structure:**
```
NEXUS/
├── workspace/              # Current active workspace
│   ├── agents/
│   ├── logs/
│   ├── .nexus/
│   │   ├── metadata.json   # Workspace metadata
│   │   └── blackboard.json
│   └── sessions/
└── .workspace_archives/    # Archived workspaces
    ├── project-a_20251217_103045/
    ├── project-b_20251216_154523/
    └── experiment-1_20251215_092314/
```

### WorkspaceInfo

**`WorkspaceInfo`** (dataclass)
- Contains workspace metadata and metrics
- Persisted to `workspace/.nexus/metadata.json`

**Fields:**
- `name: str` - Workspace name
- `path: Path` - Full path to workspace directory
- `created_at: datetime` - Creation timestamp
- `last_used: datetime` - Last access timestamp
- `last_task: str` - Description of last task performed
- `is_current: bool` - Whether this is the active workspace
- `metrics: WorkspaceMetrics` - Usage metrics

**Methods:**
- `get_relative_time() -> str`: Human-readable relative time ("2 hours ago")
- `get_size_human() -> str`: Human-readable size ("12.3 MB")
- `update_files_count() -> int`: Count files in workspace
- `to_dict() -> dict`: Serialize to dict
- `from_dict(data: dict) -> WorkspaceInfo`: Deserialize from dict
- `save_metadata()`: Save metadata to JSON file
- `load_from_path(path: Path) -> Optional[WorkspaceInfo]`: Load from directory

### WorkspaceMetrics

**`WorkspaceMetrics`** (dataclass)
- Tracks workspace usage statistics

**Fields:**
- `iterations: int` - Number of FSM iterations
- `files_count: int` - Number of files in workspace
- `total_tokens: int` - Total tokens consumed
- `tasks_completed: int` - Number of tasks completed

**Methods:**
- `to_dict() -> dict`: Serialize
- `from_dict(data: dict) -> WorkspaceMetrics`: Deserialize

### Exceptions

**`WorkspaceError`** - Base exception for workspace errors

**`WorkspaceNotFoundError`** - Workspace not found by name

**`WorkspaceExistsError`** - Workspace already exists with that name

**`WorkspaceCorruptedError`** - Workspace metadata corrupted or invalid

## Dependencies & Integration

### Internal Dependencies
- `pathlib` - Path handling
- `json` - Metadata serialization
- `datetime` - Timestamps
- `shutil` - Directory operations
- `difflib` - Fuzzy name matching for suggestions

### Integration Points
- **REPL**: Commands like `/workspace`, `/archive`, `/switch`
- **Orchestrators**: Update workspace metrics after task completion
- **Telemetry**: Workspace-scoped telemetry files
- **Session**: Isolated session data per workspace

### Usage Examples

```python
from core.workspace import WorkspaceManager
from pathlib import Path

# Initialize manager
manager = WorkspaceManager(nexus_root=Path("/path/to/NEXUS"))

# Check current workspace
current = manager.get_current()
if current:
    print(f"Current: {current.name}")
    print(f"Created: {current.get_relative_time()}")
    print(f"Size: {current.get_size_human()}")
    print(f"Files: {current.metrics.files_count}")

# List all workspaces
workspaces = manager.list_workspaces()
for ws in workspaces:
    marker = "[CURRENT]" if ws.is_current else "[ARCHIVE]"
    print(f"{marker} {ws.name} - {ws.last_task}")

# Create new workspace
new_ws = manager.create_workspace(
    name="my-project",
    archive_current=True  # Archive current before creating new
)
print(f"Created workspace: {new_ws.name}")

# Switch to existing workspace
try:
    ws = manager.switch_workspace("old-project", save_current=True)
    print(f"Switched to: {ws.name}")
except WorkspaceNotFoundError as e:
    # Get suggestions
    suggestions = manager.get_suggestions("old-projekt")
    print(f"Not found. Did you mean: {', '.join(suggestions)}?")

# Update task description
manager.update_current_task("Implementing authentication module")

# Archive current workspace
archive_path = manager.archive_current(name="project-backup")
print(f"Archived to: {archive_path}")

# Delete old archive
manager.delete_archive("old-experiment")

# Get archive size
size = manager.get_archive_size()
print(f"Total archives: {size}")
```

## Design Notes

### Workspace Isolation

- **Independent State**: Each workspace has its own agents, logs, sessions, telemetry
- **Metadata Persistence**: Workspace info saved to `.nexus/metadata.json`
- **Archive Format**: Timestamped directories in `.workspace_archives/`
- **Seamless Switching**: Switch command archives current and restores target

### Name Management

- **Auto-Generation**: Creates timestamped names if not provided
- **Sanitization**: Removes invalid characters from names
- **Fuzzy Matching**: `get_suggestions()` uses difflib for typo tolerance
- **Uniqueness**: Prevents duplicate workspace names

### Metrics Tracking

- **Automatic Updates**: Orchestrators update metrics after each task
- **Persistent**: Metrics saved to metadata.json
- **Human-Readable**: Methods for relative time, file counts, sizes

### Archive Management

- **Timestamp Suffix**: Archives named `<name>_YYYYMMDD_HHMMSS`
- **Preserve History**: Archives never overwritten
- **Selective Deletion**: Can delete individual archives
- **Size Monitoring**: Track total archive size for cleanup decisions

### Use Cases

1. **Project Organization**: Separate workspace per project
2. **Experiment Isolation**: Create workspace for experiments, archive when done
3. **Context Switching**: Switch between multiple ongoing tasks
4. **Historical Snapshots**: Archive before major refactoring
5. **Clean Slate**: Create fresh workspace without losing previous work
