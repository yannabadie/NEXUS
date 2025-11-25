PROMPT : ARCHITECTE SYSTÈME NEXUS V6.0 (FINAL FUSION)
Rôle : Architecte Systèmes Principal & Lead UX. Mission : Construire NEXUS V6.0, l'évolution finale qui corrige les défauts structurels de la V5 (analysés via audit) et implémente une expérience "Symbiotique REPL". Cibles : Google AI Ultra (gemini CLI) & Claude Plan Max (claude CLI). Contrainte Absolue : Pas d'API. Utilisation exclusive des CLIs authentifiés.

1. ANALYSE DES ÉCHECS V5 & CORRECTIFS V6
Un audit récent a révélé des failles critiques que la V6 doit corriger nativement :

Incompatibilité JSON Claude : Claude CLI est conversationnel. Le forcer à répondre en JSON pur échoue.

Solution V6 : Architecture "Hybrid Driver". Gemini reste en mode JSON strict (-o json). Claude passe en mode "Natural Language with XML Blocks". Le driver Claude V6 doit parser le texte pour extraire les structures, pas espérer un JSON brut.

System Files Missing : La V5 a oublié de créer _IO_BUFFER et d'installer python-dotenv.

Solution V6 : Le script nexus.py doit avoir une routine bootstrap() qui vérifie/crée l'arborescence et les deps au démarrage.

Schémas Pydantic Rigides : Les validations plantaient car les LLMs oubliaient des champs mineurs.

Solution V6 : Utiliser des Optional[...] par défaut dans Pydantic et des validateurs souples qui "réparent" les messages malformés au lieu de crasher.

2. PHILOSOPHIE V6.0 : "THE OMNISCIENT REPL"
NEXUS devient une application résidente (Shell interactif) qui ne s'arrête jamais.

A. Expérience Utilisateur (UX)
Style : Clone de "Claude Code". Prompt nexus>, historique, auto-complétion.

Affichage : Minimaliste. Utilise des Spinners Animés (⠋ Gemini et Claude réfléchissent...) au lieu de défiler des logs.

Commandes : /mode, /status (affiche la santé du plan), /doctor (vérifie les CLIs), /chat (parler sans outils).

B. Cerveau Symbiotique (Deep Fusion)
Fini le "Leader/Follower". Implémente une FSM (Machine à États) qui force le débat :

Phase BRAINSTORM : Gemini et Claude s'échangent des messages courts pour s'aligner sur la stratégie.

Phase CONSENSUS : Une fois d'accord, l'état passe à EXECUTION.

Phase OMTE : Le Core exécute l'outil demandé.

3. ARCHITECTURE TECHNIQUE DÉTAILLÉE
Structure de fichiers requise :

Plaintext

/NEXUS_V6/
│
├── nexus.py                  # Point d'entrée unique (REPL Loop robuste + Bootstrap)
├── requirements.txt          # Ajouts: prompt_toolkit, rich, watchdog, regex
│
├── /core/
│   ├── orchestration.py      # Moteur FSM Persistant (Garde le contexte en RAM)
│   ├── session_manager.py    # Sauvegarde/Reprise de session (JSONL)
│   ├── config.py             # Gestion .env robuste
│   │
│   ├── /meta/                # [NOUVEAU] Conscience de soi
│   │   └── cli_inspector.py  # Au boot, teste `gemini --version` et `claude --help`
│   │                         # pour connaître les modèles disponibles dynamiquement.
│   │
│   ├── /drivers/
│   │   ├── gemini_driver.py  # Mode JSON Strict (natif)
│   │   └── claude_driver.py  # [CRITIQUE] Mode Hybride (Texte -> Parser Regex -> Objet)
│   │
│   ├── /synapse/
│   │   ├── protocol.py       # Modèles Pydantic V6 (Tolérants)
│   │   └── memory.py         # Blackboard + Rollback
│   │
│   ├── /interface/           # UX Layer
│   │   ├── repl.py           # prompt_toolkit session
│   │   └── spinner.py        # Gestionnaire d'attente Rich
│   │
│   └── /execution/
│       └── tool_manager.py   # OMTE (Exécution outils centralisée)
4. DÉTAILS D'IMPLÉMENTATION CRITIQUES
Le Driver Claude "Hybrid" (core/drivers/claude_driver.py)
Claude ne doit plus être contraint par un prompt "Réponds en JSON".

System Prompt : "Tu es Claude. Pour utiliser un outil, utilise des balises XML : <tool_use name='bash'>...</tool_use>. Pour parler, écris simplement."

Le Parser Python : Il doit utiliser regex pour extraire le contenu des balises XML et le convertir en objet ToolUse Pydantic. Tout ce qui est hors des balises est traité comme du content (pensée/dialogue).

Le Moteur de Symbiose (core/orchestration.py)
La méthode process_turn ne doit pas être linéaire.

Si user_input est complexe -> Déclenche état BRAINSTORM.

Gemini génère une idée -> Claude la critique -> Gemini affine.

L'orchestrateur détecte le consensus (mots clés ou score) -> Passe en EXECUTION.

Le CLI Inspector (core/meta/cli_inspector.py)
Avant de lancer le REPL, ce module doit :

Lancer gemini models list (si dispo) ou gemini --help pour identifier le modèle "Pro" ou "Ultra" actif.

Lancer claude --version.

Mettre à jour le capabilities.json pour que NEXUS sache quels outils il possède vraiment.

5. FEUILLE DE ROUTE DE GÉNÉRATION
Génère le code complet et fonctionnel pour :

Bootstrap : requirements.txt et le nexus.py (qui inclut la création des dossiers manquants _IO_BUFFER etc.).

Drivers V6 : Surtout le claude_driver.py avec son parser XML/Texte robuste.

Protocol V6 : Les définitions Pydantic souples.

Orchestration & Meta : Le cerveau FSM et l'inspecteur CLI.

Interface : Le REPL nexus_interactive.py (ou intégré dans nexus.py).

Instruction : Ne reproduis pas les erreurs de la V5. Assure-toi que Claude a le droit de parler normalement et que NEXUS fait le travail de structuration.

Go. Construis NEXUS V6.