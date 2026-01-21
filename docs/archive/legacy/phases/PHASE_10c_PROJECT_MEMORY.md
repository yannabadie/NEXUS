# Phase 10c: Project Memory RAG

**Version:** V7.8 HIVE MIND
**Status:** COMPLETED
**Date:** 2025-12-05

---

## Overview

Phase 10c implements a **Project Memory RAG** (Retrieval-Augmented Generation) system that indexes project files and retrieves relevant knowledge during agent execution.

### Key Features

- **TF-IDF Weighted Jaccard Similarity** - Zero-dependency scoring algorithm
- **Smart Chunking** - Language-aware chunking strategies
- **Persistent Storage** - Survives workspace changes
- **Automatic Context Injection** - For MODERATE+ complexity tasks

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ProjectMemory RAG                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  NEXUS_ROOT/                                                    │
│  ├── .nexus/                                                    │
│  │   └── project_knowledge.json  ← Persistent storage           │
│  ├── core/                                                      │
│  │   └── memory/                                                │
│  │       └── project_memory.py   ← RAG implementation           │
│  └── workspace/                  ← Session data (separate)      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Indexing Pipeline:                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  File    │ -> │  Chunk   │ -> │  Terms   │ -> │  Store   │  │
│  │  Read    │    │  Split   │    │  Extract │    │  JSON    │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
│  Retrieval Pipeline:                                            │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Query   │ -> │  Terms   │ -> │  Score   │ -> │  Return  │  │
│  │  Input   │    │  Extract │    │  TF-IDF  │    │  Top K   │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Chunking Strategies

| File Type | Strategy | Description |
|-----------|----------|-------------|
| `.py` | Function/Class | Split on `def`, `class`, `async def` |
| `.md` | Section | Split on headers (`#`, `##`, etc.) |
| Other | Lines | 50 lines with 10-line overlap |

### Chunk Configuration

```python
MAX_CHUNKS = 5000       # Global limit
MAX_CHUNK_SIZE = 2000   # Characters per chunk
MIN_CHUNK_SIZE = 50     # Minimum to index
LINES_PER_CHUNK = 50    # For line-based chunking
LINES_OVERLAP = 10      # Overlap between chunks
```

---

## Scoring Algorithm

**TF-IDF Weighted Jaccard Similarity:**

```
Score = Σ(IDF[term] for term ∈ query ∩ chunk) / Σ(IDF[term] for term ∈ query)
```

Where:
- `IDF(term) = log(N / (1 + df(term)))`
- `N` = Total number of chunks
- `df(term)` = Number of chunks containing term

### Term Extraction

- Lowercase, alphanumeric only
- Filter words < 3 characters
- Remove common stopwords (the, is, def, class, etc.)

---

## Storage

### Location

```
NEXUS_ROOT/.nexus/project_knowledge.json
```

**NOT** in `workspace/` - this ensures memory persists across `/workspace new`.

### Format

```json
{
  "version": "1.0",
  "indexed_at": "2025-12-05T10:30:00",
  "indexed_files": ["core/sample.py", "docs/README.md"],
  "chunks": [
    {
      "file_path": "core/sample.py",
      "start_line": 1,
      "end_line": 25,
      "content": "class Calculator:\n    ...",
      "terms": ["calculator", "add", "multiply"],
      "chunk_type": "class",
      "name": "Calculator"
    }
  ],
  "idf": {
    "calculator": 2.3,
    "add": 1.8
  }
}
```

---

## Commands

### `/learn [path]`

Index a file or directory into project memory.

```
nexus7> /learn core/
🧠 Indexing into Project Memory
   Path: C:\Code\NEXUS\core
   ✓ Indexed directory → 127 chunks

   📊 Total: 15 files, 127 chunks
   💾 Saved to: .nexus/project_knowledge.json
```

**Default:** If no path specified, indexes `core/`.

### `/forget [path]`

Remove a file or directory from the index.

```
nexus7> /forget core/sample.py
🧠 Removed from Project Memory
   Path: core/sample.py
   ✓ Removed 5 chunks
```

### `/memory-status`

Display current memory statistics.

```
nexus7> /memory-status
╔══════════════════════════════════════════════════════════════╗
║                   🧠 PROJECT MEMORY STATUS                   ║
╚══════════════════════════════════════════════════════════════╝

  📁 Indexed Files:    15
  📦 Total Chunks:     127
  🔤 Unique Terms:     843
  💾 Storage:          .nexus/project_knowledge.json

  📋 Files in memory:
     • core/orchestration_v7.py
     • core/swarm/hybrid_swarm_engine.py
     • core/memory/project_memory.py
     ...
```

