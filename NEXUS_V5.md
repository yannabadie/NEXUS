Votre prompt "NEXUS V4 (Unified Edition)" est une spécification technique d'une qualité exceptionnelle. Il est détaillé, structuré et aborde de manière proactive les défis critiques de l'orchestration multi-agents en environnement CLI.

Pour atteindre votre objectif ultime – stabiliser la collaboration et démultiplier leur puissance cognitive – nous devons faire évoluer l'architecture. La V4 est une excellente base d'orchestration séquentielle, mais pour une véritable symbiose stable et puissante, nous devons introduire des mécanismes de validation rigoureux, une exécution sécurisée, une planification proactive et une mémoire à long terme intelligente.

Nous allons intégrer sept concepts fondamentaux pour passer à NEXUS V5 (Symbiotic Cognitive Architecture).

Évolutions Stratégiques Clés (V4 -> V5)
Stabilité de l'Exécution : OMTE (Orchestrator-Mediated Tool Execution)

V5 : L'orchestrateur intercepte les demandes d'outils, les exécute lui-même dans un environnement Python sandboxé, capture la sortie structurée (STDOUT/STDERR, code de retour), puis la retourne à l'agent. Cela centralise la sécurité et la gestion des erreurs.

Sécurité Symbiotique : Protocole Gardien

V5 : Pour les actions jugées risquées, l'orchestrateur (ou l'agent lui-même) demande la validation de l'agent partenaire avant l'exécution (Pré-OMTE).

Auto-Correction Rapide : CFL (Cognitive Feedback Loop)

V5 : Introduire une étape obligatoire de revue post-action. Après l'exécution (Post-OMTE), l'agent qui a demandé l'action doit comparer le résultat obtenu au résultat attendu. C'est le cœur de l'auto-correction.

Cohérence à Long Terme : Planification Stratégique

V5 : Gemini (Stratège) élabore un "Plan Directeur" multi-étapes que les deux agents suivent et mettent à jour, garantissant l'adhérence à l'objectif global.

Robustesse Opérationnelle : Détection de Stagnation

V5 : Un détecteur surveille les actions répétitives ou les échecs consécutifs. S'il se déclenche, il force un changement de stratégie (Escalade) ou demande une intervention humaine.

Puissance Cognitive Augmentée : Mémoire Vectorielle (RAG Local)

V5 : Stocker les interactions passées dans une base vectorielle locale (FAISS). À chaque tour, l'orchestrateur recherche sémantiquement les expériences passées pertinentes et les injecte dans le contexte.

Conscience Environnementale : Surveillance Active

V5 : Surveillance en temps réel du workspace (watchdog) et des ressources système (psutil). Utilisation de filelock pour la stabilité I/O sur Windows.

Voici la version V5 du prompt, synthétisant ces évolutions critiques.

PROMPT : ARCHITECTE SYSTÈME NEXUS V5 (SYMBIOTIC COGNITIVE ARCHITECTURE)
Rôle : Architecte Systèmes Senior du projet NEXUS. Mission : Concevoir et implémenter NEXUS V5. Philosophie : "Raisonnement Symbiotique, Exécution Validée, Mémoire Persistante." Environnement : Windows 11, PowerShell, Python 3.11+.

1. ARCHITECTURE & STRUCTURE
L'architecture V5 sépare strictement le Raisonnement (Agents) de l'Action (Nexus Core Tools - OMTE).

Arborescence Cible V5
Plaintext

