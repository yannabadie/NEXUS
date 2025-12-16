# PLAN D'ACTION - FIX CRITIQUES NEXUS V9 CYBORG

## 🚨 URGENCE CRITIQUE - À FAIRE IMMÉDIATEMENT

### JOUR 1-2: SÉCURITÉ (BLOCANT)

#### 1. Fix Path Traversal dans Evolution Mode
**Fichier cible** : `core/execution/tool_manager.py`

**Code actuel problématique** :
```python
def _is_evolution_safe_read(self, path: Path) -> bool:
    try:
        relative = path.relative_to(self.parent_path)
        path_str = str(relative).replace("\\", "/")
        allowed_prefixes = ["core/", "prompts/", "benchmarks/"]
        # VULNÉRABILITÉ: Validation par chaîne
        if any(path_str.startswith(prefix) for prefix in allowed_prefixes):
            return True
    except ValueError:
        return False
```

**Fix sécurisé** :
```python
def _is_evolution_safe_read(self, path: Path) -> bool:
    """V9.6 SECURITY: Use proper path containment, not string matching."""
    try:
        # Résoudre symlinks et chemins relatifs
        resolved = path.resolve()

        # Vérifier containment réel avec relative_to()
        allowed_dirs = [
            self.parent_path / "core",
            self.parent_path / "prompts",
            self.parent_path / "benchmarks"
        ]

        for allowed_dir in allowed_dirs:
            try:
                resolved.relative_to(allowed_dir)
                return True
            except ValueError:
                continue

        return False
    except Exception:
        return False
```

**Appliquer le même fix à** :
- `_is_evolution_safe_list()`
- `_is_evolution_safe_write()`

#### 2. Renforcer Protection des Fichiers Sacrés
**Fichier cible** : `core/security/path_guardian.py`

**Fix** :
```python
def __init__(self, ...):
    # Patterns plus stricts avec regex complet
    self.sacred_patterns = [
        r'^\.env',           # Commence par .env
        r'\.key$',           # Termine par .key
        r'\.pem$',           # Termine par .pem
        r'credentials?\.',   # credentials.json, credential.txt, etc.
        r'KERNEL\.py$',      # Exact match KERNEL.py
        r'MISSION\.md$',     # Exact match MISSION.md
    ]
```

### JOUR 3-4: PERFORMANCE ASYNC (BLOCANT)

#### 3. Supprimer ParallelExecutor Sync Blocking
**Fichier cible** : `core/swarm/executors/parallel_executor.py`

**Code à supprimer** :
```python
def execute(self, context: ExecutionContext) -> ExecutionResult:
    """DEPRECATED - Remove this method entirely."""
    import warnings
    warnings.warn(
        "ParallelExecutor.execute() is deprecated. "
        "Use `await executor.execute_async(context)` in async code.",
        DeprecationWarning,
        stacklevel=2
    )

    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        future = asyncio.run_coroutine_threadsafe(self.execute_async(context), loop)
        return future.result(timeout=300)  # REMOVE THIS BLOCKING CALL
    except RuntimeError:
        return asyncio.run(self.execute_async(context))  # REMOVE THIS TOO
```

**Migration requise** : Tous les appels à `executor.execute()` doivent devenir `await executor.execute_async()`.

#### 4. Fix Context Thread-Safety
**Fichier cible** : `core/orchestration/orchestration_v7.py`

**Fix** :
```python
def _sync_context_agent(self, context: TaskExecutionContext):
    """V9.3: Thread-safe context replacement."""
    # OLD: self._task_context = context  # Race condition!
    # NEW: Atomic replacement with immutable copy
    self._task_context = context.copy()  # Assuming TaskExecutionContext has copy()
```

### JOUR 5-7: TESTS ET VALIDATION

#### 5. Tests Sécurité Path Traversal
**Nouveau fichier** : `tests/security/test_path_traversal.py`

```python
import pytest
from pathlib import Path
from core.execution.tool_manager import ToolManager

class TestPathTraversal:
    def test_evolution_path_traversal_prevention(self):
        """Test that ../../../etc/passwd is blocked."""
        workspace = Path("/tmp/nexus/workspace")
        tool_manager = ToolManager(workspace)

        # These should all be BLOCKED
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "core/../../../root/.ssh/id_rsa",
            "prompts/../secrets.txt"
        ]

        for path in malicious_paths:
            assert not tool_manager._is_evolution_safe_read(Path(path))
            assert not tool_manager._is_evolution_safe_write(Path(path))
```

