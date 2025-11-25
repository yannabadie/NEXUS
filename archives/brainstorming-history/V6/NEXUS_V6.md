PROMPT : MISSION NEXUS V6.0 - "TRUE SYMBIOSIS REPL"
Contexte : Tu reprends le projet NEXUS. L'architecture actuelle (V5.1) est fonctionnelle (Drivers CLI, Tool Executor, CFL) mais l'expérience utilisateur est fragmentée et la collaboration entre IA est trop hiérarchique (Google donne des ordres -> Claude exécute).

TA MISSION : Transformer NEXUS en une Console Unifiée Persistante qui utilise mes CLIs locaux (gemini, claude) pour créer une Super-IA Fusionnelle. Je veux une expérience fluide, identique à l'interface native de Claude Code, mais avec deux cerveaux.

1. REFACTORING ARCHITECTURAL (PRIORITÉ ABSOLUE)
A. Orchestrateur Persistant (Fin du "Start/Stop")
Modifie core/orchestration.py.

Actuellement : run() est une boucle qui finit par break.

Cible : Transforme Orchestrator en un moteur d'état persistant.

Crée une méthode process_turn(user_input) qui prend l'entrée, fait avancer l'état, et rend la main sans tuer l'objet.

L'état (Blackboard, Historique, Plan) doit rester chaud en RAM. Le disque (blackboard.json) sert de sauvegarde, pas de mémoire principale.

B. Protocole "Deep Fusion" (Co-Reasoning)
Casse la logique "Gemini décide, Claude obéit". Implémente une phase de "Ping-Pong Cognitif" avant l'action.

Nouveau Status : BRAINSTORMING.

Logique : Si la tâche est complexe (détectée par le premier agent), l'orchestrateur doit permettre 2-3 échanges de pur texte entre Gemini et Claude (sans outils) pour affiner la stratégie avant de passer en mode EXECUTION.

Prompt Système : Modifie les prompts pour dire : "Tu es une partie d'une conscience double. Si tu as un doute, consulte ton partenaire avant d'agir."

2. INTERFACE & UX "CLAUDE CODE-LIKE"
Refais l'interface dans nexus_interactive.py et core/ui/console.py pour atteindre le Minimalisme Informatif.

Le Spinner Intelligent : Au lieu de spammer des logs JSON, affiche un spinner animé avec un texte changeant :

"Gemini analyse la stratégie..."

"Claude valide la sécurité..."

"Exécution : pytest..."

Affichage Compact :

Cache les ThoughtProcess par défaut (accessibles via une commande verbose ou une touche).

Affiche uniquement le content final et les ToolResult importants.

Input Multi-lignes : Utilise prompt_toolkit pour permettre de coller du code ou des textes longs (support du Alt+Enter).

3. GESTION DES DRIVERS (CONTRAINTE STRICTE)
INTERDICTION D'UTILISER LES API. Tu dois continuer d'utiliser subprocess pour appeler les exécutables gemini et claude authentifiés sur ma machine.

Optimisation Latence : Les appels CLI sont lents. Implémente un système de "Pre-fetching" ou de cache contextuel intelligent si possible, mais privilégie la robustesse. Si un CLI timeout, le système doit le dire clairement et proposer un retry.

4. FEUILLE DE ROUTE D'EXÉCUTION
Agis étape par étape :

Analyse : Lis nexus_interactive.py, core/orchestration.py et les fichiers dans core/synapse/.

Refactor State : Modifie StateManager pour supporter le mode BRAINSTORMING et la persistance RAM.

Refactor Loop : Réécris la boucle principale de nexus_interactive.py pour qu'elle garde l'instance de l'orchestrateur vivante.

Upgrade UI : Implémente l'affichage minimaliste avec rich.live ou rich.progress.

Debug : Vérifie que le passage de parole (Gemini <-> Claude) conserve tout le contexte conversationnel.

Sortie attendue : Je veux que tu réécrives les fichiers clés (nexus_interactive.py, core/orchestration.py, core/ui/console.py) pour atteindre cet état de grâce.

Go. Construis l'interface ultime.