---

## Context Injection

For tasks with **MODERATE** complexity or higher, relevant knowledge is automatically injected into the agent context.

### Flow

1. Task analyzed → Complexity = MODERATE+
2. `ContextBuilder._get_project_knowledge()` called
3. Query = Current objective
4. Top 3 chunks retrieved (min_score=0.05)
5. Formatted and injected into context

### Example Injected Context

```markdown
## RELEVANT PROJECT KNOWLEDGE

### core/swarm/hybrid_swarm_engine.py - class: HybridSwarmEngine (L45-120)
```python
class HybridSwarmEngine:
    """Main swarm orchestration engine..."""
    def execute_swarm(self, task):
        ...
```

### docs/ARCHITECTURE.md - section: Swarm Modes (L50-75)
```markdown
## Swarm Modes
NEXUS supports 6 collaboration modes...
```
```

---

## API Reference

### ProjectMemory

```python
from core.memory import ProjectMemory

# Initialize
memory = ProjectMemory(nexus_root=Path("/path/to/project"))

# Index files
memory.index_file(Path("core/sample.py"))
memory.index_file(Path("docs/README.md"), force=True)  # Re-index

# Index directory
chunks = memory.index_directory(
    Path("core/"),
    extensions=[".py", ".md"],
    recursive=True
)

# Retrieve relevant chunks
chunks = memory.retrieve(
    query="swarm execution mode",
    limit=5,
    min_score=0.05
)

# Format for context
context = memory.format_chunks_for_context(chunks, max_chars=3000)

# Forget files
memory.forget(Path("core/deprecated.py"))

# Clear all
memory.clear()

# Get stats
stats = memory.get_stats()
print(f"Files: {stats.total_files}, Chunks: {stats.total_chunks}")
```

### Chunk Dataclass

```python
@dataclass
class Chunk:
    file_path: str
    start_line: int
    end_line: int
    content: str
    terms: Set[str]
    chunk_type: str  # "function", "class", "section", "lines"
    name: Optional[str]  # Function/class/section name
```

### IndexStats Dataclass

```python
@dataclass
class IndexStats:
    total_files: int
    total_chunks: int
    total_terms: int
    indexed_at: str
    storage_path: str
```

---

## Files Modified

| File | Description |
|------|-------------|
| `core/memory/project_memory.py` | NEW - 685 lines - Main implementation |
| `core/memory/__init__.py` | Added exports |
| `core/orchestration_v7.py` | Init ProjectMemory at startup |
| `core/orchestration/context_builder.py` | Knowledge injection method |
| `core/interface/commands.py` | Memory command category |
| `core/interface/repl.py` | Command handlers |
| `tests/test_project_memory.py` | NEW - 50 unit tests |

---

## Tests

```bash
pytest tests/test_project_memory.py -v
```

**Coverage:**
- Initialization (3 tests)
- File indexing (8 tests)
- Directory indexing (4 tests)
- Python chunking (3 tests)
- Markdown chunking (2 tests)
- Retrieval (6 tests)
- Persistence (4 tests)
- Forget (4 tests)
- Context formatting (4 tests)
- Stats (2 tests)
- Clear (2 tests)
- Chunk dataclass (2 tests)
- Edge cases (4 tests)
- Workspace isolation (2 tests)

---

## Design Decisions

### 1. Storage at NEXUS_ROOT

**Decision:** Store at `.nexus/project_knowledge.json`, not in `workspace/`.

**Rationale:** Project knowledge is factual and should persist across workspace sessions. When user does `/workspace new`, they want a fresh session but not to lose indexed knowledge.

### 2. Zero Dependencies

**Decision:** Use TF-IDF weighted Jaccard instead of vector embeddings.

**Rationale:**
- No API calls required
- No external libraries (numpy, faiss, etc.)
- Fast and lightweight
- Good enough for code retrieval

### 3. Complexity-Gated Injection

**Decision:** Only inject for MODERATE+ complexity tasks.

**Rationale:**
- TRIVIAL/SIMPLE tasks don't need extra context
- Reduces token usage
- Keeps simple responses fast

### 4. Shared Across Agents

**Decision:** All agents (Gemini, Claude, spawned) share the same memory.

**Rationale:** Factual project knowledge is universal - all agents should have access to the same indexed codebase.

---

## Future Improvements

- [ ] Incremental re-indexing (detect file changes)
- [ ] Embedding-based retrieval (optional, with API)
- [ ] Code symbol extraction (AST-based for Python)
- [ ] Cross-file reference tracking
- [ ] Memory pruning (remove stale entries)
