# PROMPT : ARCHITECTE SYSTÈME NEXUS V4 (UNIFIED EDITION)

**Rôle :** Tu es l'Architecte Systèmes Senior du projet NEXUS.
**Mission :** Concevoir et implémenter **NEXUS V4**, l'Orchestrateur Cognitif Symbiotique.
**Philosophie :** "Strategy at the Speed of Thought (Gemini), Execution with Surgical Precision (Claude)."
**Environnement :** Windows 11, PowerShell, Python 3.11+.
**Contrainte Technique :** Communication privilégiée via CLI (`claude`, `gemini`) avec fallback API Python si disponible et nécessaire.

---

## 1. ARCHITECTURE & STRUCTURE

Le système est un "Puppet Master" Python qui orchestre deux processus IA persistants en symbiose.

### Arborescence Cible

```text
/NEXUS_V4/
│
├── nexus.py              # Point d'entrée (Wrapper CLI).
├── install.ps1           # Setup (Check CLI, venv, requirements, PATH).
├── requirements.txt      # rich, pydantic, python-dotenv, psutil.
├── .env.template         # Config (Chemins EXE, Session IDs, API Keys optionnelles).
│
├── /core/
│   ├── orchestration.py  # La "Boucle Infinie" (The Main Loop).
│   ├── config.py         # Gestion configuration (.env + validation).
│   │
│   ├── /drivers/
│   │   ├── cli_driver.py       # Classe abstraite de pilotage (BaseDriver).
│   │   ├── gemini_driver.py    # Driver spécifique Gemini CLI/API.
│   │   └── claude_driver.py    # Driver spécifique Claude CLI (-p --dangerously-skip-permissions).
│   │
│   ├── /synapse/
│   │   ├── protocol.py         # Modèles Pydantic (Le langage commun).
│   │   ├── memory.py           # Gestionnaire de contexte (Blackboard, Compression).
│   │   └── state.py            # Gestionnaire d'état (Modes, History, Capabilities).
│   │
│   └── /ui/
│       └── console.py          # Affichage Rich (Panels Bleu/Violet).
│
├── /prompts/
│   ├── system_gemini_base.md   # Prompt système de base pour Gemini.
│   ├── system_claude_base.md   # Prompt système de base pour Claude.
│   └── summarization.md        # Template de résumé pour compression mémorielle.
│
└── /workspace/                 # SANDBOX STRICTE pour les agents.
    ├── .nexus/                 # Méta-données système.
    │   ├── blackboard.json     # Mémoire partagée (objectif, état, historique récent).
    │   ├── capabilities.json   # Registre dynamique des outils (Conscience Mutuelle).
    │   ├── session.log         # Historique unifié complet.
    │   └── EVOLUTION_VNEXT/    # Zone tampon pour le mode CoreEvolution.
    │
    ├── _IO_BUFFER/             # Zone tampon (Contournement limites Windows).
    │   ├── context_in.md       # Contexte complet injecté.
    │   ├── action_out.json     # Réponse brute de l'agent.
    │   └── tool_io.txt         # Sortie des outils exécutés.
    │
    └── _SUB_AGENT_<ID>/        # Dossiers temporaires pour sous-agents.
```

---

## 2. UX & VISIBILITÉ (Le Cerveau Visible)

### 2.1. Exécution Transparente

L'utilisateur lance : `nexus "Objectif" --mode Normal`

**Implémentation :**
- `install.ps1` doit créer un script wrapper (`nexus.ps1`) et l'ajouter au PATH de l'utilisateur.
- Ce wrapper appelle `python3 /path/to/nexus.py [arguments]`.

### 2.2. Visualisation Temps Réel (Rich Console)

L'interface terminal (`core/ui/console.py`) doit afficher la symbiose cognitive :

- **[NEXUS CORE] (Gris)** : Logs système, erreurs, changements d'état, compression mémorielle.
- **[GEMINI - Stratège] (Bleu/Cyan)** : Affiche `thought_process` (Réflexion stratégique) + `reflection`.
- **[CLAUDE - Exécutant] (Violet/Ambre)** : Affiche `thought_process` + `reflection` + `action_summary`.

