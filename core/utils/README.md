# Module: Utils - NEXUS V8.4.x Utilities

**Version**: 8.4.4 (TRUE HIVE MIND)
**Last Updated**: 2025-12-10

---

## Role Architectural

Utilitaires partagés pour NEXUS V8.4.x, incluant extraction JSON, parsing de streams, vérification d'artefacts, persistance atomique, et **sérialisation NEXUS** (V8.4.4).

---

## Alignement ROADMAP V7.5+ / V8.4.x

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 6** | `json_extractor.py` - Extraction JSON robuste (COMPLETE) |
| **Phase 7: Session Isolation** | `atomic_store.py` - Persistance atomique thread-safe (COMPLETE) |
| **Phase 15: Response Streaming** | `stream_parser.py` - Parsing JSONL pour streaming (COMPLETE) |
| **V8.4.4: P0 Blind Spot** | `serialization.py` - NexusJSONEncoder (COMPLETE) |

---

## Components

### 1. AtomicJsonStore (`atomic_store.py`) - NEW Phase 7

**Thread-safe atomic JSON persistence** using Write-Replace pattern.

**Problem Solved**: En mode Swarm PARALLEL, plusieurs threads peuvent écrire simultanément. Sans protection: race conditions, fichiers corrompus.

**Pattern Write-Replace**:
1. Écrire dans fichier temporaire (.tmp)
2. Forcer sync disque (fsync)
3. Renommer atomiquement vers cible (os.replace)

```python
from core.utils import AtomicJsonStore
from pathlib import Path

store = AtomicJsonStore(Path("workspace/.nexus/blackboard.json"))

# Read (returns {} if file doesn't exist)
data = store.load()
data = store.load_safe()  # Never raises, returns {} on error

# Atomic write
store.save({"key": "value", "counter": 42})

# Atomic update (load + modify + save)
store.update({"new_key": "value"})
```

**Guarantees**:
- Atomicity: All-or-nothing writes
- Thread-safety: RLock for concurrent access
- Persistence: fsync forces disk write
- Recovery: Previous file intact on error

### 2. JSON Extractor (`json_extractor.py`)

**Critical for V7.5**. Provides robust parsing of LLM outputs.

**Strategies:**
1. `START_JSON` ... `END_JSON` markers (Highest priority).
2. Markdown code blocks (```json).
3. Brute-force brace matching (`{ ... }`).

```python
from core.utils import extract_json, extract_json_safe

raw_llm_output = "Here is the data: START_JSON {'key': 'value'} END_JSON"
data, error = extract_json_safe(raw_llm_output)

if data:
    print(data['key'])  # "value"
```

### 3. Stream Parser (`stream_parser.py`) - NEW Phase 15

**Unified JSONL parser** for Gemini and Claude CLI stream-json outputs.

**Problem Solved**: Les deux CLI ont des formats stream-json différents. Ce parser unifie l'extraction de texte streaming.

```python
from core.utils import parse_stream_chunk, is_result_message, extract_stats

# Parse JSONL line from either CLI
text_chunk, metadata = parse_stream_chunk(line, "gemini")  # or "claude"

if text_chunk:
    # Text delta - display immediately
    print(text_chunk, end="", flush=True)

if is_result_message(metadata, "gemini"):
    stats = extract_stats(metadata, "gemini")
    print(f"\n[Tokens: {stats.get('total_tokens')}]")
```

**Formats supportés**:
- **Gemini**: `{"type":"message", "role":"assistant", "content":"...", "delta":true}`
- **Claude**: `{"type":"stream_event", "event":{"type":"content_block_delta", "delta":{"type":"text_delta", "text":"..."}}}`

**See also**: `docs/STREAM_FORMAT_ANALYSIS.md`

### 4. Artifact Verifier (`artifact_verifier.py`)

Ensures downloaded or generated files meet integrity checks (checksums, size limits).

```python
from core.utils import ArtifactVerifier

verifier = ArtifactVerifier()
is_valid = verifier.verify(artifact_path)
```

### 5. NEXUS Serialization (`serialization.py`) - NEW V8.4.4

**Problem Solved**: Standard `json.dumps()` fails on datetime, Enum, UUID, Path, dataclass, etc. SagaManager checkpoints need to serialize complex NEXUS types.

**NexusJSONEncoder** handles:
- `datetime` → ISO format string
- `Enum` → `.value`
- `UUID` → `str(uuid)`
- `Path` → `str(path)`
- `bytes` → base64 encoded
- `set` → list
- `dataclass` → via `asdict()`
- Pydantic models → via `.model_dump()`
- Objects with `to_dict()` method

```python
from core.utils import nexus_dumps, nexus_loads, NexusJSONEncoder
from datetime import datetime
from enum import Enum
from uuid import uuid4

# Serialize complex types
data = {
    "timestamp": datetime.now(),
    "state": HiveMindState.HIVE_GATING,
    "session_id": uuid4(),
    "config_path": Path("/workspace/.nexus")
}

json_str = nexus_dumps(data, indent=2)
# {"timestamp": "2024-12-10T15:30:00", "state": "hive_gating", "session_id": "abc-123", ...}

# Deserialize with datetime parsing
restored = nexus_loads(json_str)
print(type(restored["timestamp"]))  # <class 'datetime.datetime'>
```

**Convenience Functions**:
- `nexus_dumps(obj)` - Serialize with NexusJSONEncoder
- `nexus_loads(json_str)` - Deserialize with ISO date parsing
- `serialize_for_checkpoint(obj)` - Prepare object for SagaManager checkpoint

---

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `atomic_store.py` | Atomic JSON persistence | `AtomicJsonStore`, `get_store` |
| `json_extractor.py` | Robust JSON parsing | `extract_json`, `extract_json_safe` |
| `stream_parser.py` | JSONL stream parsing | `parse_stream_chunk`, `is_result_message`, `extract_stats` |
| `serialization.py` | **V8.4.4** NEXUS JSON encoding | `NexusJSONEncoder`, `nexus_dumps`, `nexus_loads` |
| `artifact_verifier.py` | File integrity | `ArtifactVerifier` |
| `__init__.py` | Module exports | All public APIs |

---

## Tests

```bash
# AtomicJsonStore tests (27 tests)
pytest tests/test_atomic_store.py -v

# Concurrency tests only
pytest tests/test_atomic_store.py::TestAtomicJsonStoreConcurrency -v

# Stream Parser tests (23 tests)
pytest tests/test_stream_parser.py -v

# Gemini format tests
pytest tests/test_stream_parser.py::TestGeminiStreamParser -v

# Claude format tests
pytest tests/test_stream_parser.py::TestClaudeStreamParser -v
```

---

## Dependencies

- Standard library only: `json`, `os`, `pathlib`, `threading`, `tempfile`

---

## See Also

- [Synapse Module](../synapse/README.md) - Uses AtomicJsonStore for Blackboard
- [Swarm Module](../swarm/README.md) - Benefits from thread-safety in PARALLEL mode
