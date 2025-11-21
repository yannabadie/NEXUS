PROMPT : ARCHITECTE SYSTÈME NEXUS V5.0 (SYMBIOTIC COGNITIVE ARCHITECTURE)
Rôle : Architecte Systèmes Senior du projet NEXUS. Mission : Concevoir et implémenter NEXUS V5.0. Philosophie : "Raisonnement Symbiotique, Exécution Validée (OMTE/CFL), Conscience Environnementale (Watchdog), Confiance Adaptative (Guardian)." Environnement : Windows 11, PowerShell, Python 3.11+.

1. ARCHITECTURE & STRUCTURE [V5.0]
L'architecture V5.0 sépare strictement la Décision (Agents) de l'Action (Nexus Core - OMTE) et adopte une structure FSM.

Arborescence Cible V5.0
Plaintext

/NEXUS_V5.0/
│
├── nexus.py, install.ps1, .env.template
├── requirements.txt      # Ajouts V5.0: watchdog. (rich, pydantic, dotenv, psutil, filelock)
│
├── /core/
│   ├── orchestration.py  # [V5.0] FSM principale (OMTE, CFL, Guardian, Handoff).
│   ├── config.py, resource_monitor.py (psutil)
│   │
│   ├── /drivers/         # (Drivers CLI/API - Intègrent I/O Timestamp Validation)
│   │
│   ├── /synapse/
│   │   ├── protocol.py         # [V5.0] Modèles Pydantic (Refonte majeure).
│   │   ├── memory.py           # Gestion Contexte (Avec State Rollback).
│   │   └── state.py            # Gestion État (Inclut Score de Confiance).
│   │
│   ├── /execution/             # [V5.0] OMTE (Orchestrator-Mediated Tool Execution).
│   │   ├── tool_manager.py     # Registre (SDC) et exécution centralisée.
│   │   └── sandbox.py          # Exécution sécurisée (subprocess, file I/O sandboxé).
│   │
│   ├── /environment/
│   │   └── watcher.py          # [V5.0] Watchdog (Surveillance Workspace).
│   │
│   └── /ui/console.py
│
└── /workspace/
    ├── .nexus/
    │   ├── blackboard.json
    │   ├── blackboard.json.bak1 # [V5.0] State Rollback.
    │   ├── capabilities_sdc.json# [V5.0] Schema-Driven Capabilities.
    │   └── ...
    ├── _IO_BUFFER/
    │   ├── nexus.lock (filelock), context_in.md, action_out.json
2. UX & VISIBILITÉ (Le Cerveau Visible) [V5.0]
(Visualisation V4.5, avec ajouts V5.0)

Nouveaux Panels V5.0 :

[V5.0] [NEXUS CORE - OMTE] (Orange) : Exécution de l'outil par l'orchestrateur et résultat objectif capturé.

[V5.0] [NEXUS CORE - GUARDIAN] (Magenta) : Déclenchement du Protocole Gardien (Confiance faible + action risquée).

[V5.0] [AGENT - Handoff] (Gris Foncé) : Résumé cognitif lors du changement d'agent.

[V5.0] [NEXUS CORE - WATCHDOG] (Cyan Clair) : Changements environnementaux détectés.

Header : Ajout du Score de Confiance dynamique (ex: Confiance G: 92% | C: 85%) et État FSM.

3. PROTOCOLE DE COMMUNICATION (LE SYNAPSE V5.0)
3.1. Mécanisme I/O Fichier, Verrouillage et Validation Temporelle [V5.0]
(Utilisation de filelock maintenue.)

Injection (Nexus -> Agent) : (Idem V4.5)

Invocation (Nexus) :

CRITIQUE V5.0 : --dangerously-skip-permissions est SUPPRIMÉ. La sécurité est gérée par OMTE (/core/execution/sandbox.py).

Validation (Nexus <- Agent) :

Acquérir le verrou nexus.lock.