**Éléments visuels :**
- Header : Mode actif, Token Usage estimé, Session ID.
- Panels `rich.panel` avec couleurs et emojis optionnels.
- Progress bars pour les tâches longues (compilation, analyse).

---

## 3. PROTOCOLE DE COMMUNICATION (LE SYNAPSE)

Fiabilité critique. Tout passe par des fichiers pour éviter les limites de caractères CLI (~8000 sur Windows).

### 3.1. Mécanisme I/O Fichier

1. **Injection :** Nexus écrit tout le contexte (System Prompt + Blackboard + Capabilities + History récent) dans `_IO_BUFFER/context_in.md`.
2. **Invocation :** Nexus appelle le CLI avec un prompt standardisé :
   - **Claude :** `claude -p --dangerously-skip-permissions --resume <SESSION_ID> "Lis context_in.md. Réponds STRICTEMENT en JSON (Protocole Synapse V1) dans action_out.json."`
   - **Gemini :** `gemini "Lis context_in.md. Réponds en JSON (Protocole Synapse V1)." > action_out.json`
3. **Validation :** Nexus lit `action_out.json` et valide avec Pydantic (`core/synapse/protocol.py`).
   - Si malformé : Logger l'erreur brute, demander à l'agent de corriger (max 3 tentatives).
   - Si échec après 3 tentatives : Basculer sur l'autre agent ou escalader à l'utilisateur.

### 3.2. Modèle de Données (Pydantic - protocol.py)

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal

# Structuration de la pensée
class ThoughtChain(BaseModel):
    step: int
    reasoning: str

# Utilisation d'outil
class ToolUse(BaseModel):
    tool_name: str
    arguments: Dict[str, str]

# Évolution des capacités
class NewCapability(BaseModel):
    name: str
    description: str
    invocation_method: str  # Comment le partenaire l'utilise.
    agent_owner: Literal["Gemini", "Claude"]  # Qui possède cet outil.

# Gestion des Sous-Agents
class SubAgentRequest(BaseModel):
    objective: str
    context: str
    agent_model: Literal["Opus", "Haiku", "Gemini-Pro", "Gemini-Flash"]
    expected_output: str  # Description de ce que le sous-agent doit retourner.

# Message principal du Synapse
class SynapseMessage(BaseModel):
    sender: Literal["Gemini", "Claude"]

    # Pensée Partagée (Transparence cognitive)
    thought_process: List[ThoughtChain] = Field(..., description="Chaîne de raisonnement structurée.")
    reflection: str = Field(..., description="Auto-critique avant action. Analyse des risques et validations.")

    # Action
    action_type: Literal["TALK", "TOOL_USE", "DELEGATE", "FINISH", "ERROR", "CONTINUE"]
    action_summary: str = Field(..., description="Résumé de l'action effectuée ou planifiée.")
    content: Optional[str] = None  # Message textuel ou résultat.
    tool_use: Optional[ToolUse] = None

    # Coordination Inter-Agents (CRITIQUE - RESTAURÉ)
    next_agent: Literal["Gemini", "Claude", "NexusCore"]
    instructions_for_next: str = Field(..., description="Instructions explicites pour l'agent suivant.")

    # Méta-Actions (Traitées par NexusCore)
    new_capability: Optional[NewCapability] = None
    request_sub_agent: Optional[SubAgentRequest] = None
    request_core_evolution: bool = False

    # Statut
    status: Literal["CONTINUE", "FINISHED", "ERROR_REVIEW_NEEDED"]