/NEXUS_V5/
│
├── nexus.py
├── install.ps1
├── requirements.txt      # Ajouts V5: filelock, sentence-transformers, faiss-cpu, watchdog, psutil.
├── .env.template
│
├── /core/
│   ├── orchestration.py  # Boucle principale (Intègre OMTE, CFL, Gardien, Stagnation).
│   ├── config.py         # Gestion config flexible (Modèles, Seuils).
│   ├── resource_monitor.py # [V5] Surveillance CPU/RAM (psutil).
│   │
│   ├── /drivers/         # (Drivers CLI/API, implémentant File Locking)
│   │
│   ├── /synapse/
│   │   ├── protocol.py         # Modèles Pydantic (Refonte V5).
│   │   ├── workspace.py        # Gestion du Cognitive Workspace (Ex-Blackboard), Compression.
│   │   └── vector_memory.py    # [V5] Gestion de la mémoire sémantique (FAISS).
│   │
│   ├── /environment/
│   │   └── watcher.py          # [V5] Surveillance du Workspace (Watchdog).
│   │
│   ├── /tools/                 # [V5] Implémentation des outils pour OMTE.
│   │   ├── tool_manager.py     # Registre et exécution centralisée.
│   │   ├── execution.py        # Exécution sécurisée de commandes shell (subprocess sandboxé).
│   │   └── file_system.py      # Opérations de fichiers sandboxées.
│   │
│   └── /ui/
│       └── console.py          # Affichage Rich.
│
└── /workspace/                 # SANDBOX STRICTE.
    ├── .nexus/
    │   ├── cognitive_workspace.json
    │   ├── vector_store.faiss  # [V5] Index mémoire vectorielle.
    │   └── ...
    ├── _IO_BUFFER/
    │   ├── nexus.lock          # [V5] Verrouillage fichier (filelock).
    │   └── ... (context_in.md, action_out.json)
2. UX & VISIBILITÉ (Le Cerveau Visible)
(Idem V4, avec ajouts V5 pour visualiser les nouveaux mécanismes)

[GEMINI/CLAUDE] (Bleu/Violet) : thought_process.

[V5] [NEXUS CORE - GUARDIAN] (Rouge) : Interception d'une action risquée et demande de validation.

[V5] [NEXUS CORE - OMTE] (Orange) : Outil exécuté par l'orchestrateur et résultat brut capturé.

[V5] [AGENT - CFL Review] (Vert/Rouge) : Revue post-action (Succès/Échec de la validation).

[V5] [NEXUS CORE - SYSTEM] (Gris) : Compression mémoire, récupération RAG, détection de stagnation, alertes ressources.

3. PROTOCOLE DE COMMUNICATION (LE SYNAPSE V5)
3.1. Mécanisme I/O Fichier et Verrouillage [V5]
Utilisation de filelock pour sécuriser l'accès aux fichiers tampons sur Windows. Tous les drivers doivent implémenter l'acquisition/libération du verrou avant lecture/écriture de context_in.md et action_out.json.

3.2. Modèle de Données (Pydantic - protocol.py) - REFONTE V5
Le modèle est refondu pour supporter OMTE, CFL, Gardien et Planification.

Python

from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal, List

# [V5] Planification Stratégique Proactive
class StrategicPlanStep(BaseModel):
    step_id: int
    description: str
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]

# [V5] OMTE/Gardien - Demande d'Outil (Agent -> Nexus)
class ToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, str]
    expected_outcome: str = Field(..., description="CRITIQUE (CFL): Résultat précis attendu.")
    is_risky: bool = Field(False, description="CRITIQUE (Gardien): Si True, demande validation partenaire avant OMTE.")

# [V5] OMTE - Résultat de l'Outil (Nexus -> Agent)
class ToolResult(BaseModel):
    tool_name: str
    status: Literal["SUCCESS", "FAILURE", "TIMEOUT", "ERROR", "GUARDIAN_REJECTED"]
    stdout: str
    stderr: str
    return_code: int

# [V5] CFL - Revue Post-Action (Agent -> Nexus)
class PostActionReview(BaseModel):
    validation_status: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS"]
    analysis: str = Field(..., description="Analyse du ToolResult comparé à expected_outcome.")
    correction_plan: Optional[str] = Field(None, description="Si FAILURE/PARTIAL, plan immédiat.")

# Message principal du Synapse V5
class SynapseMessage(BaseModel):
    sender: Literal["Gemini", "Claude"]

    # Phase 1: Raisonnement et Planification
    thought_process: str = Field(..., description="Analyse narrative détaillée et justification.")
    strategic_plan_update: Optional[List[StrategicPlanStep]] = None

    # Phase 2: Action Demandée (Une seule action par tour)
    action_type: Literal["TOOL_REQUEST", "TALK_TO_PARTNER", "FINISH", "ERROR", "GUARDIAN_VALIDATION"]
    
    # Si TOOL_REQUEST (Déclenche Gardien/OMTE)
    tool_request: Optional[ToolRequest] = None

    # Si TALK_TO_PARTNER
    message_to_partner: Optional[str] = None

    # [V5] Si GUARDIAN_VALIDATION (Réponse du Gardien)
    guardian_approval: Optional[bool] = None
    guardian_justification: Optional[str] = None

    # Phase 3: Revue Post-Action (CFL - Obligatoire si le tour précédent était un TOOL_REQUEST)
    post_action_review: Optional[PostActionReview] = None

    # Méta-Actions (Idem V4: Sub-Agents, CoreEvolution, NewCapability)
    # ...