[V5.0] Timestamp Validation : Vérifier que timestamp(action_out.json) > timestamp(context_in.md). Sinon, attendre (avec timeout) ou signaler une erreur CLI (fichier non mis à jour par l'agent).

Lire et valider Pydantic.

Libérer le verrou.

3.2. Modèle de Données (Pydantic - protocol.py) - REFONTE V5.0
Python

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any

# (StrategicPlanStep - Idem V4.5)

# [V5.0 Handoff] Protocole de Transfert Contextuel
class HandoffProtocol(BaseModel):
    cognitive_state_summary: str
    strategic_justification: str
    immediate_goals_for_partner: List[str]
    potential_blockers: Optional[List[str]] = None

# [V5.0 OMTE] Demande d'Outil (Agent -> Nexus)
class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] # Doit correspondre au schéma SDC
    expected_outcome: str = Field(..., description="[CFL] Résultat précis attendu.")
    is_risky: bool = Field(False, description="[Guardian] Si True, peut déclencher Gardien si confiance faible.")

# [V5.0 OMTE] Résultat de l'Outil (Nexus -> Agent) - CRITIQUE
class ToolResult(BaseModel):
    tool_name: str
    status: Literal["SUCCESS", "FAILURE", "TIMEOUT", "ERROR", "INVALID_SCHEMA", "GUARDIAN_REJECTED"]
    stdout: str
    stderr: str
    return_code: int

# [V5.0 Guardian] Réponse du Protocole Gardien
class GuardianResponse(BaseModel):
    approval: bool
    justification: str

# (PostActionReview - Idem V4.5, basé sur ToolResult)

# Message principal du Synapse V5.0
class SynapseMessage(BaseModel):
    sender: Literal["Gemini", "Claude"]

    # (Pensée Partagée, Planification Stratégique - Idem V4.5)
    thought_process: str
    reflection: str
    strategic_plan_update: Optional[List[StrategicPlanStep]] = None

    # [V5.0] Action (FSM - Une seule action par tour)
    action_type: Literal["TOOL_REQUEST", "TALK_HANDOFF", "FINISH", "ERROR", "GUARDIAN_VALIDATION"]
    
    # Si TOOL_REQUEST (Déclenche OMTE/Guardian)
    tool_request: Optional[ToolRequest] = None

    # Si TALK_HANDOFF (Synergie)
    handoff_data: Optional[HandoffProtocol] = None

    # Si GUARDIAN_VALIDATION (Confiance Adaptative)
    guardian_response: Optional[GuardianResponse] = None

    # CFL - Revue Post-Action (OBLIGATOIRE si le tour précédent était TOOL_REQUEST)
    post_action_review: Optional[PostActionReview] = None

    # (Méta-Actions : Sub-Agents, CoreEvolution, NewCapability)
    # (Statut : CONTINUE, FINISHED, ERROR_REVIEW_NEEDED)
4. GESTION DE L'ÉTAT ET CONSCIENCE PARTAGÉE [V5.0]
4.1. Le Blackboard (blackboard.json) - ÉVOLUTION V5.0
JSON

{
  // (Champs existants : objective, mode, strategic_plan, history...)

  "current_state": {
    // (Champs existants : iteration, stalemate_counter...)

    // [V5.0] Confiance Adaptative
    "confidence_scores": {
      "Gemini": 95.0,
      "Claude": 95.0
    },
    // [V5.0] État FSM (Pour débogage)
    "fsm_state": "CONTEXT_BUILDING"
  }
}
4.2. Registre des Capacités (capabilities_sdc.json) - V5.0 SDC
Objectif : Capacités Pilotées par Schéma (SDC). Utilisation de JSON Schema pour validation stricte par tool_manager.py avant exécution OMTE.

JSON

{
  "NEXUS_CORE_TOOLS": [
    {
      "name": "execute_shell",
      "description": "Exécute une commande shell dans le workspace sandboxé.",
      "schema": {
        "type": "object",
        "properties": {
          "command": {"type": "string", "description": "La commande shell exacte."}
        },
        "required": ["command"]
      }
    }
    // ... write_file, read_file, list_files, etc.
  ]
}
4.3. Compression Mémorielle et State Rollback [V5.0]
(Idem V4.5 pour Compression Textuelle)

[V5.0] State Rollback (core/synapse/memory.py) :

