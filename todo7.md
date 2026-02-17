🧠 NEXUS NX-CG : MASTER EXECUTION BLUEPRINT
Target Agent: Claude Code 4.6 Opus

## 1. 🛡️ GUARDRAILS & ARCHITECTURE (NE PAS CASSER)

**Paradigme Système :**
NEXUS est une plateforme d'orchestration agentique avancée reposant sur un écosystème Multi-LLM asynchrone. L'état global est piloté par une **Machine à États Finis (FSM) persistante** et un moteur d'**Event Sourcing**. Le cycle de vie d'une exécution d'outil est immuable : `Tool Invocation -> Validation CFL (Control Flow Logic) -> Evidence Pack Update`.

**Règles d'Or Absolues (CRITICAL DIRECTIVES) :**
1. **Intégrité KERNEL :** Ne **JAMAIS** altérer la logique de vérification cryptographique du `KERNEL.py` et de `KERNEL_HASH.txt`. Toute modification de ces fichiers brisera la chaîne de confiance.
2. **Streaming Asynchrone :** L'OrchestratorV7 fonctionne nativement en asynchrone. Interdiction stricte d'introduire des appels I/O bloquants synchrones dans la boucle d'exécution.
3. **Agnosticisme Multi-Modèles :** Le routage dynamique (Hive-Mind/Swarm) doit rester agnostique. Ne pas hardcoder de noms de modèles spécifiques dans la logique métier.
4. **Préservation de l'Evidence Pack :** La traçabilité est sacrée. L'Evidence Pack est "append-only". Ne jamais écraser le contexte ou l'historique de recherche ; toute synthèse finale doit s'y référer.

## 2. 🔍 DIAGNOSTIC DES DERNIÈRES ÉVOLUTIONS

À partir de l'exploration de la branche `NX-CG`, voici l'état des lieux structurel actuel :
- **Packaging :** Un fichier `pyproject.toml` a été initialisé, posant les bases du packaging, mais les entrypoints CLI (ex: commande globale `nexus`) nécessitent d'être déclarés et câblés.
- **Sécurité (Sandbox) :** Le module `core/execution/handlers/sandbox_handler.py` a fait son apparition. L'infrastructure d'isolation existe, mais elle n'est pas encore systématiquement imposée par le `ToolManager`.
- **Research CLI :** Le script `nexus_research.py` est présent, mais le mode de réduction final (`--synthesize`) exploitant l'Evidence Pack pour rédiger une réponse argumentée manque à l'appel.
- **Dette de Configuration :** La dérive (drift) est confirmée. Les fichiers `core/config.py`, `.env.example` et `docker-compose.yml` sont désynchronisés et des valeurs "Yann-centric" (chemins locaux, identifiants) subsistent en dur.
- **Serveur MCP :** La fondation du Model Context Protocol est en place (`core/mcp/server.py`, `protocol.py`), mais elle nécessite une stricte application des contrats Pydantic pour éviter les crashs sur des payloads malformés.

## 3. 🛠️ BACKLOG D'EXÉCUTION (Task List)

### Phase 1 : Clean-up Config & Tenants (Dette & Abstraction)
- [ ] **Standardiser la configuration globale**
  - **Objectif :** Résoudre le "drift" et purger le code des dépendances "Yann-centric".
  - **Fichiers ciblés :** `core/config.py`, `.env.example`, `docker-compose.yml`
  - **Logique attendue :** 
    1. Analyser `core/config.py` et extraire tous les chemins absolus locaux, emails ou identifiants en dur. Les remplacer par des résolutions via variables d'environnement (`os.getenv` ou `pydantic-settings`) avec des fallbacks agnostiques.
    2. Mettre à jour `.env.example` pour qu'il reflète exactement les clés utilisées par la configuration.
    3. Aligner la section `environment` du `docker-compose.yml` pour assurer la bonne injection de ces variables.

### Phase 2 : Core Features Completion (Research CLI)
- [ ] **Implémenter le mode `--synthesize`**
  - **Objectif :** Permettre au Research CLI de générer une réponse finale argumentée basée sur l'Evidence Pack.
  - **Fichiers ciblés :** `nexus_research.py`
  - **Logique attendue :** 
    1. Ajouter l'argument booléen `--synthesize` via `argparse`.
    2. En fin de processus de recherche asynchrone, si le flag est présent, récupérer le contenu consolidé de l'Evidence Pack.
    3. Construire un prompt de synthèse injectant ce contexte et l'envoyer au LLM via le routeur.
    4. Capter le flux de retour (streaming asynchrone) et l'afficher sur `stdout` au format Markdown.

### Phase 3 : Security Sandboxing
- [ ] **Coupler la Sandbox au gestionnaire d'outils**
  - **Objectif :** Isoler obligatoirement l'exécution des outils à risque du système hôte.
  - **Fichiers ciblés :** `core/execution/tool_manager.py`, `core/execution/handlers/sandbox_handler.py`
  - **Logique attendue :** 
    1. Finaliser `sandbox_handler.py` pour restreindre l'exécution (timeouts stricts, limitation du filesystem, nettoyage de l'environnement parent).
    2. Dans `tool_manager.py`, modifier le dispatch pour que l'exécution de code externe ou de commandes shell soit **obligatoirement** routée vers le `sandbox_handler`. Une exception claire doit être levée si ce routing échoue ou est bypassé.

### Phase 4 : Packaging & MCP Stabilization
- [ ] **Câbler l'Entrypoint CLI et stabiliser le MCP**
  - **Objectif :** Rendre NEXUS installable universellement et garantir des échanges JSON-RPC robustes.
  - **Fichiers ciblés :** `pyproject.toml`, `core/mcp/protocol.py`, `core/mcp/server.py`
  - **Logique attendue :** 
    1. Dans `pyproject.toml`, ajouter la section `[project.scripts]` pour mapper les commandes globales (ex: `nexus = "nexus7:main"`, `nexus-research = "nexus_research:main"`).
    2. Dans `protocol.py`, configurer les modèles Pydantic des messages MCP avec `extra = "forbid"` pour rejeter les champs non conformes.
    3. Dans `server.py`, ajouter des blocs `try/except` globaux pour assurer une gestion gracieuse des erreurs de schéma sans faire crasher l'Event Loop.

## 4. 🧪 PROTOCOLE DE TEST CONTINU

Exécute les commandes suivantes de manière séquentielle dans ton terminal local à la fin de chaque étape. Répare immédiatement toute régression (Exit code != 0).

**Validation Post-Phase 1 (Config) :**
```bash
cp .env.example .env
python -c "import core.config; print('Config loaded successfully')"
docker-compose config -q

Validation Post-Phase 2 (CLI Synthesize) :

Bash
python nexus_research.py --help | grep synthesize
python nexus_research.py "Quantum computing basics" --synthesize --dry-run
Validation Post-Phase 3 (Sandboxing) :

Bash
pytest tests/test_sandbox_handler.py -v
pytest tests/test_tool_manager.py -v
Validation Post-Phase 4 (Packaging & MCP) :

Bash
pip install -e .
nexus --help
nexus-research --help
pytest tests/test_mcp_server.py -v
Vérification de Non-Régression Globale (CRITICAL) :

Bash
pytest tests/fsm/ -v
python -c "import KERNEL; KERNEL.verify_kernel_integrity()"