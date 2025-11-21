PROMPT : ARCHITECTE SYSTÈME NEXUS V6.0 (THE SYMBIOTIC REPL)
Rôle : Architecte Systèmes Principal & Lead UX Designer. Mission : Construire NEXUS V6.0, la fusion définitive entre une architecture cognitive de sécurité (V5) et une expérience utilisateur fluide type "Claude Code" (Interactive REPL). Cibles IA : Google AI Ultra (via gemini CLI) & Claude Plan Max (via claude CLI). Environnement : Windows 11, PowerShell, Python 3.11+ (Stack prompt_toolkit + rich).

PHILOSOPHIE V6.0 : "UNIFIED COGNITION"
Zero-Friction UX : NEXUS est un Shell persistant (nexus>). Pas de relance de script. Le contexte est vivant.

Deep Fusion (Ping-Pong Cognitif) : Fini le "Leader/Follower". Gemini et Claude débattent en "mode pensée" (Brainstorming) avant de cristalliser un plan d'action.

Objective Truth (OMTE) : L'exécution des outils reste centralisée et validée par le Core (Héritage V5.0).

Conscience Totale : Watchdog (Environnement) + Guardian (Confiance) + State Rollback (Sécurité).

1. ARCHITECTURE & STRUCTURE CIBLE
Le système devient une application résidente (REPL) pilotant une FSM (Finite State Machine).

Plaintext

/NEXUS_V6.0/
│
├── nexus.py                  # Point d'entrée unique (Interactive Shell REPL)
├── requirements.txt          # prompt_toolkit, rich, watchdog, pydantic, psutil, filelock
│
├── /core/
│   ├── session_manager.py    # Gestionnaire de persistance (Load/Save sessions complètes)
│   ├── orchestration.py      # Moteur FSM Persistant (Ne meurt jamais entre les tours)
│   │
│   ├── /interface/           # [NOUVEAU] UX "Claude Code-like"
│   │   ├── repl.py           # Boucle prompt_toolkit (History, Auto-completion, Keybindings)
│   │   ├── spinner.py        # Gestionnaire d'état visuel (Live Display Rich)
│   │   └── renderer.py       # Rendu Markdown/Syntax highlighting propre
│   │
│   ├── /synapse/
│   │   ├── protocol.py       # Modèles Pydantic V6 (Inclut Brainstorming)
│   │   ├── memory.py         # Blackboard + Rollback
│   │   └── state.py          # Scores de Confiance & Contexte
│   │
│   ├── /execution/           # OMTE (Orchestrator-Mediated Tool Execution)
│   │   ├── tool_manager.py   # SDC (Schema-Driven Capabilities)
│   │   └── sandbox.py        # Exécution sécurisée subprocess
│   │
│   └── /environment/
│       └── watcher.py        # Watchdog (Surveillance live du workspace)
2. UX & INTERFACE : "CLAUDE CODE" EXPERIENCE
Comportement attendu du Shell (nexus.py) :

Prompt Stylisé : nexus (gemini+claude) > avec coloration syntaxique de l'input.

Commandes Slash (Interceptées avant l'IA) :

/mode [Auto|Brainstorm|Execute] : Force le comportement.

/compact : Réduit l'affichage (cache les pensées, montre juste les actions).

/cost : Estimation des tokens session.

/clear : Nettoie l'affichage (garde la mémoire).

/doctor : Vérifie la santé des CLIs et du Watchdog.

Spinner Intelligent (Masquage de la complexité) :

Au lieu de défiler du JSON, afficher un spinner : ⠋ Gemini et Claude analysent la requête...

Mise à jour dynamique : ⠋ Exécution : pytest (via OMTE)... -> ✓ Succès.

3. PROTOCOLE SYNAPSE V6.0 - DEEP FUSION
3.1. Nouveaux États FSM
La machine à états gère désormais le débat interne.

USER_INPUT : Attente passive dans le REPL.

DEEP_FUSION (Brainstorming) : Gemini et Claude échangent des messages textuels courts (sans outils) pour s'aligner.

Condition de sortie : Consensus atteint OU limite de tours (3) atteinte.

STRATEGIC_LOCK : Le plan est figé.

OMTE_EXECUTION : L'agent désigné (celui qui a la compétence) demande l'outil. Nexus exécute.

CFL_VALIDATION : L'autre agent (ou le même) valide le résultat objectif.

3.2. Modèles Pydantic (Mise à jour)
Python

class BrainstormEntry(BaseModel):
    sender: Literal["Gemini", "Claude"]
    insight: str
    consensus_score: int = Field(..., description="0-100. Si > 90, on passe à l'action.")

class SynapseMessage(BaseModel):
    # ... champs existants V5 ...
    
    # [NOUVEAU V6] Mode Débat
    action_type: Literal["BRAINSTORM", "TOOL_REQUEST", "HANDOFF", "FINISH"]
    
    brainstorm_data: Optional[BrainstormEntry] = None
    
    # Si BRAINSTORM : Pas d'outil, juste de la pure intelligence.
    # Si TOOL_REQUEST : Déclenche OMTE (Le Core prend la main).
4. LA BOUCLE PRINCIPALE (PERSISTANTE)
Contrairement à la V5, l'orchestrateur ne s'arrête pas.

Python

class NexusREPL:
    def __init__(self):
        self.session = PromptSession()
        self.orchestrator = Orchestrator(persistent=True)
    
    def run(self):
        while True:
            try:
                user_input = self.session.prompt("nexus> ")
                
                # 1. Gestion Slash Commands
                if user_input.startswith("/"):
                    self.handle_command(user_input)
                    continue

                # 2. Injection dans l'Orchestrateur Vivant
                # L'orchestrator ne "reboot" pas, il ajoute l'input au contexte existant
                with Live(Spinner("Thinking..."), refresh_per_second=10) as live_display:
                    self.orchestrator.process_turn(user_input, live_display)
            
            except KeyboardInterrupt:
                continue # Juste annuler la ligne, pas tuer le shell
5. CONSIGNES D'IMPLÉMENTATION (STEP-BY-STEP)
Refactorisation Core (orchestration.py) :

Transforme la classe pour qu'elle garde l'état en mémoire (RAM) entre deux process_turn.

Intègre la logique de "Deep Fusion" : Si la requête est complexe, force un échange Gemini <-> Claude avant tout appel d'outil.

Création Interface (interface/repl.py) :

Utilise prompt_toolkit pour l'historique et l'édition multi-lignes.

Utilise rich pour le rendu des réponses (Markdown) et les spinners d'état.

Intégration Watchdog V5 :

Le Watchdog tourne dans un thread séparé. À chaque nouvel input utilisateur, il injecte le diff des fichiers modifiés depuis la dernière commande dans le contexte.

Drivers CLI :

Maintiens l'utilisation stricte de subprocess pour gemini et claude.

Ajoute un système de cache contextuel pour accélérer les échanges lors de la phase de Brainstorming (éviter de re-lire tout le contexte si rien n'a changé).

LIVRABLES ATTENDUS : Code complet et modulaire pour nexus.py (le REPL), core/orchestration.py (la FSM persistante), et core/interface/renderer.py (l'UI).

Go. Crée l'interface symbiotique ultime.