#### 6. Tests Async Performance
**Nouveau fichier** : `tests/performance/test_async_performance.py`

```python
import asyncio
import time
from core.swarm.executors.parallel_executor import ParallelExecutor

class TestAsyncPerformance:
    async def test_no_event_loop_blocking(self):
        """Ensure execute_async() doesn't block event loop."""
        executor = ParallelExecutor()

        # Start timing
        start_time = time.time()

        # This should complete without blocking
        task = asyncio.create_task(executor.execute_async(mock_context))

        # Event loop should remain responsive
        await asyncio.sleep(0.1)  # Should not be blocked

        result = await task
        elapsed = time.time() - start_time

        assert elapsed < 5.0  # Should be fast
        assert result.status == "completed"
```

### JOUR 8-10: MIGRATION ARCHITECTURALE

#### 7. Unified Async Interface
**Fichier cible** : `core/interface/repl.py`

**Refactor** :
```python
class NexusREPL:
    def __init__(self, ...):
        # Single orchestrator instance
        self.orchestrator = UnifiedOrchestrator(...)

    async def process_input_async(self, user_input: str):
        """Single async entry point."""
        return await self.orchestrator.process_turn_async(user_input)

    def process_input_sync(self, user_input: str):
        """Sync wrapper for backward compatibility."""
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            return loop.run_until_complete(self.process_input_async(user_input))
        except RuntimeError:
            return asyncio.run(self.process_input_async(user_input))
```

#### 8. Service Layer Extraction
**Nouvelle structure** :
```
core/orchestration/
├── orchestrator.py          # 200 lines - coordination only
├── services/
│   ├── task_dispatcher.py   # Task routing logic
│   ├── state_manager.py     # FSM state management
│   ├── agent_coordinator.py # Agent invocation logic
│   └── evolution_orchestrator.py # Evolution management
└── handlers/                 # FSM state handlers
    ├── idle_handler.py
    ├── brainstorming_handler.py
    └── ...
```

### JOUR 11-14: MONITORING ET OBSERVABILITÉ

#### 9. Security Monitoring
**Nouveau fichier** : `core/security/monitor.py`

```python
class SecurityMonitor:
    def __init__(self):
        self.violations = []

    def log_violation(self, violation_type: str, details: dict):
        """Log security violation with structured data."""
        violation = {
            "timestamp": datetime.utcnow(),
            "type": violation_type,
            "details": details,
            "severity": self._calculate_severity(violation_type)
        }
        self.violations.append(violation)

        # Alert if critical
        if violation["severity"] == "CRITICAL":
            self._alert_security_team(violation)
```

#### 10. Performance Metrics
**Nouveau fichier** : `core/telemetry/performance_monitor.py`

```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "event_loop_blocking": [],
            "async_task_duration": [],
            "memory_usage": []
        }

    def record_event_loop_blocking(self, duration: float):
        """Record event loop blocking incidents."""
        self.metrics["event_loop_blocking"].append({
            "duration": duration,
            "timestamp": time.time()
        })

        if duration > 1.0:  # Alert on >1s blocking
            self._alert_performance_issue(f"Event loop blocked for {duration}s")
```

### VALIDATION FINALE

#### Checklist Déploiement Production
- [ ] Tous les path traversal tests passent
- [ ] Aucune méthode sync blocking remaining
- [ ] Context thread-safe validé
- [ ] Security audit passé (outil externe)
- [ ] Performance benchmarks > 95% async
- [ ] Monitoring alerts configurés
- [ ] Rollback plan documenté

---

## 📈 MÉTRIQUES DE VALIDATION

### Sécurité
```bash
# Run security tests
pytest tests/security/ -v --tb=short

# Expected: 100% pass, 0 vulnerabilities
```

### Performance
```bash
# Run async performance tests
pytest tests/performance/ -v --tb=short

# Expected: <500ms latency, 0 blocking
```

### Architecture
```bash
# Code complexity check
radon cc core/orchestration/ --min B

# Expected: All functions < 20 complexity
```

---

## 🎯 PROCHAINES ÉTAPES POST-FIX

1. **Phase 2** : Architecture monolithique → microservices
2. **Phase 3** : Scalabilité horizontale
3. **Phase 4** : Intelligence émergente

**Priorité absolue** : Ne déployer en production qu'après validation complète de cette Phase 1.</content>
<parameter name="filePath">c:\Code\NEXUS\NEXUS-N7A\CRITICAL_FIXES_ACTION_PLAN.md