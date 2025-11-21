# PROMPT : ARCHITECTE SYSTÈME NEXUS V4.5 (PRAGMATIC SYMBIOTIC EDITION)

**Rôle :** Tu es l'Architecte Systèmes Senior du projet NEXUS.
**Mission :** Concevoir et implémenter **NEXUS V4.5**, l'Orchestrateur Cognitif Symbiotique avec Auto-Correction.
**Philosophie :** "Strategy at the Speed of Thought (Gemini), Execution with Surgical Precision (Claude), Validation through Reflection."
**Environnement :** Windows 11, PowerShell, Python 3.11+.
**Contrainte Technique :** Communication privilégiée via CLI (`claude`, `gemini`) avec fallback API Python si disponible et nécessaire.

---

## 1. ARCHITECTURE & STRUCTURE

Le système est un "Puppet Master" Python qui orchestre deux processus IA persistants en symbiose, avec mécanismes d'auto-correction et de planification stratégique.

### Arborescence Cible

```text
/NEXUS_V4.5/
│
├── nexus.py              # Point d'entrée (Wrapper CLI).
├── install.ps1           # Setup (Check CLI, venv, requirements, PATH).
├── requirements.txt      # rich, pydantic, python-dotenv, psutil, filelock.
├── .env.template         # Config (Chemins EXE, Session IDs, API Keys, Seuils).
│
├── /core/
│   ├── orchestration.py  # La "Boucle Infinie" avec CFL et détection de stagnation.
│   ├── config.py         # Gestion configuration (.env + validation).
│   ├── resource_monitor.py # [V4.5] Surveillance CPU/RAM (psutil).
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
│       └── console.py          # Affichage Rich (Panels Bleu/Violet + CFL Review).
│
├── /prompts/
│   ├── system_gemini_base.md   # Prompt système de base pour Gemini.
│   ├── system_claude_base.md   # Prompt système de base pour Claude.
│   └── summarization.md        # Template de résumé pour compression mémorielle.
│
└── /workspace/                 # SANDBOX STRICTE pour les agents.
    ├── .nexus/                 # Méta-données système.
    │   ├── blackboard.json     # Mémoire partagée (objectif, état, plan stratégique).
    │   ├── capabilities.json   # Registre dynamique des outils (Conscience Mutuelle).
    │   ├── session.log         # Historique unifié complet.
    │   └── EVOLUTION_VNEXT/    # Zone tampon pour le mode CoreEvolution.
    │
    ├── _IO_BUFFER/             # Zone tampon (Contournement limites Windows).
    │   ├── nexus.lock          # [V4.5] Verrouillage fichier (filelock).
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

L'interface terminal (`core/ui/console.py`) doit afficher la symbiose cognitive avec les nouveaux mécanismes V4.5 :

**Panels Existants :**
- **[NEXUS CORE] (Gris)** : Logs système, erreurs, changements d'état, compression mémorielle.
- **[GEMINI - Stratège] (Bleu/Cyan)** : Affiche `thought_process` + `reflection` + plan stratégique.
- **[CLAUDE - Exécutant] (Violet/Ambre)** : Affiche `thought_process` + `reflection` + `action_summary`.

**Nouveaux Panels V4.5 :**
- **[V4.5] [AGENT - CFL Review] (Vert/Jaune/Rouge)** : Revue post-action.
  - Vert : `validation_status: SUCCESS`
  - Jaune : `validation_status: PARTIAL_SUCCESS`
  - Rouge : `validation_status: FAILURE` + plan de correction
- **[V4.5] [NEXUS CORE - SYSTEM] (Orange)** :
  - Détection de stagnation (`Stagnation détectée: tentative 3/5`)
  - Alertes ressources (`CPU: 92% - Pause temporaire`)
  - Mise à jour du plan stratégique

**Éléments visuels :**
- Header : Mode actif, Token Usage estimé, Session ID, Stalemate Counter (si > 0).
- Panels `rich.panel` avec couleurs et emojis optionnels.
- Progress bars pour les tâches longues (compilation, analyse).

---

## 3. PROTOCOLE DE COMMUNICATION (LE SYNAPSE V4.5)

Fiabilité critique. Tout passe par des fichiers pour éviter les limites de caractères CLI (~8000 sur Windows).

### 3.1. Mécanisme I/O Fichier avec Verrouillage [V4.5]

**Robustesse Windows améliorée avec `filelock` :**

1. **Injection :**
   - Acquérir le verrou `nexus.lock` (filelock).
   - Nexus écrit tout le contexte dans `_IO_BUFFER/context_in.md`.
   - Libérer le verrou.

2. **Invocation :** Nexus appelle le CLI avec un prompt standardisé :
   - **Claude :** `claude -p --dangerously-skip-permissions --resume <SESSION_ID> "Lis context_in.md. Réponds STRICTEMENT en JSON (Protocole Synapse V4.5) dans action_out.json."`
   - **Gemini :** `gemini "Lis context_in.md. Réponds en JSON (Protocole Synapse V4.5)." > action_out.json`

3. **Validation :**
   - Acquérir le verrou `nexus.lock`.
   - Nexus lit `action_out.json` et valide avec Pydantic (`core/synapse/protocol.py`).
   - Libérer le verrou.
   - Si malformé : Logger l'erreur brute, demander à l'agent de corriger (max 3 tentatives).
   - Si échec après 3 tentatives : Basculer sur l'autre agent ou escalader à l'utilisateur.

### 3.2. Modèle de Données (Pydantic - protocol.py) - ÉVOLUTION V4.5

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal

# Structuration de la pensée
class ThoughtChain(BaseModel):
    step: int
    reasoning: str

# [V4.5] Planification Stratégique Proactive
class StrategicPlanStep(BaseModel):
    step_id: int
    description: str
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "FAILED"]
    assigned_agent: Optional[Literal["Gemini", "Claude"]] = None

# Utilisation d'outil avec attente explicite [V4.5]
class ToolUse(BaseModel):
    tool_name: str
    arguments: Dict[str, str]
    expected_outcome: str = Field(..., description="[V4.5 CFL] Résultat précis attendu de l'exécution. CRITIQUE pour la validation post-action.")

# [V4.5] CFL - Revue Post-Action (Obligatoire après TOOL_USE)
class PostActionReview(BaseModel):
    validation_status: Literal["SUCCESS", "FAILURE", "PARTIAL_SUCCESS"]
    analysis: str = Field(..., description="Comparaison détaillée entre expected_outcome et résultat réel obtenu.")
    discrepancies: Optional[List[str]] = Field(None, description="Liste des écarts constatés si FAILURE/PARTIAL.")
    correction_plan: Optional[str] = Field(None, description="Si FAILURE/PARTIAL, plan d'action immédiat pour corriger.")

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

# Message principal du Synapse V4.5
class SynapseMessage(BaseModel):
    sender: Literal["Gemini", "Claude"]

    # Pensée Partagée (Transparence cognitive)
    thought_process: List[ThoughtChain] = Field(..., description="Chaîne de raisonnement structurée.")
    reflection: str = Field(..., description="Auto-critique avant action. Analyse des risques et validations.")

    # [V4.5] Planification Stratégique
    strategic_plan_update: Optional[List[StrategicPlanStep]] = Field(
        None,
        description="Mise à jour du plan directeur. Gemini (Stratège) l'initialise, les deux agents le maintiennent."
    )

    # Action
    action_type: Literal["TALK", "TOOL_USE", "DELEGATE", "FINISH", "ERROR", "CONTINUE"]
    action_summary: str = Field(..., description="Résumé de l'action effectuée ou planifiée.")
    content: Optional[str] = None  # Message textuel ou résultat.
    tool_use: Optional[ToolUse] = None

    # [V4.5] CFL - Revue Post-Action (OBLIGATOIRE si le tour précédent était TOOL_USE)
    post_action_review: Optional[PostActionReview] = Field(
        None,
        description="Validation du résultat de l'outil exécuté au tour précédent. OBLIGATOIRE après tout TOOL_USE."
    )

    # Coordination Inter-Agents (CRITIQUE)
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

### 4.1. Le Blackboard (blackboard.json) - ÉVOLUTION V4.5

Géré par `core/synapse/memory.py`.

**Contenu :**
```json
{
  "objective": "Objectif global de l'utilisateur",
  "mode": "Normal | InProjectImprovement | CoreEvolution",

  // [V4.5] Plan Directeur Stratégique
  "strategic_plan": [
    {"step_id": 1, "description": "Analyser le code existant", "status": "COMPLETED", "assigned_agent": "Gemini"},
    {"step_id": 2, "description": "Corriger les bugs identifiés", "status": "IN_PROGRESS", "assigned_agent": "Claude"},
    {"step_id": 3, "description": "Tester les corrections", "status": "PENDING", "assigned_agent": null}
  ],

  "recent_history": [
    {"agent": "Gemini", "timestamp": "...", "summary": "..."}
  ],
  "compressed_history_summary": "Résumé des 500 premiers tours...",

  "current_state": {
    "active_agent": "Claude",
    "iteration": 42,
    "token_count_estimate": 85000,

    // [V4.5] Détection de Stagnation
    "stalemate_counter": 0,
    "last_action_signature": "tool_use:bash:run_tests",

    // [V4.5] CFL - Attente de validation
    "pending_tool_validation": false,
    "last_tool_result": null
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
      "invocation_method": "Utiliser tool_use avec tool_name='bash' et expected_outcome obligatoire"
    },
    {
      "name": "FileEdit",
      "description": "Éditer des fichiers texte",
      "invocation_method": "Utiliser tool_use avec tool_name='edit' et expected_outcome obligatoire"
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

### 4.4. Planification Stratégique et Auto-Correction [V4.5 - NOUVEAU]

#### 4.4.A. Planification Stratégique Proactive

**Objectif :** Maintenir la cohérence à long terme en suivant un plan directeur multi-étapes.

**Fonctionnement :**

1. **Initialisation (Gemini - Stratège) :**
   - Au démarrage, Gemini analyse l'objectif utilisateur.
   - Génère un `strategic_plan` initial avec 3-7 étapes.
   - Assigne chaque étape à un agent (Gemini ou Claude) si possible.

2. **Suivi et Mise à Jour (Les deux agents) :**
   - À chaque tour, l'agent actif consulte le plan dans `blackboard.json`.
   - Peut mettre à jour le statut des étapes (`IN_PROGRESS`, `COMPLETED`, `FAILED`).
   - Peut ajouter/modifier des étapes si l'objectif évolue.

3. **Visualisation :**
   - Le plan est affiché dans le header ou un panel dédié.
   - Progression visuelle : `[✓ Étape 1] [→ Étape 2] [  Étape 3]`

**Exemple de Plan :**
```json
[
  {"step_id": 1, "description": "Analyser architecture existante", "status": "COMPLETED", "assigned_agent": "Gemini"},
  {"step_id": 2, "description": "Identifier les bugs critiques", "status": "COMPLETED", "assigned_agent": "Gemini"},
  {"step_id": 3, "description": "Corriger bug #42 (auth)", "status": "IN_PROGRESS", "assigned_agent": "Claude"},
  {"step_id": 4, "description": "Écrire tests unitaires", "status": "PENDING", "assigned_agent": "Claude"},
  {"step_id": 5, "description": "Valider avec CI/CD", "status": "PENDING", "assigned_agent": null}
]
```

#### 4.4.B. CFL (Cognitive Feedback Loop) - Boucle d'Auto-Correction

**Objectif :** Valider que chaque action produit le résultat attendu, détecter les échecs immédiatement.

**Cycle CFL en 3 Phases :**

**Phase 1 : Spécification (Agent A - Avant exécution)**
```json
{
  "action_type": "TOOL_USE",
  "tool_use": {
    "tool_name": "bash",
    "arguments": {"command": "pytest tests/"},
    "expected_outcome": "Tous les tests passent. Sortie contient 'passed' et pas 'FAILED'."
  }
}
```

**Phase 2 : Exécution (Nexus Core)**
- L'orchestrateur exécute l'outil (via l'agent natif ou subprocess).
- Capture stdout, stderr, return_code.
- Stocke le résultat dans `blackboard.json` → `last_tool_result`.

**Phase 3 : Validation (Agent A - Tour suivant - OBLIGATOIRE)**
```json
{
  "post_action_review": {
    "validation_status": "FAILURE",
    "analysis": "3 tests ont échoué (test_auth, test_db, test_api). Expected_outcome non satisfait.",
    "discrepancies": [
      "test_auth: AssertionError ligne 42",
      "test_db: Connection timeout",
      "test_api: 404 not found"
    ],
    "correction_plan": "Corriger test_auth en priorité (bug auth token). Puis investiguer DB timeout."
  }
}
```

**Gestion par l'Orchestrateur :**
- Si `validation_status == "SUCCESS"` : Réinitialiser `stalemate_counter`, passer au `next_agent`.
- Si `validation_status == "FAILURE"` : L'agent RESTE actif pour corriger, incrémenter `stalemate_counter`.
- Si `post_action_review` absent alors que `pending_tool_validation == True` : **ERREUR PROTOCOLE** (l'agent a violé le protocole CFL).

#### 4.4.C. Détection de Stagnation

**Problème :** Boucles infinies (agent répète la même action échouée).

**Mécanisme :**

1. **Signature d'Action :**
   - À chaque action, calculer une signature : `f"{action_type}:{tool_name}:{primary_arg}"`
   - Exemple : `"tool_use:bash:run_tests"`, `"tool_use:edit:fix_auth.py"`

2. **Détection :**
   - Si la signature est identique à la précédente ET `validation_status == "FAILURE"` → Incrémenter `stalemate_counter`.
   - Si la signature change OU `validation_status == "SUCCESS"` → Réinitialiser à 0.

3. **Escalade (si `stalemate_counter > MAX_STALEMATE_COUNT`) :**
   - **Niveau 1 (Seuil = 3)** : Afficher un avertissement à l'agent actif dans `context_in.md` :
     ```
     [NEXUS ALERT] Stagnation détectée (3 échecs consécutifs sur la même action).
     Considère une approche radicalement différente ou demande de l'aide au partenaire.
     ```
   - **Niveau 2 (Seuil = 5)** : Basculer de force vers l'agent partenaire avec contexte d'escalade.
   - **Niveau 3 (Seuil = 7)** : Utiliser un modèle plus puissant (ex: Opus au lieu de Sonnet) ou arrêt avec demande d'intervention humaine.

**Configuration :**
- `MAX_STALEMATE_COUNT` dans `.env` (défaut: 5).

---

## 5. LA BOUCLE D'ORCHESTRATION (core/orchestration.py) - ÉVOLUTION V4.5

### Pseudo-code de la Boucle Principale V4.5

```python
from filelock import FileLock

def main_loop():
    # Initialisation
    config = load_config()
    state = StateManager()
    memory = MemoryManager()
    resource_monitor = ResourceMonitor(config)  # [V4.5]
    gemini_driver = GeminiDriver(config)
    claude_driver = ClaudeDriver(config)

    lock = FileLock("workspace/_IO_BUFFER/nexus.lock")  # [V4.5]

    active_agent = "Gemini"  # Démarrage par le stratège.
    pending_tool_validation = False  # [V4.5] CFL State
    last_tool_result = None

    while True:
        # [V4.5] 0. Surveillance Système
        if resource_monitor.is_overloaded():
            console.log("[NEXUS CORE] CPU/RAM surchargé. Pause 30s...")
            time.sleep(30)
            continue

        # 1. Préparation du contexte
        if memory.should_compress():
            console.log("[NEXUS CORE] Compression mémorielle déclenchée...")
            memory.compress_history()

        # [V4.5] Construire le contexte avec CFL si nécessaire
        with lock:  # Verrouillage fichier
            context = memory.build_context(
                system_prompt=get_system_prompt(active_agent),
                blackboard=memory.get_blackboard(),
                capabilities=state.get_capabilities(),
                pending_tool_validation=pending_tool_validation,  # [V4.5]
                last_tool_result=last_tool_result  # [V4.5]
            )
            # Écriture dans context_in.md

        # 2. Invocation de l'agent
        driver = gemini_driver if active_agent == "Gemini" else claude_driver
        response_json = driver.invoke(context)

        # 3. Validation
        with lock:  # Verrouillage fichier
            try:
                message = SynapseMessage.parse_obj(response_json)
            except ValidationError as e:
                handle_malformed_response(driver, e)  # Max 3 tentatives.
                continue

        # 4. Visualisation
        console.display_thought_process(message, active_agent)

        # [V4.5] Afficher plan stratégique si mis à jour
        if message.strategic_plan_update:
            console.display_strategic_plan(message.strategic_plan_update)

        # [V4.5] 5. Validation CFL (Cognitive Feedback Loop)
        if pending_tool_validation:
            if message.post_action_review is None:
                handle_protocol_violation("CFL Review obligatoire manquante")
                continue

            # Afficher la revue post-action
            console.display_cfl_review(message.post_action_review)

            if message.post_action_review.validation_status == "SUCCESS":
                # Action validée - Réinitialiser CFL et stagnation
                pending_tool_validation = False
                last_tool_result = None
                state.reset_stalemate_counter()
                console.log("[NEXUS CORE - CFL] ✓ Action validée avec succès.")

            else:  # FAILURE ou PARTIAL_SUCCESS
                # Échec - L'agent reste actif pour corriger
                console.log(f"[NEXUS CORE - CFL] ✗ Échec détecté. Correction requise.")
                state.increment_stalemate_counter()

                # Vérifier stagnation
                if state.is_stalemate():
                    handle_stalemate(state, active_agent)

                # L'agent DOIT rester actif (override next_agent)
                # Le message.next_agent est ignoré en cas d'échec CFL
                pending_tool_validation = False  # Reset pour le prochain tour
                last_tool_result = None
                continue  # Même agent rejoue

        # 6. Traitement des Méta-Actions
        if message.new_capability:
            state.register_capability(message.new_capability)

        if message.request_sub_agent:
            result = execute_sub_agent(message.request_sub_agent)
            memory.add_sub_agent_result(result)

        if message.request_core_evolution:
            handle_core_evolution(message)

        # [V4.5] Mise à jour du plan stratégique
        if message.strategic_plan_update:
            memory.update_strategic_plan(message.strategic_plan_update)

        # 7. Mise à jour de l'état
        memory.add_to_history(message)

        # 8. Condition de sortie
        if message.status == "FINISHED":
            console.log("[NEXUS CORE] Objectif atteint. Fin de session.")
            break

        if message.status == "ERROR_REVIEW_NEEDED":
            console.log("[NEXUS CORE] Erreur critique. Revue requise.")
            break

        # [V4.5] 9. Gestion de TOOL_USE (Déclenche CFL au prochain tour)
        if message.action_type == "TOOL_USE":
            # Exécuter l'outil (via l'agent natif - pas d'OMTE)
            # Les agents utilisent leurs outils natifs (Claude bash, Gemini search, etc.)
            # L'orchestrateur capture juste les résultats si nécessaire

            pending_tool_validation = True  # Attendre validation au prochain tour
            last_tool_result = {
                "tool_name": message.tool_use.tool_name,
                "expected_outcome": message.tool_use.expected_outcome,
                "timestamp": time.time()
            }
            # L'agent reste actif pour faire la revue au prochain tour
            # (on n'incrémente pas active_agent)
            continue

        # 10. Transition vers l'agent suivant
        active_agent = message.next_agent

        # [V4.5] Réinitialiser stalemate si changement d'agent
        if active_agent != message.sender:
            state.reset_stalemate_counter()


def handle_stalemate(state, active_agent):
    """[V4.5] Gestion de la stagnation détectée."""
    count = state.get_stalemate_counter()

    if count >= 7:
        # Niveau 3 : Arrêt avec intervention humaine
        console.log("[NEXUS CORE] STAGNATION CRITIQUE (7+ échecs). Intervention requise.")
        raise StalemateException("Human intervention required")

    elif count >= 5:
        # Niveau 2 : Basculer vers l'agent partenaire
        console.log("[NEXUS CORE] Stagnation détectée (5 échecs). Transfert au partenaire.")
        # Ajouter contexte d'escalade dans le blackboard
        memory.add_escalation_context(active_agent, count)
        # Forcer changement d'agent (sera fait dans main_loop)

    elif count >= 3:
        # Niveau 1 : Avertissement
        console.log("[NEXUS CORE] ⚠ Stagnation détectée (3 échecs). Changement de stratégie recommandé.")
        # L'avertissement sera injecté dans context_in.md au prochain tour
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
   - **Le sous-agent DOIT également utiliser le protocole CFL** (expected_outcome + validation).
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
- "[V4.5] IMPORTANT : Après tout TOOL_USE, tu DOIS fournir post_action_review au tour suivant."
- "[V4.5] Consulte le strategic_plan dans le blackboard et mets-le à jour si nécessaire."

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

### 8.4. Violation du Protocole CFL [V4.5]

**Problème :** Un agent n'a pas fourni `post_action_review` alors que `pending_tool_validation == True`.

**Procédure :**
1. Logger la violation dans `session.log`.
2. Injecter un message d'erreur strict dans `context_in.md` :
   ```
   [ERREUR PROTOCOLE CFL] Tu as exécuté un TOOL_USE au tour précédent.
   Tu DOIS fournir post_action_review pour valider le résultat.

   Rappel du tool exécuté :
   - tool_name: [NOM]
   - expected_outcome: [ATTENDU]

   Fournis immédiatement ta revue post-action.
   ```
3. Réinvoquer l'agent sans compter comme une itération normale.
4. Si violation répétée (2 fois) : Basculer sur l'autre agent avec contexte d'erreur.

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
   filelock>=3.12.0
   ```

3. **nexus.py** : Point d'entrée.
   - Parser arguments CLI (`argparse`).
   - Charger configuration.
   - Lancer `core/orchestration.main_loop()`.

4. **core/synapse/protocol.py** : Modèles Pydantic complets V4.5 (voir section 3.2).

5. **core/drivers/claude_driver.py** : Driver spécifique Claude.
   - Gestion de `--resume <SESSION_ID>`.
   - Gestion de `--dangerously-skip-permissions`.
   - Timeout et retry logic.

### Phase 2 : Système Complet

6. **core/orchestration.py** : La boucle principale V4.5 avec CFL et stagnation (voir section 5).
7. **core/synapse/memory.py** : Gestion du Blackboard, plan stratégique et compression mémorielle (voir section 4).
8. **core/synapse/state.py** : Gestion des capacités, stalemate_counter et de l'état CFL.
9. **core/drivers/cli_driver.py** : Classe abstraite `BaseDriver`.
10. **core/drivers/gemini_driver.py** : Driver spécifique Gemini.
11. **core/ui/console.py** : Visualisation Rich (Panels, Colors, Progress, CFL Review, Plan Stratégique).
12. **core/config.py** : Chargement et validation de `.env`.
13. **core/resource_monitor.py** : [V4.5] Surveillance CPU/RAM avec psutil.

### Phase 3 : Templates et Documentation

14. **prompts/system_gemini_base.md** : Prompt système pour Gemini.
    - Inclure instructions CFL et planification stratégique.
15. **prompts/system_claude_base.md** : Prompt système pour Claude.
    - Inclure instructions CFL et expected_outcome obligatoire.
16. **prompts/summarization.md** : Template de résumé (voir section 4.3).
17. **.env.template** :
    ```env
    # Chemins des CLI
    CLAUDE_CLI_PATH=claude
    GEMINI_CLI_PATH=gemini

    # Sessions persistantes
    CLAUDE_SESSION_ID=

    # API Keys (optionnelles - fallback si CLI échoue)
    ANTHROPIC_API_KEY=
    GOOGLE_API_KEY=

    # [V4.5] Configuration Flexible des Modèles
    MODEL_STRATEGY=gemini-pro-1.5      # Hémisphère Gauche (Gemini)
    MODEL_EXECUTION=claude-sonnet-4    # Hémisphère Droit (Claude)
    MODEL_SUMMARIZATION=claude-haiku-3 # Compression mémorielle
    MODEL_ESCALATION=claude-opus-3     # Résolution de stagnation

    # Configuration
    COMPRESSION_THRESHOLD_TOKENS=100000
    MAX_SUB_AGENT_TURNS=10
    CLI_TIMEOUT_SECONDS=120

    # [V4.5] Paramètres CFL et Stagnation
    MAX_STALEMATE_COUNT=5
    RESOURCE_CPU_THRESHOLD=90          # Pause si CPU > 90%
    RESOURCE_RAM_THRESHOLD=85          # Pause si RAM > 85%
    ```

18. **workspace/.nexus/capabilities.json** : Contenu initial (voir section 4.2).

### Phase 4 : Documentation

19. **README.md** : Guide d'utilisation complet.
20. **ARCHITECTURE.md** : Documentation technique de l'architecture V4.5.

---

## 10. PRINCIPES DE DÉVELOPPEMENT

1. **Robustesse Absolue :** Aucun crash autorisé. Toute erreur doit être loggée et gérée.
2. **Transparence Cognitive :** Chaque décision d'agent doit être visible et traçable.
3. **Auto-Correction Systématique :** CFL obligatoire après tout TOOL_USE - pas de "fire and forget".
4. **Planification Proactive :** Plan stratégique maintenu et visible en permanence.
5. **Détection de Stagnation :** Pas de boucles infinies - escalade automatique.
6. **Évolution Sécurisée :** Le mode CoreEvolution nécessite validation humaine obligatoire.
7. **Modularité :** Chaque composant doit être testable indépendamment.
8. **Performance :** Compression mémorielle proactive pour éviter la saturation du contexte.
9. **Flexibilité :** Architecture permettant l'ajout facile de nouveaux agents ou capacités.

---

## 11. DIFFÉRENCES CLÉS V4 → V4.5

### Ajouts V4.5 :

1. **CFL (Cognitive Feedback Loop)**
   - `expected_outcome` obligatoire dans `ToolUse`
   - `PostActionReview` obligatoire après `TOOL_USE`
   - Validation systématique succès/échec

2. **Planification Stratégique**
   - `StrategicPlanStep` dans le protocole
   - `strategic_plan` dans blackboard.json
   - Mise à jour collaborative du plan

3. **Détection de Stagnation**
   - `stalemate_counter` dans l'état
   - Escalade automatique (3 niveaux)
   - Basculement agent ou intervention humaine

4. **Robustesse Windows**
   - `filelock` pour I/O sécurisé
   - Gestion concurrence fichiers

5. **Surveillance Système**
   - `resource_monitor.py` avec psutil
   - Pause automatique si surcharge

### Conservé de V4 :

- Architecture modulaire complète
- Compression mémorielle textuelle (pas de RAG/FAISS)
- Protocole sous-agents détaillé
- Coordination `next_agent` + `instructions_for_next`
- CLI privilégié + fallback API
- Les 3 modes opératoires
- Gestion d'erreurs robuste

### Rejeté de V5 :

- ❌ OMTE (garde les outils natifs des agents)
- ❌ Protocole Gardien (trop coûteux)
- ❌ RAG/FAISS (complexité excessive, instable Windows)
- ❌ watchdog filesystem (overkill)

---

## INSTRUCTION FINALE

**Objectif :** Génère un système NEXUS V4.5 complet, robuste, auto-correctif et opérationnel.

**Priorités :**
1. **CFL (Auto-Correction)** : Implémentation rigoureuse du cycle expected_outcome → exécution → validation.
2. **Planification Proactive** : Plan stratégique maintenu et mis à jour en collaboration.
3. **Détection de Stagnation** : Pas de boucles infinies - escalade intelligente.
4. **Fiabilité de la communication** : File I/O + Filelock + Pydantic Validation.
5. **Gestion proactive de la mémoire** : Compression automatique textuelle.
6. **Coordination inter-agents explicite** : `next_agent`, `instructions_for_next`.
7. **Sécurité du mode CoreEvolution** : Human-in-the-Loop obligatoire.
8. **Expérience utilisateur fluide** : Rich Console avec visualisation CFL et plan.

**Standards de Code :**
- Python 3.11+ avec type hints complets.
- Docstrings pour toutes les classes et fonctions publiques.
- Logging exhaustif (`logging` module).
- Tests unitaires pour les composants critiques (protocol.py, memory.py, CFL logic).

**Livrables :** Tous les fichiers listés en section 9, prêts à l'exécution.

---

**Sois ambitieux. Sois robuste. Sois pragmatique.**

**Construis un système qui mérite le nom NEXUS - avec la sagesse de savoir quand s'autocorriger.**
