# Plan: Gemini Persistent Driver via pywinpty

**Date**: 2025-11-28
**Objectif**: Réduire la latence Gemini de ~15-20s à ~2-3s par tour
**Méthode**: Utiliser pywinpty pour maintenir un process Gemini interactif persistant

---

## 1. Architecture

### 1.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                    GeminiDriverV7                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                   Mode Selection                             ││
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      ││
│  │  │  PTY Mode   │ -> │  Resume     │ -> │  Subprocess │      ││
│  │  │  (fastest)  │    │  (medium)   │    │  (slowest)  │      ││
│  │  └─────────────┘    └─────────────┘    └─────────────┘      ││
│  │       ↓ fail             ↓ fail              ↓               ││
│  │       └─────────────────>└──────────────────>│               ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 PersistentGeminiPTY                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  winpty.PtyProcess                                           ││
│  │  - spawn() -> gemini -m model --prompt-interactive "init"   ││
│  │  - write() -> send prompts                                   ││
│  │  - read()  -> receive responses (with ANSI parsing)          ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  OutputParser                                                ││
│  │  - strip_ansi_codes()                                        ││
│  │  - detect_response_end() -> prompt marker detection          ││
│  │  - extract_json() -> JSON extraction from mixed output       ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  HealthMonitor                                               ││
│  │  - is_alive() -> process check                               ││
│  │  - watchdog() -> timeout detection                           ││
│  │  - restart() -> automatic recovery                           ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Fichiers à créer/modifier

| Fichier | Action | Description |
|---------|--------|-------------|
| `core/drivers/gemini_pty.py` | CRÉER | Nouveau driver PTY |
| `core/drivers/gemini_driver_v7.py` | MODIFIER | Intégrer le mode PTY |
| `core/config.py` | MODIFIER | Ajouter config PTY |
| `tests/test_gemini_pty.py` | CRÉER | Tests unitaires |

---

## 2. Spécifications Techniques

### 2.1 Class PersistentGeminiPTY

```python
class PersistentGeminiPTY:
    """
    Gemini CLI persistent process via Windows PTY.

    Lifecycle:
    1. start() -> spawn gemini with --prompt-interactive
    2. send_prompt(prompt) -> write to PTY, read response
    3. close() -> terminate gracefully

    Recovery:
    - Auto-restart on failure (max 3 retries)
    - Fallback to subprocess mode after exhaustion
    """

    # Configuration
    STARTUP_TIMEOUT = 30.0      # Max time to wait for Gemini startup
    RESPONSE_TIMEOUT = 300.0    # Max time for a response
    READ_CHUNK_SIZE = 4096      # Bytes per read
    PROMPT_MARKER = "❯"         # Gemini's prompt character (or detect dynamically)
    MAX_RESTARTS = 3            # Before giving up on PTY mode

    def __init__(self, config, workspace_path, model):
        ...

    def start(self) -> bool:
        """Start the persistent PTY process."""
        ...

    def send_prompt(self, prompt: str, timeout: float = None) -> str:
        """Send prompt and wait for complete response."""
        ...

    def is_alive(self) -> bool:
        """Check if PTY process is running."""
        ...

    def restart(self) -> bool:
        """Restart the PTY process."""
        ...

    def close(self):
        """Gracefully terminate the PTY process."""
        ...
```

### 2.2 Détection de fin de réponse

Le défi principal: savoir quand Gemini a fini de répondre.

