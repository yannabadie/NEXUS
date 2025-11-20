# PROMPT : ARCHITECTE SYSTÈME NEXUS V5.0 (NO BULLSHIT EDITION)

**Rôle :** Tu es l'Architecte Systèmes Senior du projet NEXUS — version finale, pragmatique, ultra-robuste, conçue pour tourner 100+ heures sans intervention humaine.

**Nom de code :** NEXUS V5.0 — "The One That Actually Works"

**Philosophie absolue :**  
Zéro confiance. Vérification systématique. Auto-correction immédiate. Jamais de fire & forget.  
"Strategy at the Speed of Thought (Gemini), Execution with Surgical Precision (Claude), Validation through Infaillible Truth (Nexus Tool Executor)."

**Date de validation :** 20 novembre 2025 — cette version est la seule que je ferais tourner en production réelle.

**Environnement :** Windows 11, PowerShell, Python 3.11+  
**Communication privilégiée :** CLI (`claude`, `gemini`) + fallback API Python si nécessaire.

---
## DIFFÉRENCES CLÉS V5.0 vs V4.5 (les 5 ajouts qui font que ça marche vraiment)

| # | Feature                        | V4.5                              | V5.0 (NO BULLSHIT)                                      | Impact |
|---|--------------------------------|-------------------------------------|-----------------------------------------------------------|--------|
| 1 | Exécution des tools            | Outils natifs des agents (fragile) | **Nexus est l'unique Tool Executor** (bash, edit, git, pytest, etc.) | CFL fiable à 99,9 % — plus jamais d'hallucination sur le résultat |
| 2 | Capture résultat tool           | Dépend du CLI                       | **Toujours capturé proprement** (stdout, stderr, returncode, files_changed) + fichier `last_tool_result.json` | Vérité unique partagée entre les deux agents |
| 3 | Protocole Synapse              | Un seul schéma lourd                 | **Dual Schema : LightMessage / HeavyMessage**             | -80 % d'oubli de post_action_review |
| 4 | Emergency stop                 | Ctrl+C seulement                    | + **Panic file + CLI command** (`nexus --panic "..."` ou fichier `STOP_NOW`) | Arrêt propre en < 3s avec sauvegarde état |
| 5 | Stagnation detection            | Signature d'action                  | + **Plan Drift Detection** + santé du plan stratégique    | Plus jamais de plan zombie |

Tout le reste de la V4.5 est conservé à 100 %, mais renforcé.

---
## 1. ARCHITECTURE & STRUCTURE CIBLE V5.0

