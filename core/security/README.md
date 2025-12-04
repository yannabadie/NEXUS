# Module: Security - Defense-in-Depth Layer

**Version**: 7.5 (HIVE MIND)
**Last Updated**: 2025-12-04

---

## Role Architectural

Implementation des mecanismes de defense actifs qui enforecent les politiques de Governance. Protege le code parent NEXUS et le systeme utilisateur.

**Principe**: Defense multi-couches - chaque requete passe par plusieurs validations.

---

## Alignement ROADMAP V7.5+

| Phase ROADMAP | Impact sur ce module |
|---------------|---------------------|
| **Phase 5: Agent Factory** | PathGuardian protege agents spawnes |
| **Phase 7: Session Isolation** | PathGuardian supportera sessions isolees |
| **Phase 8: Self-Healing** | IntegrityMonitor detectera corruption |

**MutationValidator**: Utilise par `core/evolution/phases/create.py` pour valider le code genere par AI.

---

## Composants Cles

### Fichier: `execution_policy.py` (Phase 14a)

**Classe**: `ExecutionPolicy`

* **Fonction**: Validation securisee des commandes bash
* **Interaction FSM**: Consulte par ToolManager._execute_bash()
* **Notes d'Audit**: Phase 14a Security Hardening

**Defense Layers**:
1. Blocked pattern detection (fork bombs, password files, etc.)
2. Dangerous executable blocking (sudo, nc, curl, wget, etc.)
3. Command analysis (SIMPLE vs COMPLEX)
4. shell=False pour commandes simples, shell=True pour grep/cat avec pipe

**Commandes Bloquees**:
| Type | Exemples | Raison |
|------|----------|--------|
| Privilege Escalation | `sudo`, `su`, `pkexec` | Elevation privileges |
| Network Exfiltration | `nc`, `curl`, `wget` | Transfert donnees |
| Destructive | `rm -rf /`, `dd`, `mkfs` | Destruction systeme |
| Code Execution | `perl`, `php`, `powershell` | Payload execution |

**Patterns Bloques**:
- `/etc/passwd`, `/etc/shadow` - Fichiers sensibles
- `$(...)`, `` `...` `` - Command substitution
- `:(){:|:&};:` - Fork bombs
- `while true` - Boucles infinies

**Usage**:
```python
from core.security.execution_policy import ExecutionPolicy, CommandType

policy = ExecutionPolicy(workspace_path)

# Validate command
is_valid, error = policy.validate_command("ls -la")
if not is_valid:
    print(f"Blocked: {error}")

# Analyze for shell execution
analysis = policy.analyze_command("ls -la")
if analysis.command_type == CommandType.SIMPLE:
    subprocess.run(["ls", "-la"], shell=False)  # SECURE
```

---

### Fichier: `path_guardian.py`

**Classe**: `PathGuardian`

* **Fonction**: Autorite centrale pour controle d'acces fichiers
* **Interaction FSM**: Consulte par ToolManager avant chaque operation fichier
* **Notes d'Audit**: OK - Protection robuste

**Zones de securite**:
| Zone | Chemin | Permissions |
|------|--------|-------------|
| Workspace | `workspace/` | Read/Write |
| Agents | `workspace/agents/` | Read/Write |
| Evolution | `GENERATION_ACTIVE/` | Read/Write (mode evolution) |
| Parent | `core/`, `prompts/` | **Read-Only** |

**Fichiers Immutables**:
- `KERNEL.py` - Noyau alignement
- `MISSION.md` - Mission NEXUS
- `.env` - Secrets

**Protections Anti-Traversal**:
- Resolution symlinks
- Blocage chemins `..`
- Normalisation paths

---

### Fichier: `mutation_validator.py`

**Classe**: `MutationValidator`

* **Fonction**: Analyse statique AST du code genere par AI
* **Interaction FSM**: Appele par CreatePhase lors de l'application des mutations
* **Notes d'Audit**: Mode WARN-ONLY (ne bloque pas, mais log)

**Verifications**:
| Type | Exemples | Action |
|------|----------|--------|
| Appels Dangereux | `exec`, `eval`, `os.system`, `subprocess.Popen` | Warning |
| Imports Suspects | `socket`, `ctypes`, `pickle` | Warning |
| Patterns Malveillants | `rm -rf`, `format C:` | Warning |

**Usage**:
```python
validator = MutationValidator(workspace_path)
warnings, errors = validator.validate(code, filename)
if warnings:
    logger.warning(f"Code risks: {warnings}")
```

---

### Fichier: `integrity_monitor.py`

**Classe**: `IntegrityMonitor`

* **Fonction**: Verification integrite systeme au demarrage
* **Interaction FSM**: Execute au boot de NEXUS (nexus7.py)
* **Notes d'Audit**: OK - Protection KERNEL.py

**Verifications au boot**:
1. Hash SHA-256 de `KERNEL.py` vs `KERNEL_HASH.txt`
2. Existence fichiers critiques
3. Permissions coherentes

**Comportement sur echec**:
- Modification KERNEL detectee -> **ABORT** execution
- Fichier manquant -> Warning + continue

---

### Fichier: `__init__.py`

* **Fonction**: Exports publics (PathGuardian, MutationValidator, IntegrityMonitor)
* **Notes d'Audit**: OK

---

## Architecture Defense-in-Depth

```
                    REQUEST
                       |
                       v
    Layer 1: ExecutionPolicy (command validation - Phase 14a)
              - Blocked executables (sudo, nc, curl)
              - Dangerous patterns (fork bomb, /etc/passwd)
              - Command analysis (SIMPLE vs COMPLEX)
                       |
                       v
    Layer 2: PathGuardian (file access)
              - Workspace containment
              - Immutable file protection
                       |
                       v
    Layer 3: SandboxPolicy (FSM state check - governance/)
              - Tool permissions during brainstorming
              - SAFE vs BLOCKED tools
                       |
                       v
    Layer 4: MutationValidator (code analysis)
              - AST inspection
              - Dangerous call detection
                       |
                       v
                   EXECUTION
              (shell=False preferred)
```

**Principe**: Echec a n'importe quelle couche = blocage.

**Phase 14a**: Tool manager now uses `shell=False` for simple commands.

---

## Dependances et Interactions (Synapses)

```
ToolManager ─────────────► PathGuardian
                               |
Evolution/CreatePhase ────► MutationValidator
                               |
nexus7.py (boot) ─────────► IntegrityMonitor
```

**Imports**:
- Standard library: `pathlib`, `hashlib`, `ast`
- Aucune dependance externe

---

## Usage

```python
from core.security import PathGuardian, MutationValidator, IntegrityMonitor
from pathlib import Path

# 1. Validation chemin
guardian = PathGuardian(workspace=Path("workspace"), parent=Path("."))
valid, resolved, msg = guardian.validate_write("core/orchestration_v7.py")
if not valid:
    print(f"Blocked: {msg}")  # "Write to parent code blocked"

# 2. Validation code mute
validator = MutationValidator(Path("workspace"))
warnings, errors = validator.validate(
    "import os; os.system('rm -rf /')",
    "dangerous.py"
)
# warnings: ["Dangerous call: os.system", "Dangerous pattern: rm -rf"]

# 3. Verification integrite
monitor = IntegrityMonitor(Path("."))
if not monitor.verify_kernel():
    raise SystemExit("KERNEL.py compromised!")
```

---

## Voir Aussi

- [Governance Module](../governance/README.md) - Definitions des politiques
- [Execution Module](../execution/README.md) - Firewall outils
- [Evolution Module](../evolution/README.md) - Utilise MutationValidator