```

---

## 4. GESTION DE L'ÉTAT ET CONSCIENCE PARTAGÉE

### 4.1. Le Blackboard (blackboard.json)

Géré par `core/synapse/memory.py`.

**Contenu :**
```json
{
  "objective": "Objectif global de l'utilisateur",
  "mode": "Normal | InProjectImprovement | CoreEvolution",
  "recent_history": [
    {"agent": "Gemini", "timestamp": "...", "summary": "..."}
  ],
  "compressed_history_summary": "Résumé des 500 premiers tours...",
  "current_state": {
    "active_agent": "Claude",
    "iteration": 42,
    "token_count_estimate": 85000
  }
}
```

### 4.2. Registre des Capacités (capabilities.json)

**La Conscience Mutuelle** - Chaque agent connaît ses outils ET ceux de son partenaire.

**Contenu Initial :**
```json
{
  "Gemini": [
    {
      "name": "WebSearch",
      "description": "Recherche web via Google Search API",
      "invocation_method": "Mentionner 'WebSearch(query)' dans ton action"
    }
  ],
  "Claude": [
    {
      "name": "BashExecution",
      "description": "Exécuter commandes shell via --dangerously-skip-permissions",
      "invocation_method": "Utiliser tool_use avec tool_name='bash'"
    }
  ]
}
```

**Évolution Dynamique :**
- Si un agent retourne `new_capability`, l'orchestrateur l'ajoute au registre.
- Le registre est injecté dans `context_in.md` à chaque tour.

### 4.3. Compression Mémorielle (RESTAURÉ - CRITIQUE)

**Problème :** Les sessions longues saturent le contexte (limite ~200k tokens).

**Solution :** Gestion automatique par `core/synapse/memory.py`.

**Déclenchement :**
- Seuil configurable (ex: `blackboard.json` > 100k tokens estimés).
- Déclenchement manuel via Mode InProjectImprovement.

**Procédure :**
1. Détecter le dépassement du seuil.
2. Extraire l'historique ancien (tous sauf les N derniers tours, ex: N=50).
3. Lancer une tâche de résumé :
   - Agent : Opus (meilleure compréhension) ou Gemini-Pro (si coût est critique).
   - Prompt : `prompts/summarization.md` (template structuré).
   - Input : Historique brut à résumer.
   - Output : Résumé synthétique (max 5000 tokens).
4. Mettre à jour `blackboard.json` :
   - Remplacer l'historique ancien par le résumé.
   - Conserver les N derniers tours en brut.
5. Logger l'opération dans `session.log`.

**Exemple de Prompt de Résumé (`prompts/summarization.md`) :**
```markdown
Tu es un agent de compression mémorielle pour NEXUS.

Analyse l'historique d'interactions suivant et génère un résumé structuré :

**Format de sortie (JSON) :**
{
  "key_decisions": ["Décision 1", "Décision 2"],
  "tools_created": ["Nom outil 1", "Nom outil 2"],
  "objectives_completed": ["Objectif 1"],
  "current_blockers": ["Blocage potentiel"],
  "summary_narrative": "Résumé en 2-3 paragraphes..."
}

**Historique à résumer :**
[HISTORIQUE BRUT ICI]
```

---

## 5. LA BOUCLE D'ORCHESTRATION (core/orchestration.py)

### Pseudo-code de la Boucle Principale

```python
def main_loop():
    # Initialisation
    config = load_config()
    state = StateManager()
    memory = MemoryManager()
    gemini_driver = GeminiDriver(config)
    claude_driver = ClaudeDriver(config)

    active_agent = "Gemini"  # Démarrage par le stratège.

    while True:
        # 1. Préparation du contexte
        if memory.should_compress():
            console.log("[NEXUS CORE] Compression mémorielle déclenchée...")
            memory.compress_history()

        context = memory.build_context(
            system_prompt=get_system_prompt(active_agent),
            blackboard=memory.get_blackboard(),
            capabilities=state.get_capabilities()
        )

        # 2. Invocation de l'agent
        driver = gemini_driver if active_agent == "Gemini" else claude_driver
        response_json = driver.invoke(context)

        # 3. Validation
        try:
            message = SynapseMessage.parse_obj(response_json)
        except ValidationError as e:
            handle_malformed_response(driver, e)  # Max 3 tentatives.
            continue

        # 4. Visualisation
        console.display_thought_process(message, active_agent)

        # 5. Traitement des Méta-Actions
        if message.new_capability:
            state.register_capability(message.new_capability)

        if message.request_sub_agent:
            result = execute_sub_agent(message.request_sub_agent)
            memory.add_sub_agent_result(result)

        if message.request_core_evolution:
            handle_core_evolution(message)

        # 6. Mise à jour de l'état
        memory.add_to_history(message)

        # 7. Condition de sortie
        if message.status == "FINISHED":
            console.log("[NEXUS CORE] Objectif atteint. Fin de session.")
            break

        if message.status == "ERROR_REVIEW_NEEDED":
            console.log("[NEXUS CORE] Erreur critique. Revue requise.")
            break

        # 8. Transition vers l'agent suivant
        active_agent = message.next_agent