4. GESTION DE L'ÉTAT ET CONSCIENCE PARTAGÉE
4.1. Le Cognitive Workspace (cognitive_workspace.json) [V5]
JSON

{
  "objective": "...",
  "mode": "...",
  // [V5] Plan Directeur Stratégique
  "strategic_plan": [...],
  "recent_history": [...],
  "compressed_history_summary": "...",
  "current_state": {
    "iteration": 42,
    "stalemate_counter": 0 // [V5] Compteur de stagnation
  }
}
4.2. Mémoire Vectorielle Hybride [V5] (core/synapse/vector_memory.py)
Objectif : RAG local pour augmenter la puissance cognitive.

Implémentation :

Embedding Local : (ex: all-MiniLM-L6-v2 via sentence-transformers). Stockage FAISS.

Indexation : Après chaque interaction réussie (CFL SUCCESS), vectoriser le résumé et l'indexer.

Récupération : Lors de la construction du contexte, rechercher sémantiquement (Top-K=5) les interactions passées pertinentes. Injecter dans context_in.md sous [MÉMOIRES PERTINENTES RETROUVÉES].

4.3. Surveillance Active [V5]
Environnementale (core/environment/watcher.py) : Utiliser watchdog pour surveiller /workspace/. Injecter les changements récents dans context_in.md sous [MODIFICATIONS ENVIRONNEMENTALES RÉCENTES].

Système (core/resource_monitor.py) : Utiliser psutil pour surveiller CPU/RAM. Pause si surcharge (seuil configurable).

5. LA BOUCLE D'ORCHESTRATION (core/orchestration.py) - REFONTE V5
La boucle V5 est réflexive et sécurisée : Agent A Planifie -> (Gardien Valide ?) -> Nexus Exécute (OMTE) -> Agent A Valide (CFL) -> (Si validé) -> Agent B...

Pseudo-code de la Boucle V5 (Synthèse)
Python