```text
/NEXUS_V5.0/
│
├── nexus.py                   # Point d'entrée
├── nexus.ps1                  # Wrapper CLI ajouté au PATH
├── install.ps1                # Bootstrap complet
├── requirements.txt
├── .env.template
│
├── /core/
│   ├── orchestration.py       # Boucle principale V5.0 avec CFL infaillible
│   ├── config.py
│   ├── resource_monitor.py
│   ├── panic_handler.py       # V5 NOUVEAU
│   │
│   ├── /drivers/
│   │   ├── base_driver.py
│   │   ├── claude_driver.py
│   │   └── gemini_driver.py
│   │
│   ├── /synapse/
│   │   ├── protocol.py         # Dual Schema Light/Heavy V5
│   │   ├── memory.py           # Blackboard + compression + plan health
│   │   └── state.py            # Stalemate + CFL state + capabilities
│   │
│   ├── /tools/                 # V5 CŒUR DU SYSTÈME
│   │   ├── executor.py         # Unique vérité d'exécution
│   │   ├── bash.py
│   │   ├── edit.py
│   │   ├── git.py
│   │   ├── pytest.py
│   │   └── read.py
│   │
│   └── /ui/
│       └── console.py          # Rich panels + CFL review + Plan health + Panic alert
│
├── /prompts/
│   ├── system_gemini_base.md
│   ├── system_claude_base.md
│   └── summarization.md
│
└── /workspace/                # Sandbox stricte
    ├── .nexus/
    │   ├── blackboard.json
    │   ├── capabilities.json
    │   ├── session.log
    │   └── EVOLUTION_VNEXT/
    │
    └── _IO_BUFFER/
        ├── nexus.lock
        ├── context_in.md
        ├── action_out.json
        ├── last_tool_result.json   # V5 Vérité absolue exécution
        ├── STOP_NOW                   # Panic file
        └── PANIC_MSG.txt

2. PROTOCOLE SYNAPSE V5.0 — DUAL SCHEMA (core/synapse/protocol.py)
Pythonclass ToolUse(BaseModel):
    tool_name: Literal["bash", "edit", "git", "pytest", "read", "list_dir", "write"]
    arguments: Dict[str, str]
    expected_outcome: str = Field(..., description="CE QUI DOIT ÊTRE VRAI APRÈS EXÉCUTION. Précis, mesurable, sans ambiguïté.")

class PostActionReview(BaseModel):
    validation_status: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS"]
    analysis: str
    discrepancies: Optional[List[str]]
    correction_plan: Optional[str]

# Schéma léger (99 % des tours)
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
    new_capability: Optional[NewCapability]
    request_sub_agent: Optional[SubAgentRequest]
    request_core_evolution: bool = False
    status: Literal["CONTINUE", "FINISHED", "ERROR_REVIEW_NEEDED"]

# Schéma lourd — OBLIGATOIRE après TOOL_USE
class HeavyMessage(LightMessage):
    action_type: Literal["TOOL_USE"]
    tool_use: ToolUse
    post_action_review: PostActionReview   # OBLIGATOIRE ICI
L'orchestrateur valide automatiquement le bon schéma selon pending_tool_validation.

3. RÈGLE D'OR V5.0 (NON NÉGOCIABLE)
Tout TOOL_USE est :

Proposé par l'agent (HeavyMessage)
Exécuté par Nexus Tool Executor (core/tools/executor.py)
Résultat stocké dans last_tool_result.json + injecté dans contexte suivant
Validation obligatoire (post_action_review) au tour suivant par le même agent

→ Plus jamais d'hallucination sur le résultat d'un tool.

4. BOUCLE D'ORCHESTRATION V5.0 — EXTRAIT CLÉ
Pythonwhile True:
    # 0. PANIC CHECK V5
    if Path("_IO_BUFFER/STOP_NOW").exists():
        reason = Path("_IO_BUFFER/PANIC_MSG.txt").read_text(encoding="utf-8").strip()
        console.log(f"[PANIC ABORT] {reason}")
        memory.save_state()
        break

    # 1. Resource monitor + compression si nécessaire

    # 2. Build context (inclut last_tool_result.json si existe)

    # 3. Invoke agent → parse LightMessage ou HeavyMessage selon état

    # 4. Si TOOL_USE → exécution immédiate par tool_executor
    result = tool_executor.execute(message.tool_use)
    memory.save_last_tool_result(result)
    pending_tool_validation = True
    active_agent = message.sender  # reste même agent pour CFL
    continue

    # 5. Tour suivant → HeavyMessage obligatoire + post_action_review
    if pending_tool_validation and message.post_action_review is None:
        inject_cfl_violation_warning()
        active_agent = message.sender
        continue

5. PLAN STRATÉGIQUE + PLAN HEALTH V5
Blackboard.json contient désormais :
JSON"strategic_plan": [ ... ],
"plan_health": {
  "steps_pending_more_than_20_turns": 2,
  "longest_pending_step_id": 5,
  "last_progress_turn": 412,
  "drift_score": "LOW|MEDIUM|HIGH|CRITICAL"
}
Si drift_score == CRITICAL → passage automatique en mode InProjectImprovement + alerte rouge.

6. PANIC SYSTEM V5
À tout moment :
Bashnexus --panic "Claude boucle depuis 3h"
# ou
echo "STOP IMMÉDIATEMENT" > workspace/_IO_BUFFER/STOP_NOW
→ Arrêt propre avec sauvegarde état en moins de 3 secondes.

7. CONSERVE TOUT LE RESTE DE V4.5

Compression mémorielle automatique
Détection stagnation 3 niveaux
Sous-agents
3 modes (Normal / InProjectImprovement / CoreEvolution avec human-in-the-loop obligatoire)
Filelock + I/O fichier
Rich console avec panels CFL, plan stratégique, plan health
Robustesse erreurs JSON, timeout, session perdue


INSTRUCTION FINALE
Génère le système NEXUS V5.0 complet, fichier par fichier, prêt à tourner demain matin.
Commence immédiatement par la Phase 1 :

install.ps1
requirements.txt
nexus.py + nexus.ps1
core/synapse/protocol.py (Dual Schema)
core/tools/executor.py

Sois ambitieux. Sois paranoïaque. Sois implacable.
Construis le système multi-agent local le plus robuste jamais créé.
GO.