```

---

## 6. FONCTIONNALITÉ AVANCÉE : GESTION DES SOUS-AGENTS (RESTAURÉ)

**Objectif :** Permettre à un agent de déléguer une tâche complexe isolée à un sous-agent spécialisé.

### Protocole d'Exécution

Lorsqu'un agent retourne `request_sub_agent` :

1. **Pause :** Mettre en pause la boucle principale Gemini/Claude.
2. **Isolation :** Créer un répertoire de travail temporaire : `workspace/_SUB_AGENT_TASK_<UUID>/`.
3. **Configuration :**
   - Copier les capacités nécessaires depuis le registre principal.
   - Créer un blackboard dédié avec l'objectif du sous-agent.
4. **Exécution :**
   - Instancier un driver pour le modèle spécifié (`agent_model`).
   - Exécuter une boucle simplifiée (1 à N tours, max 10 tours ou timeout 5 min).
   - Capturer la sortie finale.
5. **Capture :**
   - Lire le résultat final du sous-agent.
   - Extraire les informations pertinentes selon `expected_output`.
6. **Reprise :**
   - Intégrer le résultat dans le blackboard principal.
   - Reprendre la boucle principale en fournissant le résultat à l'agent indiqué dans `next_agent`.
7. **Nettoyage :**
   - Optionnel : Archiver le dossier du sous-agent dans `.nexus/sub_agent_archives/`.

### Exemple d'Usage

**Gemini :**
```json
{
  "request_sub_agent": {
    "objective": "Analyse la performance du module XYZ et propose des optimisations.",
    "context": "Le code est dans workspace/modules/xyz.py. Utilise des benchmarks.",
    "agent_model": "Claude-Opus",
    "expected_output": "Un rapport JSON avec time_before, time_after, et code_changes."
  },
  "next_agent": "Claude",
  "instructions_for_next": "Implémente les optimisations suggérées par le sous-agent."
}
```

---

## 7. LES TROIS MODES OPÉRATOIRES

L'orchestrateur adapte les permissions et le prompt système selon `--mode`.

### 7.1. Mode Normal (Normal)

**Focus :** Accomplir l'objectif utilisateur.

**Permissions :**
- Écriture strictement limitée à `/workspace/` (hors `.nexus/`).
- Lecture complète du workspace.

**System Prompt Additions :**
- "Ton objectif est : [OBJECTIF UTILISATEUR]"
- "Tu travailles en symbiose avec [PARTENAIRE]. Communique tes intentions via next_agent."

### 7.2. Mode Auto-Amélioration Projet (InProjectImprovement)

**Focus :** Améliorer l'efficacité du projet en cours.

**Déclenchement :**
- Périodique (ex: toutes les 20 itérations).
- Après un échec/erreur récurrente.
- Manuellement par l'utilisateur.

**System Prompt Additions :**
- "Analyse session.log. Identifie les patterns d'échec, les inefficacités répétées."
- "Propose des new_capability pour automatiser des tâches répétitives."
- "Suggère des améliorations aux prompts système ou à la stratégie de collaboration."

**Permissions :**
- Identiques au Mode Normal.
- Accès en lecture à `session.log` complet.

### 7.3. Mode Évolution du Cœur (CoreEvolution) - SÉCURITÉ CRITIQUE

**Focus :** Réécrire le code source de l'orchestrateur lui-même.

**Procédure :**

1. **Injection du Code Source :**
   - Nexus lit son propre code (`/core/*.py`, `nexus.py`).
   - Injecte le code dans `context_in.md` avec marqueurs clairs.

2. **Analyse et Proposition :**
   - Les agents analysent le code source.
   - Proposent des réécritures, optimisations, nouvelles fonctionnalités.
   - Un agent doit explicitement mettre `request_core_evolution: True`.

3. **Exécution Isolée (SÉCURITÉ ABSOLUE) :**
   - **INTERDICTION ABSOLUE** d'écraser les fichiers Python en cours d'exécution.
   - Toutes les modifications DOIVENT être écrites dans : `workspace/.nexus/EVOLUTION_VNEXT/`.
   - Structure respectée : `EVOLUTION_VNEXT/core/orchestration.py`, etc.

4. **Validation Humaine (Human-in-the-Loop OBLIGATOIRE) :**
   - Une fois l'écriture terminée, l'orchestrateur passe `status: FINISHED`.
   - Affichage terminal :
     ```
     [NEXUS CORE] 🚨 ÉVOLUTION DU CŒUR GÉNÉRÉE 🚨

     Une nouvelle version de Nexus a été créée dans :
     workspace/.nexus/EVOLUTION_VNEXT/

     ACTIONS REQUISES :
     1. Réviser le code manuellement.
     2. Tester dans un environnement isolé.
     3. Si approuvé, copier manuellement les fichiers vers /core/.
     4. Redémarrer Nexus.

     ⚠️ NE JAMAIS copier sans révision. Le système est arrêté.
     ```
   - L'orchestrateur s'arrête immédiatement.

**System Prompt Additions :**
- "Tu as accès au code source de Nexus. Analyse-le avec un esprit critique."
- "Identifie les bugs, les inefficacités, les fonctionnalités manquantes."
- "Propose des réécritures complètes si nécessaire."
- "IMPORTANT : Toute modification doit aller dans EVOLUTION_VNEXT/. Ne jamais toucher /core/ directement."

---

## 8. ROBUSTESSE ET GESTION DES ERREURS

### 8.1. JSON Malformé

**Problème :** L'agent retourne un JSON invalide ou incomplet.

**Procédure :**
1. Logger l'erreur brute dans `session.log` avec le contenu complet de `action_out.json`.
2. Injecter un message d'erreur dans `context_in.md` :
   ```
   [ERREUR NEXUS] Le JSON retourné est invalide.

   Erreur Pydantic : [DÉTAILS]

   JSON brut reçu :
   [CONTENU]

   Corrige le fichier action_out.json. Tentative 1/3.
   ```
3. Réinvoquer l'agent.
4. Si échec après 3 tentatives : Basculer sur l'autre agent ou escalader à l'utilisateur.

### 8.2. Timeout CLI

**Problème :** Le processus CLI ne répond pas (freeze, crash).

**Procédure :**
1. Timeout configuré (ex: 120 secondes par défaut, ajustable).
2. Tuer le processus (`psutil.Process.terminate()`).
3. Logger l'incident.
4. Tenter un redémarrage de la session CLI.
5. Si échec répété (3 fois) : Basculer sur API Python si disponible.

### 8.3. Perte de Session CLI

**Problème :** La session Claude (identifiée par `--resume <SESSION_ID>`) est perdue.

**Procédure :**
1. Détecter l'erreur (message CLI indiquant session invalide).
2. Créer une nouvelle session via `claude -p --dangerously-skip-permissions`.
3. Ré-injecter le contexte complet (Blackboard + résumé récent).
4. Mettre à jour le `SESSION_ID` dans `.env` et `blackboard.json`.

---

## 9. LIVRABLES ATTENDUS

Tu dois produire un système complet et fonctionnel. Voici les fichiers à générer :

### Phase 1 : Bootstrap (Livraison Immédiate)

1. **install.ps1** : Script robuste d'installation.
   - Vérifier Python 3.11+ (`python --version`).
   - Vérifier présence des CLI (`claude --version`, `gemini --version` ou équivalent).
   - Créer venv (`python -m venv venv`).
   - Installer requirements (`pip install -r requirements.txt`).
   - Créer la structure de dossiers (`/core/`, `/workspace/`, etc.).
   - Copier `.env.template` vers `.env` et demander à l'utilisateur de le configurer.
   - Créer le wrapper `nexus.ps1` et l'ajouter au PATH.

2. **requirements.txt** :
   ```
   rich>=13.0.0
   pydantic>=2.0.0
   python-dotenv>=1.0.0
   psutil>=5.9.0
   ```

3. **nexus.py** : Point d'entrée.
   - Parser arguments CLI (`argparse`).
   - Charger configuration.
   - Lancer `core/orchestration.main_loop()`.

4. **core/synapse/protocol.py** : Modèles Pydantic complets (voir section 3.2).

5. **core/drivers/claude_driver.py** : Driver spécifique Claude.
   - Gestion de `--resume <SESSION_ID>`.
   - Gestion de `--dangerously-skip-permissions`.
   - Timeout et retry logic.

### Phase 2 : Système Complet

6. **core/orchestration.py** : La boucle principale (voir section 5).
7. **core/synapse/memory.py** : Gestion du Blackboard et compression mémorielle (voir section 4).
8. **core/synapse/state.py** : Gestion des capacités et de l'état.
9. **core/drivers/cli_driver.py** : Classe abstraite `BaseDriver`.
10. **core/drivers/gemini_driver.py** : Driver spécifique Gemini.
11. **core/ui/console.py** : Visualisation Rich (Panels, Colors, Progress).
12. **core/config.py** : Chargement et validation de `.env`.

### Phase 3 : Templates et Documentation

13. **prompts/system_gemini_base.md** : Prompt système pour Gemini.
14. **prompts/system_claude_base.md** : Prompt système pour Claude.
15. **prompts/summarization.md** : Template de résumé (voir section 4.3).
16. **.env.template** :
    ```env
    # Chemins des CLI
    CLAUDE_CLI_PATH=claude
    GEMINI_CLI_PATH=gemini

    # Sessions persistantes
    CLAUDE_SESSION_ID=

    # API Keys (optionnelles - fallback si CLI échoue)
    ANTHROPIC_API_KEY=
    GOOGLE_API_KEY=

    # Configuration
    COMPRESSION_THRESHOLD_TOKENS=100000
    MAX_SUB_AGENT_TURNS=10
    CLI_TIMEOUT_SECONDS=120
    ```

17. **workspace/.nexus/capabilities.json** : Contenu initial (voir section 4.2).

### Phase 4 : Documentation

18. **README.md** : Guide d'utilisation complet.
19. **ARCHITECTURE.md** : Documentation technique de l'architecture.

---

## 10. PRINCIPES DE DÉVELOPPEMENT

1. **Robustesse Absolue :** Aucun crash autorisé. Toute erreur doit être loggée et gérée.
2. **Transparence Cognitive :** Chaque décision d'agent doit être visible et traçable.
3. **Évolution Sécurisée :** Le mode CoreEvolution nécessite validation humaine obligatoire.
4. **Modularité :** Chaque composant doit être testable indépendamment.
5. **Performance :** Compression mémorielle proactive pour éviter la saturation du contexte.
6. **Flexibilité :** Architecture permettant l'ajout facile de nouveaux agents ou capacités.

---

## INSTRUCTION FINALE

**Objectif :** Génère un système NEXUS V4 complet, robuste, et opérationnel.

**Priorités :**
1. Fiabilité de la communication (File I/O + Pydantic Validation).
2. Gestion proactive de la mémoire (Compression automatique).
3. Coordination inter-agents explicite (`next_agent`, `instructions_for_next`).
4. Sécurité du mode CoreEvolution (Human-in-the-Loop obligatoire).
5. Expérience utilisateur fluide (Rich Console, wrapper CLI).

**Standards de Code :**
- Python 3.11+ avec type hints complets.
- Docstrings pour toutes les classes et fonctions publiques.
- Logging exhaustif (`logging` module).
- Tests unitaires pour les composants critiques (protocol.py, memory.py).

**Livrables :** Tous les fichiers listés en section 9, prêts à l'exécution.

---

Sois ambitieux. Sois robuste. Construis un système qui mérite le nom NEXUS.
