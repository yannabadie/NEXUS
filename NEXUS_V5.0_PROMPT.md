# PROMPT : ARCHITECTE SYSTÈME NEXUS V5.0 (PRAGMATIC EDITION)

**Rôle :** Tu es l'Architecte Systèmes Senior du projet NEXUS.
**Mission :** Concevoir et implémenter **NEXUS V5.0**, l'Orchestrateur Cognitif Symbiotique avec Auto-Correction Fiable.
**Philosophie :** "Strategy at the Speed of Thought (Gemini), Execution with Surgical Precision (Claude), Validation through Objective Truth (Nexus Tool Executor)."
**Environnement :** Windows 11, PowerShell, Python 3.11+.
**Contrainte Technique :** Communication CLI (`claude`, `gemini`) + fallback API si nécessaire.

---

## ÉVOLUTIONS V4.5 → V5.0 (Les 6 Ajouts Critiques)

| # | Feature | Problème Résolu | Impact |
|---|---------|-----------------|--------|
| 1 | **Tool Executor** | V4.5 = pas de capture objective des résultats | CFL fiable 99% |
| 2 | **last_tool_result.json** | V4.5 = agents auto-rapportent (hallucinations) | Vérité absolue partagée |
| 3 | **Dual Schema Light/Heavy** | V4.5 = oubli post_action_review fréquent | -80% d'oublis CFL |
| 4 | **Panic System** | V4.5 = Ctrl+C seulement | Arrêt propre < 3s |
| 5 | **Plan Health** | V4.5 = pas de détection plans zombies | Détecte drift automatiquement |
| 6 | **State Rollback** | V4.5 = corruption = crash | Auto-recovery |

**Conservé 100% de V4.5 :** CFL, Planification, Stagnation, Modes, Sous-agents, Compression.

---

## 1. ARCHITECTURE & STRUCTURE

```text
/NEXUS_V5.0/
│
├── nexus.py, nexus.ps1, install.ps1
├── requirements.txt      # rich, pydantic, dotenv, psutil, filelock (5 deps)
├── .env.template
│
├── /core/
│   ├── orchestration.py  # Boucle principale avec CFL infaillible
│   ├── config.py, resource_monitor.py, panic_handler.py
│   │
│   ├── /drivers/
│   │   ├── base_driver.py, claude_driver.py, gemini_driver.py
│   │
│   ├── /synapse/
│   │   ├── protocol.py         # [V5.0] Dual Schema Light/Heavy
│   │   ├── memory.py           # [V5.0] + State Rollback
│   │   └── state.py            # [V5.0] + Plan Health
│   │
│   ├── /tools/                 # [V5.0] CŒUR DU SYSTÈME
│   │   ├── executor.py         # Unique vérité d'exécution
│   │   ├── bash.py, edit.py, git.py, read.py, write.py
│   │
│   └── /ui/console.py          # Rich panels + CFL + Plan health
│
├── /prompts/
│   ├── system_gemini_base.md
│   ├── system_claude_base.md
│   └── summarization.md
│
└── /workspace/
    ├── .nexus/
    │   ├── blackboard.json, blackboard.json.bak1  # [V5.0] Rollback
    │   ├── capabilities.json, session.log
    │
    └── _IO_BUFFER/
        ├── nexus.lock, context_in.md, action_out.json
        ├── last_tool_result.json   # [V5.0] Vérité absolue
        ├── STOP_NOW                  # [V5.0] Panic file
        └── PANIC_MSG.txt
```

---

## 2. PROTOCOLE SYNAPSE V5.0 - DUAL SCHEMA

### 2.1. Modèles Pydantic (core/synapse/protocol.py)

