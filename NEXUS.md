# NEXUS V7 Chrysalis

> Self-evolving Multi-Agent Orchestrator pursuing ASI through Darwinian evolution

---

## Vision: Intelligence Collaborative Déployable

**NEXUS n'est pas un simple outil - c'est une intelligence collaborative déployable qui se spécialise selon le contexte.**

### Le Concept Fondamental

NEXUS est conçu pour être **cloné dans n'importe quel projet** et devenir son intelligence dédiée :

```
┌─────────────────────────────────────────────────────────────┐
│  NEXUS CORE (Cloné dans Projet X)                           │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 1. ANALYZE    → Découvrir structure, stack, besoins    ││
│  │ 2. SPECIALIZE → Évoluer pour s'adapter au domaine      ││
│  │ 3. IDENTIFY   → Découvrir tâches & problèmes           ││
│  │ 4. EXECUTE    → Résoudre collaborativement             ││
│  │ 5. EVOLVE     → S'améliorer via données projet         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Flux de Déploiement

```bash
# 1. Cloner NEXUS dans le projet cible
cp -r NEXUS_V7_CHRYSALIS /path/to/project/.nexus

# 2. Lancer et laisser NEXUS analyser
cd /path/to/project/.nexus && python nexus7.py
nexus7> "Analyse ce projet et dis-moi ce que tu vois"
# → AutoBootstrap génère NEXUS.md adapté au projet

# 3. Spécialiser si nécessaire
nexus7> /specialize "Expert FastAPI e-commerce avec PostgreSQL"
# → Crée un spinoff spécialisé via brainstorm Claude+Gemini

# 4. Utiliser NEXUS spécialisé pour le travail quotidien
# → Le Swarm Engine choisit le mode de collaboration optimal par tâche
```

### Mécanismes d'Adaptation

| Mécanisme | Description | Quand |
|-----------|-------------|-------|
| **NEXUS.md** | Instructions spécifiques au projet (auto-générées) | Toujours |
| **AutoBootstrap** | Analyse et génère contexte initial | Premier lancement |
| **Évolution** | Crée enfants spécialisés pour expertise domaine | Projets complexes |
| **Mémoire** | Blackboard persiste les patterns appris | Entre sessions |
| **Swarm** | Négocie le mode de collaboration optimal | Chaque tâche |

### Objectif Ultime

Un NEXUS déployé dans un projet doit devenir :
- **Autonome** - Identifier et résoudre des problèmes sans prompts constants
- **Spécialisé** - Meilleur sur CE projet qu'une IA générique
- **Évolutif** - Amélioration continue des capacités spécifiques
- **Collaboratif** - Claude + Gemini travaillant comme une seule intelligence

**Ce n'est pas juste atteindre l'ASI abstraitement - c'est une superintelligence pratique pour des projets réels.**

---

## Tech Stack

**Language:** Python 3.13+
**Architecture:** FSM (Finite State Machine) + Hybrid Swarm Engine

**AI Models:**
- Claude Opus 4.5 / Sonnet 4.5 (via Claude CLI)
- Gemini 3 Pro / 2.5 Flash (via Gemini CLI)

**Key Libraries:**
- `pydantic` - Message validation
- `pathlib` - Cross-platform path handling
- `subprocess` - CLI invocation
- `json` - Protocol serialization
- Standard library only for core FSM

**Protocols:**
- Gemini: JSON strict (LightMessageV7, HeavyMessageV7)
- Claude: Hybrid (natural language + XML `<tool_use>` tags)

---

## Project Structure

```
NEXUS_V7_CHRYSALIS/
├── core/                    # Core orchestration engine
│   ├── orchestration_v7.py  # Main FSM orchestrator
│   ├── drivers/             # AI model drivers
│   │   ├── claude_driver_hybrid.py  # Claude CLI wrapper
│   │   └── gemini_driver_v7.py      # Gemini CLI wrapper
│   ├── execution/           # Tool execution layer
│   │   └── tool_manager.py  # 11 tools management
│   ├── fsm/                 # State machine components
│   │   ├── states.py        # State definitions
│   │   ├── panic_system.py  # Fatal error handling
│   │   └── stagnation_detector.py
│   ├── synapse/             # Memory & protocol
│   │   ├── memory_v6.py     # Blackboard persistence
│   │   └── protocol_v6.py   # Message validation
│   ├── swarm/               # Hybrid Swarm Engine
│   │   ├── task_analyzer.py # Complexity detection
│   │   ├── mode_selector.py # Collaboration mode selection
│   │   └── negotiation_protocol.py
│   ├── bootstrap/           # Auto-bootstrap system
│   │   └── auto_bootstrap.py # NEXUS.md generator
│   ├── interface/           # User interface
│   │   ├── repl.py          # Interactive REPL
│   │   └── commands.py      # Slash commands
│   ├── logging/             # Structured logging
│   └── governance/          # Alignment & KERNEL
├── prompts/                 # System prompts
│   ├── system_gemini_v7.md  # Gemini collaborator prompt
│   └── system_claude_v7.md  # Claude collaborator prompt
├── workspace/               # Runtime workspace
│   ├── _IO_BUFFER/          # Agent I/O files
│   ├── .nexus/              # State persistence
│   │   ├── blackboard.json  # Current state
│   │   └── history.txt      # Session history
│   └── logs/                # Runtime logs
├── tests/                   # Test suite (312+ tests)
├── nexus7.py               # Main entry point
└── NEXUS.md                # This file
```

---

## Key Commands

### Run NEXUS V7
```bash
cd NEXUS_V7_CHRYSALIS
python nexus7.py
```

### Run Tests
```bash
pytest tests/ -v
pytest tests/ -v --tb=short  # Compact output
pytest tests/test_specific.py -v  # Single file
```

### REPL Commands (inside nexus7>)
- `/status` - Show current FSM state and task
- `/bootstrap` - Re-analyze project and regenerate NEXUS.md
- `/reset` - Clear current task, return to IDLE
- `/evolve` - Start evolution mode (create child NEXUS)
- `/specialize <mission>` - Create specialized spinoff
- `exit` or `quit` - Exit NEXUS

### Git Workflow
```bash
git checkout N7C  # Development branch
git add . && git commit -m "feat(v7): description"
git push origin N7C
```

---

## Code Conventions

- **Indentation:** 4 spaces (Python)
- **Naming:** snake_case for functions/variables, PascalCase for classes
- **Type hints:** Required on all function signatures
- **Docstrings:** Google style for public APIs
- **Max line length:** 100 characters
- **Imports:** Standard lib → Third-party → Local (isort order)

---

## FSM States

```
IDLE → BRAINSTORMING → EXECUTING_TOOL → VALIDATING_CFL → IDLE
         ↓
    WAITING_USER (task finished)
         ↓
    ERROR → /reset → IDLE
         ↓
    PANIC (fatal - restart required)