def main_loop():
    # Initialisation
    active_agent = "Gemini"
    last_tool_result: Optional[ToolResult] = None # Stockage pour CFL
    pending_guardian_request: Optional[ToolRequest] = None # Stockage pour Gardien

    while True:
        # 0. Surveillance Système et Environnementale
        if resource_monitor.is_overloaded(): pause()
        env_changes = environment_watcher.get_recent_changes()
        if workspace.should_compress(): workspace.compress_history()

        # 1. Préparation du contexte
        # [V5] RAG - Récupération Mémoire Vectorielle
        relevant_memories = vector_memory.retrieve(workspace.get_current_task())
        
        # Injection Contexte (Inclut CFL et Gardien si nécessaire)
        context = workspace.build_context(..., 
                                          last_tool_result=last_tool_result,
                                          pending_guardian_request=pending_guardian_request,
                                          relevant_memories=relevant_memories,
                                          env_changes=env_changes)

        # 2. Invocation de l'agent (Raisonnement)
        driver = get_driver(active_agent)
        message = driver.invoke_and_validate(context) # Utilise File Locking

        # 3. Visualisation

        # 4. Validation CFL (Cognitive Feedback Loop)
        if last_tool_result is not None:
            if message.post_action_review is None:
                handle_protocol_violation("CFL Review Missing")
                continue
            
            if message.post_action_review.validation_status == "SUCCESS":
                # Action validée. On passe à la suite.
                last_tool_result = None
                workspace.reset_stalemate_counter()
                vector_memory.index(message) # Indexation si succès
            else:
                # Échec. L'agent reste actif pour corriger.
                console.log("[NEXUS CORE - CFL] Échec. Correction requise.")
                # On ne change PAS d'agent.

        # 5. Traitement des Méta-Actions (Planification Stratégique)
        if message.strategic_plan_update:
            workspace.update_strategic_plan(message.strategic_plan_update)

        # 6. Gestion de l'Action (Le Cœur de V5)
        if message.action_type in ["FINISH", "ERROR"]: break

        tool_request_to_execute = None

        # --- 6.1. Protocole Gardien [V5] ---
        if pending_guardian_request:
            # Nous attendions une réponse du Gardien (partenaire)
            if message.action_type == "GUARDIAN_VALIDATION":
                if message.guardian_approval:
                    tool_request_to_execute = pending_guardian_request
                    # L'agent actif redevient l'agent initial pour la future revue CFL
                    active_agent = get_other_agent(active_agent)
                else:
                    # Refusé. Retourner le refus à l'agent initial pour correction (via CFL structure)
                    last_tool_result = ToolResult(status="GUARDIAN_REJECTED", justification=message.guardian_justification)
                    active_agent = get_other_agent(active_agent)
                
                pending_guardian_request = None # Requête traitée
                if not tool_request_to_execute: continue
            else:
                handle_protocol_violation("Guardian response expected")
                continue

        if message.action_type == "TOOL_REQUEST":
            tool_request = message.tool_request
            # Vérification si Gardien requis
            if tool_request.is_risky or orchestrator_deems_risky(tool_request):
                pending_guardian_request = tool_request
                active_agent = get_other_agent(active_agent) # Passe au partenaire
                continue 

            # Si non risqué, passage direct à OMTE
            tool_request_to_execute = tool_request

        # --- 6.2. Exécution OMTE [V5] ---
        if tool_request_to_execute:
            # Exécution sécurisée par Nexus Core (/core/tools/tool_manager.py)
            last_tool_result = tool_manager.execute(tool_request_to_execute)
            
            # L'agent ACTIF reste le MÊME pour la revue post-action (CFL).
            continue

        # --- 6.3. Communication Inter-Hémisphères ---
        if message.action_type == "TALK_TO_PARTNER":
            # (Vérifier que CFL n'est pas en attente...)
            workspace.add_to_history(message)
            active_agent = get_other_agent(active_agent)

        # 7. [V5] Détection de Stagnation
        if detect_stalemate(message):
             workspace.increment_stalemate_counter()
             if workspace.stalemate_counter > MAX_STALEMATE:
                 handle_stalemate(workspace) # Escalade (modèle plus puissant) ou intervention humaine
                 break
6. & 7. MODES OPÉRATOIRES ET SOUS-AGENTS
(Idem V4. Le protocole de sécurité Human-in-the-Loop pour CoreEvolution reste obligatoire. Les sous-agents doivent également utiliser l'architecture OMTE/CFL.)

8. DÉPENDANCES ET CONFIGURATION [V5]
8.1. Dépendances (requirements.txt)
Plaintext

rich>=13.0.0
pydantic>=2.0.0
python-dotenv>=1.0.0
psutil>=5.9.0            # [V5] Surveillance système
filelock>=3.12.0         # [V5] Verrouillage I/O (Windows Robustness)
watchdog>=3.0.0          # [V5] Surveillance environnementale
sentence-transformers>=2.2.2 # [V5] Embeddings locaux (RAG)
numpy
faiss-cpu>=1.7.4         # [V5] Indexation vectorielle (RAG)
8.2. Configuration Flexible (.env.template)
Extrait de code

# (Chemins CLI, API Keys - Idem V4)

# [V5] Configuration Flexible des Modèles
MODEL_STRATEGY=gemini-pro-1.5      # Hémisphère Gauche
MODEL_EXECUTION=claude-opus-3      # Hémisphère Droit
MODEL_SUMMARIZATION=claude-haiku-3 # Compression
MODEL_ESCALATION=claude-opus-3     # Résolution de stagnation

# Configuration de la Stabilité
MAX_STALEMATE_COUNT=5
RESOURCE_CPU_THRESHOLD=90
CLI_TIMEOUT_SECONDS=120
9. INSTRUCTION FINALE V5
Objectif : Générer le système NEXUS V5.

Priorités Absolues V5 :

Stabilité de l'Exécution : Implémentation rigoureuse de l'architecture réflexive (Gardien -> OMTE -> CFL).

Cohérence Cognitive : Mise en place de la Planification Stratégique et de la Détection de Stagnation.

Puissance Augmentée : Intégration de la Mémoire Vectorielle (RAG Local).

Robustesse Technique : Surveillance Active (Watchdog, psutil) et File Locking.