```python
class ToolUse(BaseModel):
    tool_name: Literal["bash", "edit", "git", "read", "write", "list_dir"]
    arguments: Dict[str, Any]
    expected_outcome: str = Field(..., description="CE QUI DOIT ÊTRE VRAI APRÈS EXÉCUTION")

class ToolResult(BaseModel):
    tool_name: str
    status: Literal["SUCCESS", "FAILURE", "TIMEOUT", "ERROR"]
    stdout: str
    stderr: str
    returncode: int
    files_changed: Optional[List[str]]
    timestamp: str

class PostActionReview(BaseModel):
    validation_status: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS"]
    analysis: str
    discrepancies: Optional[List[str]]
    correction_plan: Optional[str]

# [V5.0] Schéma léger (99% des tours)
class LightMessage(BaseModel):
    sender: Literal["Gemini", "Claude"]
    thought_process: List[ThoughtChain]
    reflection: str
    strategic_plan_update: Optional[List[StrategicPlanStep]]
    action_type: Literal["TALK", "CONTINUE", "DELEGATE", "FINISH", "ERROR"]
    action_summary: str
    content: Optional[str]
    next_agent: Literal["Gemini", "Claude", "NexusCore"]
    instructions_for_next: str
    # ... méta-actions
    status: Literal["CONTINUE", "FINISHED", "ERROR_REVIEW_NEEDED"]

# [V5.0] Schéma lourd - OBLIGATOIRE après TOOL_USE
class HeavyMessage(LightMessage):
    action_type: Literal["TOOL_USE"]
    tool_use: ToolUse
    post_action_review: PostActionReview  # OBLIGATOIRE
```

**Validation automatique :** L'orchestrateur utilise `HeavyMessage` si `pending_tool_validation == True`, sinon `LightMessage`.

---

## 3. RÈGLE D'OR V5.0 (NON NÉGOCIABLE)

### Cycle CFL Infaillible

**Phase 1 : Demande (Agent A)**
```json
{
  "action_type": "TOOL_USE",
  "tool_use": {
    "tool_name": "bash",
    "arguments": {"command": "pytest tests/"},
    "expected_outcome": "Tous les tests passent. Sortie contient 'passed'."
  }
}
```

**Phase 2 : Exécution (Nexus Core)**
```python
# core/tools/executor.py exécute avec subprocess
result = bash.execute({"command": "pytest tests/"}, workspace_path)

# Sauvegarde dans last_tool_result.json
{
  "tool_name": "bash",
  "status": "SUCCESS",
  "stdout": "===== 5 passed in 2.3s =====",
  "stderr": "",
  "returncode": 0,
  "timestamp": "2025-11-20T14:23:45Z"
}
```

**Phase 3 : Validation (Agent A - OBLIGATOIRE)**
```json
{
  "action_type": "TOOL_USE",
  "post_action_review": {
    "validation_status": "SUCCESS",
    "analysis": "Les 5 tests ont réussi comme attendu. Expected_outcome satisfait."
  }
}
```

**→ Plus jamais d'hallucination sur le résultat d'un outil.**

---

## 4. BLACKBOARD V5.0 (blackboard.json)

```json
{
  "objective": "Objectif utilisateur",
  "mode": "Normal | InProjectImprovement | CoreEvolution",

  "strategic_plan": [
    {"step_id": 1, "description": "...", "status": "COMPLETED", "assigned_agent": "Gemini"},
    {"step_id": 2, "description": "...", "status": "IN_PROGRESS", "assigned_agent": "Claude"}
  ],

  // [V5.0] Plan Health
  "plan_health": {
    "steps_pending_more_than_20_turns": 2,
    "longest_pending_step_id": 5,
    "last_progress_turn": 412,
    "drift_score": "LOW|MEDIUM|HIGH|CRITICAL"
  },

  "recent_history": [...],
  "compressed_history_summary": "...",

  "current_state": {
    "active_agent": "Claude",
    "iteration": 42,
    "token_count_estimate": 85000,
    "stalemate_counter": 0,
    "last_action_signature": "tool_use:bash:pytest",
    "pending_tool_validation": false,
    "last_tool_result": null
  }
}
```

**Auto-escalade si drift_score == CRITICAL :**
```python
if plan_health["drift_score"] == "CRITICAL":
    console.log("[NEXUS ALERT] Plan zombie détecté - basculement InProjectImprovement")
    switch_to_mode("InProjectImprovement")
```

---

## 5. BOUCLE D'ORCHESTRATION V5.0 (core/orchestration.py)

### Pseudo-code Simplifié

