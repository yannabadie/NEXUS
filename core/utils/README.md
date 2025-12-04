# Module: Utils - NEXUS V7.5 Utilities

**Version**: 7.5 (HIVE MIND)
**Last Updated**: 2025-12-04

---

## Role Architectural

Utilitaires partagés pour NEXUS V7.5, incluant extraction JSON, vérification d'artefacts, et persistance atomique.

---

## Alignement ROADMAP V7.5+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 6** | `json_extractor.py` - Extraction JSON robuste (COMPLETE) |
| **Phase 7: Session Isolation** | `atomic_store.py` - Persistance atomique thread-safe (COMPLETE) |

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

### 3. Artifact Verifier (`artifact_verifier.py`)

Ensures downloaded or generated files meet integrity checks (checksums, size limits).

```python
from core.utils import ArtifactVerifier

verifier = ArtifactVerifier()
is_valid = verifier.verify(artifact_path)
```

---

## Files

| File | Purpose | Key Exports |
|------|---------|-------------|
| `atomic_store.py` | Atomic JSON persistence | `AtomicJsonStore`, `get_store` |
| `json_extractor.py` | Robust JSON parsing | `extract_json`, `extract_json_safe` |
| `artifact_verifier.py` | File integrity | `ArtifactVerifier` |
| `__init__.py` | Module exports | All public APIs |

---

## Tests

```bash
# AtomicJsonStore tests (27 tests)
pytest tests/test_atomic_store.py -v

# Concurrency tests only
pytest tests/test_atomic_store.py::TestAtomicJsonStoreConcurrency -v
```

---

## Dependencies

- Standard library only: `json`, `os`, `pathlib`, `threading`, `tempfile`

---

## See Also

- [Synapse Module](../synapse/README.md) - Uses AtomicJsonStore for Blackboard
- [Swarm Module](../swarm/README.md) - Benefits from thread-safety in PARALLEL mode