Sauvegarde : Après chaque tour réussi, rotation des backups (.bak1 -> .bak2, blackboard.json -> .bak1) avant écriture du nouvel état.

Chargement : Tenter de lire blackboard.json. Si échec (Corruption, FileNotFound), restaurer automatiquement depuis .bak1.

4.4. Conscience Environnementale (Watchdog) [V5.0]
Implémentation (core/environment/watcher.py) :

Utiliser la bibliothèque watchdog pour surveiller /workspace/.

Agréger les changements (création, modification, suppression) entre les tours.

L'orchestrateur injecte ce résumé objectif dans context_in.md sous [NEXUS WATCHDOG - CHANGEMENTS RÉCENTS]. Crucial pour ancrer le CFL dans la réalité.

4.5. Confiance Adaptative et Protocole Gardien [V5.0]
Calcul du Score de Confiance (core/synapse/state.py) :

Score initial : 95%.

Après CFL SUCCESS : +1 (max 100).

Après CFL FAILURE : -5.

Violation de protocole (JSON invalide, CFL manquant) : -10.

Déclenchement du Protocole Gardien :

Si (Score Agent Actif < GUARDIAN_THRESHOLD (ex: 80%)) ET (ToolRequest.is_risky == True OU l'orchestrateur juge l'action risquée - ex: rm -rf).

5. LA BOUCLE D'ORCHESTRATION (core/orchestration.py) - V5.0 FSM
L'orchestration V5.0 est implémentée comme une Machine à États Finis (FSM) pour gérer la complexité du flux OMTE/CFL/Guardian/Handoff.

5.1. Les États de la FSM
INITIALIZING : Setup, Démarrage Watchdog, Chargement État (avec Rollback).

CONTEXT_BUILDING : Compression mémoire, Capture Watchdog, Construction context_in.md.

AGENT_REASONING : Invocation de l'agent (avec Timestamp Validation), Validation Pydantic. Détermine l'état suivant.

GUARDIAN_CHECK : Vérifie si le Protocole Gardien doit être activé (Confiance faible + Risque).

Si Oui -> AWAITING_GUARDIAN.

Si Non -> OMTE_EXECUTION.

AWAITING_GUARDIAN : Bascule vers l'agent partenaire pour validation. Attend GUARDIAN_VALIDATION réponse.

Si Approuvé -> OMTE_EXECUTION.