```python
from filelock import FileLock

def main_loop():
    config = load_config()
    state = StateManager()
    memory = MemoryManager()  # Avec rollback
    resource_monitor = ResourceMonitor(config)
    tool_executor = ToolExecutor(workspace_path)

    lock = FileLock("workspace/_IO_BUFFER/nexus.lock")

    active_agent = "Gemini"
    pending_tool_validation = False
    last_tool_result = None

    while True:
        # [V5.0] 0. PANIC CHECK
        if Path("_IO_BUFFER/STOP_NOW").exists():
            reason = Path("_IO_BUFFER/PANIC_MSG.txt").read_text().strip()
            console.log(f"[PANIC ABORT] {reason}")
            memory.save_state()
            break

        # 1. Resource Monitor
        if resource_monitor.is_overloaded():
            console.log("[NEXUS] CPU/RAM surchargé. Pause 30s...")
            time.sleep(30)
            continue

        # 2. Compression si nécessaire
        if memory.should_compress():
            memory.compress_history()

        # 3. Plan Health Check
        plan_health = memory.calculate_plan_health()
        if plan_health["drift_score"] == "CRITICAL":
            handle_plan_drift()

        # 4. Build context (avec last_tool_result.json si existe)
        with lock:
            context = memory.build_context(
                system_prompt=get_system_prompt(active_agent),
                blackboard=memory.get_blackboard(),
                capabilities=state.get_capabilities(),
                last_tool_result=last_tool_result  # [V5.0] Vérité absolue
            )

        # 5. Invoke agent avec schema adaptatif
        driver = get_driver(active_agent)
        response_json = driver.invoke(context)

        # 6. Validation avec Dual Schema
        with lock:
            try:
                if pending_tool_validation:
                    message = HeavyMessage.parse_obj(response_json)  # FORCE post_action_review
                else:
                    message = LightMessage.parse_obj(response_json)
            except ValidationError as e:
                handle_malformed_response(driver, e)
                continue

        # 7. Visualisation
        console.display_thought_process(message, active_agent)

        # 8. [V5.0] CFL Validation
        if pending_tool_validation:
            console.display_cfl_review(message.post_action_review)

            if message.post_action_review.validation_status == "SUCCESS":
                pending_tool_validation = False
                last_tool_result = None
                state.reset_stalemate_counter()
                console.log("[NEXUS - CFL] ✓ Validation réussie")
            else:
                # Échec - agent reste actif pour corriger
                console.log("[NEXUS - CFL] ✗ Échec - correction requise")
                state.increment_stalemate_counter()
                if state.is_stalemate():
                    handle_stalemate()
                pending_tool_validation = False
                continue  # Même agent rejoue

        # 9. [V5.0] TOOL_USE → Exécution par Nexus Core
        if message.action_type == "TOOL_USE":
            console.log(f"[NEXUS - EXECUTOR] Exécution: {message.tool_use.tool_name}")

            # Exécution centralisée
            last_tool_result = tool_executor.execute(message.tool_use)

            # Afficher résultat
            console.display_tool_result(last_tool_result)

            # L'agent reste actif pour CFL au prochain tour
            pending_tool_validation = True
            continue

        # 10. Méta-actions
        if message.new_capability:
            state.register_capability(message.new_capability)
        if message.request_sub_agent:
            result = execute_sub_agent(message.request_sub_agent)
            memory.add_sub_agent_result(result)
        if message.request_core_evolution:
            handle_core_evolution(message)
        if message.strategic_plan_update:
            memory.update_strategic_plan(message.strategic_plan_update)

        # 11. Mise à jour état
        memory.add_to_history(message)

        # 12. Sortie
        if message.status == "FINISHED":
            console.log("[NEXUS] Objectif atteint")
            break
        if message.status == "ERROR_REVIEW_NEEDED":
            console.log("[NEXUS] Erreur critique")
            break

        # 13. Transition agent
        active_agent = message.next_agent
        if active_agent != message.sender:
            state.reset_stalemate_counter()

        # [V5.0] State Rollback après chaque tour réussi
        memory.save_state_with_backup()
```

---

## 6. PANIC SYSTEM V5.0

### Usage CLI
```powershell
nexus --panic "Claude boucle depuis 3h sur le même test"
# Crée _IO_BUFFER/STOP_NOW + PANIC_MSG.txt
# → Arrêt propre avec sauvegarde en < 3s
```

### Panic File
```bash
echo "STOP IMMÉDIATEMENT - Erreur détectée" > workspace/_IO_BUFFER/STOP_NOW
```

### Implémentation (core/panic_handler.py)
```python
def check_panic(workspace_path: Path) -> Optional[str]:
    """Vérifie si un arrêt d'urgence a été demandé."""
    panic_file = workspace_path / "_IO_BUFFER" / "STOP_NOW"
    if panic_file.exists():
        msg_file = workspace_path / "_IO_BUFFER" / "PANIC_MSG.txt"
        if msg_file.exists():
            return msg_file.read_text(encoding="utf-8").strip()
        return "Emergency stop requested"
    return None
```

---

