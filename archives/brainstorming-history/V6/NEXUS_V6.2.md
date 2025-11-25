# PRE-INSTRUCTION CRITIQUE : MODE PLANIFICATION
Avant de générer la moindre ligne de code Python, je veux que tu actives ton mode "Thinking" maximal.
1. Analyse l'architecture actuelle vs la cible (FSM).
2. Écris en pseudo-code la logique de la nouvelle méthode `process_turn`.
3. Liste les états possibles de la machine à états (FSM).
4. Vérifie mentalement que le cycle de vie de l'objet `Orchestrator` ne sera jamais interrompu par une exception utilisateur.

Une fois cette analyse interne faite, génère le code.
PROMPT : MISSION NEXUS V6.0 - "TRUE SYMBIOSIS REPL"
Contexte : Tu es l'Architecte Système Principal. Je travaille sur NEXUS, un orchestrateur CLI qui pilote mes exécutables locaux gemini et claude. La version actuelle (V5.1) est instable : elle simule l'interactivité en relançant le moteur à chaque commande, ce qui cause des pertes de contexte et des boucles infinies d'erreurs JSON. De plus, l'interface est trop verbeuse (logs techniques) et pas assez "utilisateur".

TA MISSION : Refondre totalement la couche d'interaction et d'orchestration pour créer NEXUS V6.0. Je veux une Console Unifiée Persistante (REPL) qui imite parfaitement l'expérience utilisateur de Claude Code, mais avec deux cerveaux (Gemini + Claude) qui collaborent en temps réel.

1. ARCHITECTURE V6.0 : LE MOTEUR PERSISTANT
Tu dois réécrire core/orchestration.py pour abandonner la logique de boucle while unique. Transforme-le en une Machine à États (FSM) maintenue en mémoire vive.

Nouvelle Structure de Classe Orchestrator :
Attributs persistants : self.memory, self.state restent chargés en RAM. Ne recharge pas blackboard.json à chaque tour, utilise-le seulement pour le backup.

Méthode process_turn(user_input) :

Prend l'entrée utilisateur.

Fait avancer la FSM d'un ou plusieurs pas.

Rend la main au REPL (yield) pour afficher des mises à jour visuelles (spinners) sans bloquer.

Nouveau Mode : "DEEP FUSION" (Ping-Pong Cognitif)
Casse la hiérarchie "Gemini ordonne -> Claude exécute".

Introduis un état BRAINSTORMING.

Si la tâche est complexe, Gemini et Claude doivent échanger des messages de type TALK (texte pur, pas d'outils) pour s'aligner sur une stratégie.

L'orchestrateur ne doit PAS forcer un HeavyMessage (Tool Use) tant que le consensus n'est pas atteint.

2. UX & INTERFACE : "CLAUDE CODE-LIKE"
Réécris nexus_interactive.py et core/ui/console.py. Je veux du Minimalisme Informatif.

Le Shell (nexus_interactive.py) :

Utilise prompt_toolkit pour un vrai shell (historique, auto-complétion, multi-lignes).

Le prompt doit être stylé : nexus (gemini+claude) >.

Intercept les commandes slash (/mode, /clear, /doctor) avant d'appeler l'IA.

L'Affichage (core/ui/console.py) :

STOP aux logs JSON défilants. L'utilisateur ne doit pas voir {"action_type": "..."}.

Utilise rich.live pour afficher un Spinner Animé qui décrit l'action en cours :

⠋ Gemini réfléchit à la stratégie...

⠋ Claude analyse le code...

⠋ Exécution : pytest (via Nexus Core)...

Affiche uniquement :

Le message final destiné à l'utilisateur (Markdown rendu).

Les erreurs critiques (en rouge).

Les résultats d'outils importants (succès/échec succinct).

3. ROBUSTESSE DU PROTOCOLE (ANTI-BOUCLE)
Corrige les erreurs de parsing JSON vues dans les logs.

Gestion des Erreurs JSON :

Si Claude répond en texte ("Je comprends..."), le driver doit automatiquement tenter d'extraire le JSON s'il existe, ou renvoyer une erreur formatée qui force l'agent à réessayer immédiatement avec le bon format (sans planter l'orchestrateur).

Injecte un rappel système "JSON ONLY" encore plus strict si une erreur de parsing survient.

Assouplissement du Dual Schema :

Ne force pas HeavyMessage aveuglément. Si l'agent veut juste parler (TALK), accepte le LightMessage même si on attendait un outil, mais pénalise son score de confiance.

4. FEUILLE DE ROUTE D'IMPLÉMENTATION
Génère le code complet pour ces 3 fichiers clés. Ne fais pas de résumés, je veux le code fonctionnel.

core/ui/console.py : Nouvelle classe NexusUI utilisant Rich pour gérer les spinners et l'affichage propre.

core/orchestration.py : Refonte en FSM persistante supportant le mode BRAINSTORMING.

nexus_interactive.py : Le nouveau point d'entrée REPL qui maintient l'orchestrateur en vie.

Contrainte : Tu dois continuer d'utiliser les drivers CLI (claude, gemini) via subprocess. Pas d'API.

Go. Transforme ce script en une véritable application console professionnelle.