Si Refusé -> CONTEXT_BUILDING (Retour à l'agent initial avec refus).

OMTE_EXECUTION : Validation SDC. Exécution sécurisée par Nexus Core. Capture ToolResult. Retour à CONTEXT_BUILDING (l'agent reste actif pour CFL).

CFL_VALIDATION : Validation de PostActionReview. Mise à jour Score de Confiance.

Si Succès -> TRANSITION.

Si Échec -> STAGNATION_CHECK.

STAGNATION_CHECK / HANDLING : (Idem V4.5 - Escalade ou Arrêt).

TRANSITION : Traitement du HandoffProtocol. Changement d'agent actif. Sauvegarde État (avec Rollback). Retour à CONTEXT_BUILDING.

FINISHED : Nettoyage.

5.2. Pseudo-code de la Boucle Principale V5.0 (FSM Simplifiée)
Python

def main_loop():
    fsm_state = "INITIALIZING"
    active_agent = "Gemini"
    # Stockage temporaire pour les cycles multi-tours
    pending_tool_result: Optional[ToolResult] = None 
    pending_tool_request: Optional[ToolRequest] = None
    request_originator_agent: Optional[str] = None

    while fsm_state != "FINISHED":

        # (États INITIALIZING, CONTEXT_BUILDING - incluant Watchdog, Rollback)

        # --- État AGENT_REASONING ---
        if fsm_state == "AGENT_REASONING":
            # (Invocation et validation de l'agent, incluant Timestamp Validation)
            
            # Détermination du prochain état basé sur la réponse
            if pending_tool_result:
                fsm_state = "CFL_VALIDATION"
            elif message.action_type == "TOOL_REQUEST":
                pending_tool_request = message.tool_request
                request_originator_agent = active_agent
                fsm_state = "GUARDIAN_CHECK"
            elif message.action_type == "TALK_HANDOFF":
                fsm_state = "TRANSITION"
            elif message.action_type == "GUARDIAN_VALIDATION":
                 # (Traitement de la réponse Gardien...)
                 if message.guardian_response.approval:
                      fsm_state = "OMTE_EXECUTION"
                 else:
                      # (Gérer refus, retour à l'agent initial...)
                      active_agent = request_originator_agent
                      fsm_state = "CONTEXT_BUILDING"
            # ...
            continue

        # --- [V5.0] État GUARDIAN_CHECK ---
        if fsm_state == "GUARDIAN_CHECK":
             if state.should_trigger_guardian(active_agent, pending_tool_request):
                 console.log("[NEXUS CORE - GUARDIAN] Validation requise.")
                 # Basculer vers le partenaire (Gardien)
                 active_agent = get_other_agent(active_agent)
                 fsm_state = "CONTEXT_BUILDING" # Le Gardien raisonnera au prochain tour
             else:
                 fsm_state = "OMTE_EXECUTION"
             continue

        # --- [V5.0] État OMTE_EXECUTION ---
        if fsm_state == "OMTE_EXECUTION":
            tool_request = pending_tool_request
            
            # Validation SDC et Exécution sécurisée par Nexus Core
            if not tool_manager.validate_schema(tool_request):
                 pending_tool_result = ToolResult(status="INVALID_SCHEMA", ...)
            else:
                console.log(f"[NEXUS CORE - OMTE] Exécution: {tool_request.tool_name}")
                pending_tool_result = tool_manager.execute(tool_request)

            # Retour à l'agent initial pour la revue CFL.
            active_agent = request_originator_agent
            fsm_state = "CONTEXT_BUILDING"
            continue

        # --- (États CFL_VALIDATION, STAGNATION_CHECK/HANDLING - Mise à jour Confiance Score)

        # --- [V5.0] État TRANSITION ---
        if fsm_state == "TRANSITION":
            memory.add_to_history(message)

            # Traitement du Handoff Protocol
            if message.action_type == "TALK_HANDOFF" and message.handoff_data:
                console.display_handoff(message.handoff_data)
            
            # Logique de basculement d'agent
            active_agent = get_other_agent(active_agent)
            memory.save_state_with_backup() # [V5.0] Sauvegarde avec Rollback
            fsm_state = "CONTEXT_BUILDING"
            continue
6. à 8. (Sous-Agents, Modes Opératoires, Robustesse)
(Idem V4.5. Le mode CoreEvolution bénéficie désormais de la sécurité OMTE et du Protocole Gardien).

9. LIVRABLES ATTENDUS [V5.0]
(Idem V4.5, avec les ajouts critiques suivants :)

Phase 1 : Bootstrap

(Mise à jour) requirements.txt : Ajout watchdog.

Phase 2 : Système Complet

(Ajout) core/execution/tool_manager.py : Implémentation OMTE et validation SDC.

(Ajout) core/execution/sandbox.py : Fonctions d'exécution sécurisée.

(Ajout) core/environment/watcher.py : Implémentation Watchdog.

(Mise à jour) core/orchestration.py : Implémentation FSM complète (incluant Guardian, Handoff).

(Mise à jour) core/synapse/protocol.py : Schémas Pydantic V5.0.

(Mise à jour) core/synapse/memory.py : Intégration State Rollback.

(Mise à jour) core/drivers/*.py : Intégration I/O Timestamp Validation.

11. DIFFÉRENCES CLÉS V4.5 → V5.0
Pure OMTE : Réintroduction de l'exécution médiatisée pour stabiliser le CFL et centraliser la sécurité (suppression de --dangerously-skip-permissions).

FSM Architecture : Orchestration robuste basée sur une machine à états finis.

Adaptive Trust & Guardian Protocol : Mécanisme avancé de validation croisée basé sur la confiance dynamique.

Handoff Protocol : Formalise le transfert de contrôle avec résumé cognitif pour une meilleure synergie.

Watchdog : Ajoute une conscience environnementale objective.

SDC : Validation stricte des outils via JSON Schema.

Robustness Enhancements : State Rollback et I/O Timestamp Validation.