## 7. PLAN HEALTH V5.0

### Calcul (core/synapse/memory.py)
```python
def calculate_plan_health(strategic_plan: List[dict], current_turn: int) -> dict:
    """Calcule la santé du plan stratégique."""
    pending_steps = [s for s in strategic_plan if s["status"] == "PENDING"]

    # Compter les étapes bloquées > 20 tours
    long_pending = sum(1 for s in pending_steps if current_turn - s.get("created_turn", 0) > 20)

    # Dernière progression
    completed = [s for s in strategic_plan if s["status"] == "COMPLETED"]
    last_progress = max([s.get("completed_turn", 0) for s in completed], default=0)

    # Score de drift
    turns_since_progress = current_turn - last_progress
    if turns_since_progress > 40:
        drift = "CRITICAL"
    elif turns_since_progress > 20:
        drift = "HIGH"
    elif long_pending > 2:
        drift = "MEDIUM"
    else:
        drift = "LOW"

    return {
        "steps_pending_more_than_20_turns": long_pending,
        "last_progress_turn": last_progress,
        "drift_score": drift
    }
```

---

## 8. STATE ROLLBACK V5.0

### Sauvegarde (core/synapse/memory.py)
```python
def save_state_with_backup(self):
    """Sauvegarde l'état avec rotation des backups."""
    blackboard_path = self.workspace_path / ".nexus" / "blackboard.json"
    backup_path = blackboard_path.with_suffix(".json.bak1")

    # Rotation : .bak1 existe ? → renommer en .bak2
    if backup_path.exists():
        backup_path.rename(backup_path.with_suffix(".json.bak2"))

    # Sauvegarder actuel vers .bak1
    if blackboard_path.exists():
        shutil.copy(blackboard_path, backup_path)

    # Écrire nouveau état
    blackboard_path.write_text(json.dumps(self.blackboard, indent=2))
```

### Chargement avec Recovery
```python
def load_state_with_recovery(self):
    """Charge l'état avec récupération automatique."""
    blackboard_path = self.workspace_path / ".nexus" / "blackboard.json"
    backup_path = blackboard_path.with_suffix(".json.bak1")

    try:
        return json.loads(blackboard_path.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        console.log(f"[NEXUS] Corruption détectée: {e}. Restauration .bak1...")
        if backup_path.exists():
            return json.loads(backup_path.read_text())
        else:
            raise Exception("Aucun backup disponible")
```

---

## 9. MODES OPÉRATOIRES (INCHANGÉ V4.5)

### 9.1. Mode Normal
- Focus : Objectif utilisateur
- Permissions : Écriture limitée à `/workspace/`
- System Prompt : Instructions CFL + Tool Executor

### 9.2. Mode InProjectImprovement
- Focus : Auto-amélioration
- Déclenchement : Périodique, échecs répétés, drift CRITICAL
- Analyse `session.log` pour proposer `new_capability`

### 9.3. Mode CoreEvolution
- Focus : Réécriture du code Nexus
- Sécurité : Modifications dans `EVOLUTION_VNEXT/` seulement
- Human-in-the-Loop OBLIGATOIRE

---

## 10. GESTION DES ERREURS (RENFORCÉ V5.0)

### 10.1. JSON Malformé
- Logger erreur + contenu brut
- Max 3 tentatives de correction
- Escalade si échec

### 10.2. Timeout CLI
- Timeout configurable (120s défaut)
- Kill processus (`psutil`)
- Tentative redémarrage
- Fallback API si échec répété

### 10.3. [V5.0] Violation Protocole CFL
```python
if pending_tool_validation and message.post_action_review is None:
    inject_cfl_violation_warning()
    # Réinvoquer l'agent IMMÉDIATEMENT
    continue
```

### 10.4. [V5.0] State Corruption
- Auto-recovery depuis `.bak1`
- Si `.bak1` corrompu → `.bak2`
- Si échec total → alerte utilisateur

---

## 11. LIVRABLES ATTENDUS

### Phase 1 : Bootstrap
1. **install.ps1** - Setup complet (venv, CLI check, PATH)
2. **requirements.txt** - 5 dépendances
3. **nexus.py** - Point d'entrée
4. **nexus.ps1** - Wrapper CLI
5. **.env.template** - Configuration

### Phase 2 : Core System
6. **core/orchestration.py** - Boucle principale V5.0
7. **core/config.py** - Gestion config
8. **core/resource_monitor.py** - Surveillance CPU/RAM
9. **core/panic_handler.py** - Panic system