```

**Swarm Extension:**
```
IDLE → SWARM_ANALYZING → SWARM_NEGOTIATING → SWARM_EXECUTING → VALIDATING_CFL
```

---

## DO NOT

### Critical Protection
- **DO NOT** modify `core/governance/KERNEL.py` - Immutable alignment core
- **DO NOT** disable security validators in `clone_and_mutate.py`
- **DO NOT** bypass path traversal protection
- **DO NOT** allow children to modify parent code

### Architecture Rules
- **DO NOT** use `subprocess.run()` with long timeouts - Use Popen with polling
- **DO NOT** block signal handlers - Always allow CTRL+C interruption
- **DO NOT** hardcode paths with `/` - Use `pathlib.Path` for cross-platform
- **DO NOT** catch bare `except:` - Always specify exception types

### Testing Rules
- **DO NOT** commit with failing tests
- **DO NOT** modify `tests/` structure without updating conftest.py
- **DO NOT** skip tests without documenting reason

### Data Rules
- **DO NOT** commit `.env` files or API keys
- **DO NOT** log sensitive data (tokens, credentials)
- **DO NOT** overwrite `workspace/.nexus/blackboard.json` without backup

---

## Architecture Notes

### Agent Communication
- Agents communicate via file-based I/O buffer (`workspace/_IO_BUFFER/`)
- Claude: `claude_context_in.md` → stdout parsed
- Gemini: `gemini_context_in.md` → `gemini_output.json`

### Model Routing
| Task Type | Claude | Gemini |
|-----------|--------|--------|
| Brainstorm, Evolution | Opus | 3-Pro |
| Reasoning, Research | Sonnet | 3-Pro |
| Tool execution | Sonnet | Flash |
| Validation | Sonnet | Flash |

### Swarm Collaboration Modes
- `PARALLEL` - Both work simultaneously
- `SEQUENTIAL` - Ordered execution
- `LEAD_SUPPORT` - Lead drives, support assists
- `PING_PONG` - Rapid alternation
- `SPECIALIST` - Single expert
- `RED_BLUE` - Adversarial review

### Evolution System
- Children created in `GENERATION_ACTIVE/`
- Selection via ASI Proximity Score
- Max 30 turns per evolution brainstorm
- 3 stagnant generations triggers human intervention

---

## Troubleshooting

### Common Issues

**CTRL+C not working:**
- Drivers use Popen with polling loop (not communicate())
- Check for blocking operations in tool execution

**Gemini CLI timeout:**
- Default timeout: 300s for reasoning models
- Check `gemini_driver_v7.py` timeout parameter

**Stale blackboard state:**
- Run `/reset` to clear current task
- Delete `workspace/.nexus/blackboard.json` if corrupted

**False positive framework detection:**
- Check `exclude_dirs` in `auto_bootstrap.py`
- Bootstrap module itself excluded from detection

---

## Testing

312+ tests covering:
- FSM state transitions
- Tool execution
- Protocol validation
- Swarm negotiation
- Security (path traversal, KERNEL protection)
- Integration scenarios

Run full suite before commits:
```bash
pytest tests/ -v --tb=short
```

---

## Related Documentation

- `CLAUDE.md` (parent directory) - Claude Code project instructions
- `prompts/system_*.md` - Agent system prompts
- `docs/` - Additional documentation
- `SESSION_CONTINUITY.md` - Session state tracking
