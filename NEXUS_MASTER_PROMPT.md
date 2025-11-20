# PROMPT : ARCHITECTE SYSTÈME NEXUS V4 (ULTIMATE EDITION)

**Rôle :** Tu es l'Architecte Systèmes Senior du projet NEXUS.
**Mission :** Concevoir et implémenter **NEXUS V4**, l'Orchestrateur Cognitif Symbiotique.
**Philosophie :** "Strategy at the Speed of Thought (Gemini), Execution with Surgical Precision (Claude)."
**Environnement :** Windows 11, PowerShell, Python 3.11+.
**Contrainte Absolue :** Utilisation exclusive des interfaces CLI existantes (`claude`, `gemini`) pilotées par Python (`subprocess`). Pas d'API Python directes.

---

## 1. ARCHITECTURE & STRUCTURE
Le système est un "Puppet Master" Python qui orchestre deux processus IA persistants.

**Arborescence Cible :**
```text
/NEXUS_V4/
│
├── nexus.py              # Point d'entrée (Wrapper CLI).
├── install.ps1           # Setup (Check CLI, venv, requirements).
├── requirements.txt      # rich, pydantic, python-dotenv, psutil.
├── .env.template         # Config (Chemins EXE, Session IDs).
│
├── /core/
│   ├── orchestration.py  # La "Boucle Infinie" (The Main Loop).
│   ├── config.py         # Gestion configuration.
│   │
│   ├── /drivers/
│   │   ├── cli_driver.py # Classe générique de pilotage CLI (I/O Files).
│   │   ├── gemini.py     # Driver spécifique Gemini CLI.
│   │   └── claude.py     # Driver spécifique Claude CLI (-p --dangerously-skip-permissions).
│   │
│   ├── /synapse/
│   │   ├── protocol.py   # Modèles Pydantic (Le langage commun).
│   │   ├── memory.py     # Gestionnaire de contexte (Blackboard -> .md).
│   │   └── state.py      # Gestionnaire d'état (Modes, History).
│   │
│   └── /ui/
│       └── console.py    # Affichage Rich (Panels Bleu/Violet).
│
└── /workspace/           # SANDBOX STRICTE pour les agents.
    ├── .nexus/           # Méta-données système.
    │   ├── blackboard.json    # Mémoire partagée.
    │   ├── capabilities.json  # Registre dynamique des outils.
    │   └── session.log        # Historique unifié.
    │
    ├── _IO_BUFFER/       # Zone tampon (Contournement limites Windows).
    │   ├── context_in.md      # Contexte complet injecté.
    │   ├── action_out.json    # Réponse brute de l'agent.
    │   └── tool_io.txt        # Sortie des outils exécutés.
    │
    └── EVOLUTION_VNEXT/  # Zone tampon pour le mode CoreEvolution.
```

## 2. UX & VISIBILITÉ (Le Cerveau Visible)
L'utilisateur lance `nexus "Objectif" --mode Normal`.
L'interface terminal (`rich`) doit afficher la symbiose :

*   **Header :** Mode, Token Usage, Session ID.
*   **[NEXUS CORE] (Gris) :** Logs système, erreurs.
*   **[GEMINI - Stratège] (Bleu/Cyan) :** Affiche `thought_process` (Réflexion stratégique).
*   **[CLAUDE - Exécutant] (Violet/Ambre) :** Affiche `thought_process` + `action_summary`.

## 3. PROTOCOLE DE COMMUNICATION (LE SYNAPSE)
Fiabilité critique. Tout passe par des fichiers pour éviter les limites de caractères CLI.

1.  **Injection :** Nexus écrit tout le contexte (System Prompt + Blackboard + Capabilities) dans `_IO_BUFFER/context_in.md`.
2.  **Invocation :** Nexus appelle le CLI :
    *   *Claude :* `claude -p "Lis context_in.md. Réponds en JSON dans action_out.json."`
    *   *Gemini :* `gemini "Lis context_in.md. Réponds en JSON." > action_out.json`
3.  **Validation :** Nexus lit `action_out.json` et valide avec Pydantic (`protocol.py`).

**Modèle de Données (Pydantic) :**
```python
class ThoughtChain(BaseModel):
    step: int
    reasoning: str

class NewCapability(BaseModel):
    name: str
    description: str
    invocation_method: str

class SubAgentRequest(BaseModel):
    objective: str
    context: str
    agent_model: Literal["Opus", "Haiku", "Gemini-Pro"]

class SynapseMessage(BaseModel):
    sender: Literal["Gemini", "Claude"]
    
    # Pensée Partagée
    thought_process: List[ThoughtChain]
    reflection: str # Auto-critique avant action
    
    # Action
    action_type: Literal["TALK", "TOOL_USE", "DELEGATE", "FINISH", "FAIL"]
    content: Optional[str]
    tool_use: Optional[ToolUse]
    
    # Méta-Actions (Traitées par Core)
    new_capability: Optional[NewCapability]
    request_sub_agent: Optional[SubAgentRequest]
    request_core_evolution: bool = False
```

## 4. LES TROIS MODES OPÉRATOIRES
L'orchestrateur adapte les permissions et le prompt système selon le `--mode`.

1.  **Normal :** Focus objectif utilisateur. Écriture restreinte à `/workspace/`.
2.  **InProjectImprovement :** Auto-analyse. Les agents scannent `session.log` et proposent des `NewCapability`.
3.  **CoreEvolution (DANGER) :**
    *   Nexus injecte son propre code source (`/core/*.py`) dans le contexte.
    *   Les agents proposent des refactorings.
    *   Les modifications sont écrites dans `/workspace/EVOLUTION_VNEXT/`.
    *   Nexus s'arrête et demande à l'utilisateur de valider/copier les fichiers. **Interdiction d'écraser à chaud.**

## 5. LIVRABLES ATTENDUS (BOOTSTRAP)
Génère le code pour démarrer maintenant.

1.  `install.ps1` : Script robuste (Check Python 3.11+, Check CLIs, venv, folders).
2.  `requirements.txt` : Les dépendances.
3.  `nexus.py` : Le point d'entrée.
4.  `core/synapse/protocol.py` : Le code Pydantic complet.
5.  `core/drivers/claude.py` : Le driver qui gère `--dangerously-skip-permissions`.

**Instruction Finale :** Sois robuste. Si un JSON est malformé, l'orchestrateur doit le détecter, logger l'erreur brute, et demander à l'agent de corriger. Pas de crash.