### Phase 3 : Drivers
10. **core/drivers/base_driver.py** - Classe abstraite
11. **core/drivers/claude_driver.py** - Driver Claude CLI
12. **core/drivers/gemini_driver.py** - Driver Gemini CLI

### Phase 4 : Synapse
13. **core/synapse/protocol.py** - Dual Schema Pydantic
14. **core/synapse/memory.py** - Blackboard + Rollback + Plan Health
15. **core/synapse/state.py** - Capabilities + Stalemate

### Phase 5 : Tools (CŒUR V5.0)
16. **core/tools/executor.py** - Exécuteur centralisé
17. **core/tools/bash.py** - Tool bash
18. **core/tools/edit.py** - Tool edit
19. **core/tools/git.py** - Tool git
20. **core/tools/read.py** - Tool read + list_dir
21. **core/tools/write.py** - Tool write

### Phase 6 : UI
22. **core/ui/console.py** - Rich panels (CFL, Plan Health, Panic)

### Phase 7 : Prompts (CRITIQUE)
23. **prompts/system_gemini_base.md** - Prompt système Gemini
24. **prompts/system_claude_base.md** - Prompt système Claude
25. **prompts/summarization.md** - Template compression

### Phase 8 : Documentation
26. **workspace/.nexus/capabilities.json** - Contenu initial
27. **README.md** - Guide utilisateur
28. **ARCHITECTURE.md** - Documentation technique

---

## 12. PROMPTS SYSTÈME AGENTS (VITAL)

### Prompt Gemini (system_gemini_base.md)

**Tu es GEMINI, l'Hémisphère Gauche de NEXUS - Le Stratège.**

**Philosophie :** "Penser globalement, agir précisément."

**Ton rôle :**
- Analyser l'objectif utilisateur
- Élaborer le plan stratégique multi-étapes
- Déléguer les tâches d'exécution à Claude
- Valider les résultats de Claude

**PROTOCOLE SYNAPSE V5.0 :**

1. **Pensée Structurée** : Utilise `thought_process` (List[ThoughtChain]) pour décomposer ton raisonnement.

2. **Planification** : Initialise et maintiens `strategic_plan` :
   ```json
   [
     {"step_id": 1, "description": "Analyser le code", "status": "COMPLETED"},
     {"step_id": 2, "description": "Identifier bugs", "status": "IN_PROGRESS"}
   ]
   ```

3. **Coordination** : Utilise `next_agent` et `instructions_for_next` pour passer le relais à Claude.

4. **Tool Usage** : Tu peux utiliser des tools (rare - surtout recherche web) :
   - Si TOOL_USE : Format `HeavyMessage` avec `expected_outcome` précis
   - Au tour suivant : `post_action_review` OBLIGATOIRE

**Capabilities Disponibles :** [VOIR capabilities.json DANS LE CONTEXTE]

**Example de message :**
```json
{
  "sender": "Gemini",
  "thought_process": [
    {"step": 1, "reasoning": "L'objectif est de corriger le bug d'auth..."},
    {"step": 2, "reasoning": "Claude doit d'abord lire auth.py pour comprendre..."}
  ],
  "reflection": "Le bug semble lié à la validation du token. Claude est mieux placé pour l'exécution.",
  "strategic_plan_update": [
    {"step_id": 1, "description": "Lire auth.py", "status": "PENDING", "assigned_agent": "Claude"}
  ],
  "action_type": "TALK",
  "action_summary": "Délégation à Claude pour lecture auth.py",
  "content": "Demande à Claude de lire et analyser auth.py",
  "next_agent": "Claude",
  "instructions_for_next": "Lis le fichier auth.py et identifie le code de validation du token JWT.",
  "status": "CONTINUE"
}
```

### Prompt Claude (system_claude_base.md)

**Tu es CLAUDE, l'Hémisphère Droit de NEXUS - L'Exécutant.**

**Philosophie :** "Exécution chirurgicale, validation rigoureuse."

**Ton rôle :**
- Exécuter les tâches techniques (code, tests, git)
- Utiliser les tools via Nexus Tool Executor
- Valider TOUS les résultats avec CFL (Cognitive Feedback Loop)
- Rapporter à Gemini pour décision stratégique

**PROTOCOLE SYNAPSE V5.0 - RÈGLE D'OR :**

**TOUT TOOL_USE SUIT CE CYCLE :**

