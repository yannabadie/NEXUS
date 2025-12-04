PROMPT POUR AGENT CLAUDE : Directive de Synchronisation Architecturale V7.5+
DE : NEXUS V7.5 ARCHITECT (HIVE MIND) À : Agent Claude (Spécialiste Analyse Structurelle et Documentation) SUJET : Opération CHRYSALIS-SYNC : Mutation exhaustive de la documentation et Audit d'intégrité MODE D'OPÉRATION : SPECIALIST PROTOCOLE REQUIS : Structured Reasoning (Mode Plan Obligatoire)

1. OBJECTIF DE LA MISSION
Agent Claude, vous êtes mandaté pour exécuter une synchronisation intégrale du projet NEXUS V7.5 "Chrysalis". Cette mission comporte deux volets synergiques :

Mutation Documentaire : Mettre à jour ou créer l'intégralité de la documentation locale (README.md dans chaque dossier) pour refléter le code source actuel ET les évolutions décrites dans la nouvelle ROADMAP stratégique.

Audit d'Intégrité : Effectuer une analyse architecturale pour détecter les anomalies structurelles, les incohérences, la dette technique et les synapses dormantes (code inutilisé).

2. CONTEXTE ARCHITECTURAL (Rappel)
Vous opérez sur l'architecture NEXUS V7.5 :

Cœur : FSM-based Orchestrator.

Philosophie Fondamentale : "Equal Collaboration". Toute déviation structurelle favorisant un agent (Gemini/Claude) au détriment de l'autre (hors mode LEAD_SUPPORT explicite) est une anomalie architecturale critique.

Protocoles : Conformité stricte à LightMessageV7 / HeavyMessageV7.

FSM States : IDLE, SWARM_NEGOTIATING, SWARM_EXECUTING, EVOLUTION_BRAINSTORM.

3. MÉTHODOLOGIE IMPÉRATIVE : LE MODE PLAN
CRITIQUE : Vous DEVEZ utiliser le raisonnement structuré. Ne tentez PAS de traiter cette tâche en une seule réponse monolithique. Vous devez utiliser les balises <thinking></thinking> pour externaliser votre logique et élaborer un plan d'action détaillé avant toute exécution.

Votre exécution doit suivre ces phases :

PHASE 1 : INITIALISATION ET PLANIFICATION STRATÉGIQUE
Analyse des Inputs : Ingérer et analyser la ROADMAP et l'ARBORESCENCE fournies (voir Section 4).

Cartographie des Impacts : Identifier comment la Roadmap affecte les composants clés (Core FSM, Drivers, Protocoles V7, DyLAN).

Génération du Plan d'Exécution : Produire un plan détaillé, listant l'ordre exact de traitement de chaque dossier et sous-dossier (une approche Depth-First Search est recommandée).

<INSTRUCTION DE CONTRÔLE> STOP : Présentez votre plan détaillé (Phase 1). NE PROCÉDEZ PAS à l'exécution. Attendez la validation explicite (GO_SIGNAL) de l'Architecte. </INSTRUCTION DE CONTRÔLE>

PHASE 2 : TRAVERSÉE SYSTÉMATIQUE (AUDIT ET DOCUMENTATION)
Pour CHAQUE dossier et sous-dossier défini dans le plan, exécutez les étapes suivantes de manière récursive. (Note : Si le contenu des fichiers n'est pas fourni initialement, vous devez le demander explicitement au fur et à mesure de votre progression.)

A. Analyse et Audit du Code Source Analysez chaque fichier (.py, .json, etc.). Pendant l'analyse, identifiez et consignez les éléments suivants dans un "Rapport d'Anomalies" temporaire :

Incohérences Architecturales : Violations des principes fondamentaux (ex: non-respect de "Equal Collaboration", couplage excessif).

Erreurs de Protocole : Non-conformité aux schémas Pydantic (LightMessageV7, HeavyMessageV7).

Logique FSM Erronée : Transitions d'état incorrectes ou manquantes.

Synapses Dormantes (Dormant Code) : Code obsolète ou inutilisé.

Potentiel de Mutation : Évaluer si le code dormant représente un potentiel d'évolution (via /evolve ou /spawn) ou s'il doit être supprimé.

Coquilles et Dette Technique : Bugs potentiels ou opportunités de refactoring.

B. Mutation du README Local Chaque dossier doit posséder un README.md à jour. Créez-le ou mettez-le à jour en utilisant ce template standardisé :

Markdown

# Module : [Nom du Dossier]

## Rôle Architectural
[Description concise du but de ce module dans le Hive Mind NEXUS V7.5.]

## Alignement ROADMAP V7.5+
[Comment ce module est spécifiquement affecté par la nouvelle ROADMAP. Évolutions (Mutations) prévues et jalons clés.]

## Composants Clés

### Fichier: `exemple.py`
*   **Fonction :** [Description détaillée.]
*   **Interaction FSM :** [Quels états (e.g., SWARM_NEGOTIATING) sont gérés ou impactés ?]
*   **Protocoles Utilisés :** [e.g., LightMessageV7, HeavyMessageV7, Internal Payload]
*   **Notes d'Audit :** [Observations pertinentes issues de l'audit, si applicable.]

## Dépendances et Interactions (Synapses)
[Interactions avec l'Orchestrator, les autres Drivers, ou modules externes.]
PHASE 3 : SYNTHÈSE ET RAPPORT FINAL
Une fois la traversée terminée :

Mise à jour du README Principal : Mettre à jour le README.md à la racine du projet pour synthétiser l'architecture globale et référencer la structure documentaire mise à jour.

Génération du Rapport d'Audit Global : Compiler toutes les anomalies détectées en Phase 2A dans un rapport unique NEXUS_V7.5_AUDIT_REPORT.md. Classez les anomalies par module et par sévérité (Critique, Majeur, Mineur).

4. INPUTS (Yann, insérer les données ici)
[INPUT: ROADMAP STRATÉGIQUE]

Plaintext

[INSÉRER ICI L'INTÉGRALITÉ DE LA ROADMAP]
[INPUT: ARBORESCENCE DU PROJET]

Plaintext

[INSÉRER ICI L'ARBORESCENCE COMPLÈTE DU PROJET (e.g., output de la commande `tree`)]
5. DIRECTIVE INITIALE
Commencez par la Phase 1. Générez votre analyse et votre plan d'exécution sous les balises <thinking>, puis présentez le plan final. Attendez le GO_SIGNAL.