**Stratégies (à tester dans l'ordre):**

1. **Prompt Marker Detection**
   - Gemini affiche `❯` quand prêt pour le prochain input
   - Regex: `r'❯\s*$'` en fin de buffer

2. **Idle Timeout**
   - Si aucune nouvelle donnée pendant 2s après contenu, considérer terminé
   - Risque: couper une réponse longue

3. **JSON Structure Detection** (mode `-o json`)
   - Détecter `}` final du JSON
   - Parser le JSON pour validation

4. **Hybrid**: Prompt marker OU JSON complet OU idle timeout

### 2.3 Parsing ANSI

```python
def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences."""
    patterns = [
        r'\x1b\[[0-9;]*[a-zA-Z]',     # CSI sequences (colors, cursor)
        r'\x1b\][^\x07]*\x07',         # OSC sequences (title)
        r'\x1b[PX^_][^\x1b]*\x1b\\',   # DCS/PM/APC/SOS sequences
        r'\x1b.',                       # Other escape sequences
    ]
    result = text
    for pattern in patterns:
        result = re.sub(pattern, '', result)
    return result
```

### 2.4 Gestion des Tools

Gemini CLI peut exécuter des tools pendant une réponse:
- `read_file`, `grep`, `glob`, etc.
- Le spinner s'affiche pendant l'exécution
- La réponse peut être fragmentée

**Solution**: Accumuler tout jusqu'au prompt marker final.

---

## 3. Plan d'Implémentation

### Phase 1: Core PTY Driver (2h estimé)

**Étape 1.1**: Créer `gemini_pty.py` avec structure de base
- [ ] Class `PersistentGeminiPTY`
- [ ] Méthodes `start()`, `close()`, `is_alive()`
- [ ] Import conditionnel de `winpty` (Windows only)

**Étape 1.2**: Implémenter `start()`
- [ ] Construire la commande Gemini CLI
- [ ] Spawner via `winpty.PtyProcess.spawn()`
- [ ] Attendre le prompt initial (startup detection)

**Étape 1.3**: Implémenter `send_prompt()`
- [ ] Écrire le prompt via `pty.write()`
- [ ] Lire en boucle via `pty.read()`
- [ ] Détecter la fin de réponse
- [ ] Retourner le contenu nettoyé

### Phase 2: Parsing & Detection (1h estimé)

**Étape 2.1**: Parser ANSI
- [ ] Fonction `strip_ansi()`
- [ ] Tests avec vrais outputs Gemini

**Étape 2.2**: Détection fin de réponse
- [ ] Regex pour prompt marker
- [ ] Fallback idle timeout
- [ ] Mode JSON si `-o json`

**Étape 2.3**: Extraction JSON
- [ ] Trouver le JSON dans le output mixte
- [ ] Valider la structure NEXUS attendue

### Phase 3: Intégration Driver V7 (1h estimé)

**Étape 3.1**: Modifier `gemini_driver_v7.py`
- [ ] Ajouter import conditionnel `PersistentGeminiPTY`
- [ ] Nouvelle méthode `_invoke_pty()`
- [ ] Ordre de fallback: PTY -> Resume -> Subprocess

**Étape 3.2**: Configuration
- [ ] `config.gemini_pty_mode: bool`
- [ ] `config.gemini_pty_timeout: float`
- [ ] Variable d'env `GEMINI_PTY_MODE`

### Phase 4: Tests & Validation (1h estimé)

(Voir section 4)

### Phase 5: Documentation & Commit (30min estimé)

- [ ] Docstrings complètes
- [ ] Update `README.md`
- [ ] Commit avec message descriptif

---

## 4. Protocole de Tests

### 4.1 Tests Unitaires (`tests/test_gemini_pty.py`)

```python
class TestPersistentGeminiPTY:

    def test_01_import_winpty(self):
        """Verify winpty is available on Windows."""
        import platform
        if platform.system() == "Windows":
            import winpty
            assert hasattr(winpty, 'PtyProcess')

    def test_02_start_stop(self):
        """PTY can start and stop cleanly."""
        pty = PersistentGeminiPTY(config, workspace, "gemini-2.5-flash")
        assert pty.start() == True
        assert pty.is_alive() == True
        pty.close()
        assert pty.is_alive() == False

    def test_03_simple_prompt(self):
        """Send a simple prompt and get response."""
        pty = PersistentGeminiPTY(...)
        pty.start()
        response = pty.send_prompt("Say just OK")
        assert "OK" in response
        pty.close()

    def test_04_multi_turn(self):
        """Multiple prompts in same session."""
        pty = PersistentGeminiPTY(...)
        pty.start()
        r1 = pty.send_prompt("Remember the number 42")
        r2 = pty.send_prompt("What number did I tell you?")
        assert "42" in r2
        pty.close()

    def test_05_json_mode(self):
        """Test with -o json output format."""
        # Uses NEXUS-style JSON response
        ...

    def test_06_tool_execution(self):
        """Gemini uses a tool during response."""
        response = pty.send_prompt("List files in current directory using list_directory")
        assert "file:" in response or "dir:" in response

    def test_07_timeout_handling(self):
        """Proper timeout on long responses."""
        with pytest.raises(TimeoutError):
            pty.send_prompt("Complex task...", timeout=1.0)

    def test_08_restart_recovery(self):
        """Auto-restart after process death."""
        pty.start()
        pty.process.terminate()  # Force kill
        response = pty.send_prompt("Hello")  # Should auto-restart
        assert response is not None

    def test_09_ansi_stripping(self):
        """ANSI codes properly removed."""
        raw = "\x1b[38;2;80;146;225mHello\x1b[0m"
        assert strip_ansi(raw) == "Hello"

    def test_10_concurrent_safety(self):
        """Thread safety of send_prompt."""
        # Verify lock prevents race conditions
        ...
```

### 4.2 Tests d'Intégration

```python
class TestGeminiDriverPTYIntegration:

    def test_driver_uses_pty_mode(self):
        """Driver selects PTY mode when available."""
        config.gemini_pty_mode = True
        driver = GeminiDriverV7(config, workspace)
        # Check internal state
        assert driver._pty_process is not None

    def test_driver_fallback_to_subprocess(self):
        """Driver falls back when PTY fails."""
        config.gemini_pty_mode = True
        # Simulate PTY failure...
        response = driver.invoke(context)
        assert response is not None  # Got response via subprocess

    def test_evolution_brainstorming_pty(self):
        """Full evolution cycle uses PTY mode."""
        # Run /evolve and verify reduced latency
        ...
```

### 4.3 Tests Manuels

| Test | Commande | Attendu |
|------|----------|---------|
| Démarrage PTY | `python -c "from gemini_pty import *; p=PersistentGeminiPTY(...); p.start(); print(p.is_alive())"` | `True` |
| Prompt simple | `p.send_prompt("Say OK")` | Contient "OK" |
| Multi-turn | 2 prompts consécutifs | Contexte préservé |
| Latence | Timer autour de `send_prompt()` | <5s après 1er appel |
| Kill/Restart | `p.process.terminate(); p.send_prompt("Hi")` | Auto-restart, réponse reçue |
| NEXUS complet | `python nexus7.py` puis une question | Réponse en <5s |
| Evolution | `/evolve` | Brainstorming en temps réel |

### 4.4 Tests de Performance

```python
def test_latency_comparison():
    """Compare latency between modes."""

    # Subprocess mode
    t1 = time.time()
    subprocess_response = driver_subprocess.invoke(context)
    subprocess_latency = time.time() - t1

    # PTY mode (warm - after first call)
    pty.send_prompt("warmup")  # First call has startup cost
    t2 = time.time()
    pty_response = pty.send_prompt(context)
    pty_latency = time.time() - t2

    print(f"Subprocess: {subprocess_latency:.1f}s")
    print(f"PTY (warm): {pty_latency:.1f}s")

    # PTY should be at least 3x faster
    assert pty_latency < subprocess_latency / 3
```

---

## 5. Edge Cases & Gestion d'Erreurs

### 5.1 Cas limites

| Cas | Comportement | Solution |
|-----|--------------|----------|
| Gemini CLI pas installé | `start()` échoue | Fallback subprocess avec `-p` |
| pywinpty pas installé | Import error | Fallback automatique |
| Process crash mid-response | `read()` retourne vide | Restart + retry |
| Réponse très longue (>1MB) | Buffer overflow | Chunked reading avec limite |
| Prompt contient caractères spéciaux | Escape issues | Proper escaping |
| Unicode dans réponse | Encoding error | UTF-8 avec errors='replace' |
| Gemini rate limit | Error dans output | Parse error, retry ou fallback |
| Network timeout Gemini | Process hang | Watchdog timeout |

### 5.2 Mécanisme de Fallback

```
PTY Mode
   │
   ├─ Success → Use PTY
   │
   └─ Failure (N retries)
         │
         ├─ --resume latest Mode
         │      │
         │      ├─ Success → Use Resume
         │      │
         │      └─ Failure
         │            │
         │            └─ Subprocess Mode (always works)
         │
         └─ Immediate fallback si PTY impossible
```

### 5.3 Logging

```python
# Niveaux de log
DEBUG: "PTY: Starting process..."
DEBUG: "PTY: Received 4096 bytes"
INFO:  "PTY: Startup complete in 2.3s"
WARNING: "PTY: Restart attempt 1/3"
ERROR: "PTY: Failed after 3 retries, falling back to subprocess"
```

---

## 6. Configuration

### 6.1 Variables d'Environnement

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_PTY_MODE` | `True` | Activer le mode PTY |
| `GEMINI_PTY_TIMEOUT` | `300` | Timeout réponse (secondes) |
| `GEMINI_PTY_STARTUP_TIMEOUT` | `30` | Timeout démarrage |
| `GEMINI_PTY_MAX_RESTARTS` | `3` | Max tentatives restart |

### 6.2 Config Python

```python
# config.py
self.gemini_pty_mode: bool = os.getenv("GEMINI_PTY_MODE", "True").lower() == "true"
self.gemini_pty_timeout: float = float(os.getenv("GEMINI_PTY_TIMEOUT", "300"))
self.gemini_pty_startup_timeout: float = float(os.getenv("GEMINI_PTY_STARTUP_TIMEOUT", "30"))
self.gemini_pty_max_restarts: int = int(os.getenv("GEMINI_PTY_MAX_RESTARTS", "3"))
```

---

## 7. Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| pywinpty incompatible Windows version | Faible | Haut | Check version, fallback |
| Gemini CLI change output format | Moyen | Haut | Version check, flexible parsing |
| Memory leak process persistant | Faible | Moyen | Periodic restart, monitoring |
| Deadlock PTY read/write | Faible | Haut | Timeouts, non-blocking I/O |
| Prompt marker change | Moyen | Moyen | Multiple detection strategies |

---

## 8. Critères de Succès

### Must Have
- [ ] PTY démarre et reste actif
- [ ] Multi-turn conversation fonctionne
- [ ] Latence <5s après warmup (vs ~15-20s avant)
- [ ] Fallback automatique si PTY échoue
- [ ] Pas de régression sur mode subprocess

### Should Have
- [ ] Restart automatique transparent
- [ ] JSON parsing fiable
- [ ] Tool execution supportée
- [ ] Logging informatif

### Nice to Have
- [ ] Metrics de performance
- [ ] Health check endpoint
- [ ] Session persistence cross-restart

---

## 9. Ordre d'Exécution

1. **Test préliminaire**: Valider que pywinpty fonctionne avec Gemini CLI
2. **Phase 1**: Core PTY driver
3. **Test Phase 1**: Tests unitaires 01-04
4. **Phase 2**: Parsing & detection
5. **Test Phase 2**: Tests 05-09
6. **Phase 3**: Intégration
7. **Test Phase 3**: Tests intégration
8. **Phase 4**: Tests manuels complets
9. **Phase 5**: Doc & commit

---

## 10. Commande pour Démarrer

```bash
# Après validation du plan
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V7_CHRYSALIS
python -c "
from core.drivers.gemini_pty import PersistentGeminiPTY
from core.config import load_config
from pathlib import Path

config = load_config()
workspace = Path('workspace')
pty = PersistentGeminiPTY(config, workspace, 'gemini-2.5-flash')
print('Starting...')
if pty.start():
    print('OK! Sending test prompt...')
    response = pty.send_prompt('Say OK')
    print('Response:', response[:200])
    pty.close()
else:
    print('Failed to start')
"
```