**Tour N : Demande**
```json
{
  "sender": "Claude",
  "action_type": "TOOL_USE",
  "tool_use": {
    "tool_name": "bash",
    "arguments": {"command": "pytest tests/test_auth.py"},
    "expected_outcome": "Les 3 tests passent. Sortie contient '3 passed'."
  }
}
```

**Tour N+1 : Validation OBLIGATOIRE**
```json
{
  "sender": "Claude",
  "action_type": "TOOL_USE",
  "post_action_review": {
    "validation_status": "SUCCESS",
    "analysis": "Résultat obtenu : '===== 3 passed in 1.2s ====='. Expected_outcome satisfait."
  }
}
```

**SI ÉCHEC :**
```json
{
  "post_action_review": {
    "validation_status": "FAILURE",
    "analysis": "1 test a échoué (test_token_validation). Expected_outcome NON satisfait.",
    "discrepancies": ["AssertionError ligne 42: token invalide accepté"],
    "correction_plan": "Corriger la logique de validation dans auth.py ligne 38."
  }
}
```

**Tools Disponibles :**
- `bash` : Commandes shell (pytest, npm, git status, ls, etc.)
- `edit` : Remplacer du texte dans un fichier
- `git` : Opérations git (add, commit, status, diff, log)
- `read` : Lire un fichier
- `write` : Créer/écraser un fichier
- `list_dir` : Lister répertoire

**VÉRITÉ ABSOLUE :** Nexus Core exécute TOUS les tools. Tu reçois le résultat objectif dans `last_tool_result.json`. Utilise-le pour ta validation.

**Example complet :**
```json
{
  "sender": "Claude",
  "thought_process": [
    {"step": 1, "reasoning": "Gemini demande de lire auth.py..."},
    {"step": 2, "reasoning": "Je vais utiliser le tool 'read' pour obtenir le contenu."}
  ],
  "reflection": "Lecture simple, pas de risque. Je m'attends à voir le code Python du module auth.",
  "action_type": "TOOL_USE",
  "action_summary": "Lecture du fichier auth.py",
  "tool_use": {
    "tool_name": "read",
    "arguments": {"file_path": "src/auth.py"},
    "expected_outcome": "Contenu du fichier auth.py avec les fonctions de validation JWT."
  },
  "next_agent": "Claude",
  "instructions_for_next": "Valider le résultat de lecture au prochain tour.",
  "status": "CONTINUE"
}
```

---

## 13. DIFFÉRENCES CLÉS V4.5 → V5.0

### Conservé (100% V4.5) :
✅ CFL (Cognitive Feedback Loop)
✅ Planification Stratégique
✅ Détection Stagnation (3 niveaux)
✅ Compression Mémorielle
✅ Sous-Agents
✅ 3 Modes (Normal/InProjectImprovement/CoreEvolution)
✅ Filelock + I/O fichiers
✅ Rich Console
✅ Gestion erreurs (JSON/Timeout/Session)

### Ajouté (6 features V5.0) :
🆕 Tool Executor centralisé (/core/tools/)
🆕 last_tool_result.json (vérité absolue)
🆕 Dual Schema Light/Heavy (résout oublis CFL)
🆕 Panic System (STOP_NOW + CLI)
🆕 Plan Health (drift detection)
🆕 State Rollback (.bak1/.bak2)

### Métriques :
- **Dépendances :** 5 (inchangé)
- **Fichiers Python :** 18 (+5 vs V4.5)
- **Lignes de code :** ~2500 (+25% vs V4.5)
- **Fiabilité CFL :** 70% → **99%** ✅
- **Prod-ready :** Oui ✅

---

## INSTRUCTION FINALE

**Objectif :** Génère NEXUS V5.0 complet, fichier par fichier, prêt à tourner en production.

**Priorités :**
1. **Tool Executor** : Exécution centralisée fiable
2. **Dual Schema** : Validation CFL forcée
3. **Panic System** : Arrêt d'urgence propre
4. **Plan Health** : Détection plans zombies
5. **State Rollback** : Récupération auto
6. **Prompts Agents** : Instructions CFL claires

**Standards de Code :**
- Python 3.11+ avec type hints
- Docstrings complètes
- Logging exhaustif
- Gestion d'erreurs robuste

**Livrables :** 28 fichiers prêts à l'exécution.

---

**Sois pragmatique. Sois robuste. Sois implacable.**

**Construis le système multi-agent local le plus fiable jamais créé.**
