# SESSION INITIATION: NEXUS V4 GENESIS

**To:** Claude (Architect & Executor)
**From:** Gemini (Strategist & Orchestrator)
**Context:** We are rebuilding NEXUS. Previous attempts failed due to fragmentation. We have a solid plan validated by the User.

## MISSION
Bootstraper l'environnement **NEXUS V4** ("The Puppet Master Architecture") sur Windows 11.

## INPUT CONTEXT
Lis attentivement le fichier `20_NEXUS/NEXUS_MASTER_PROMPT.md`. C'est notre *Blueprint* validé.

## TES DIRECTIVES D'EXÉCUTION (Strictes)
1.  **Analyse** le blueprint.
2.  **Génère** les fichiers suivants :
    *   `NEXUS_V4/requirements.txt` (Incluant: `rich`, `pydantic`, `python-dotenv`, `psutil`).
    *   `NEXUS_V4/install.ps1` (Script d'installation robuste : check python, check CLIs, venv creation, install deps, create folder structure).
    *   `NEXUS_V4/nexus.py` (Le squelette du point d'entrée).
3.  **Respecte** ces contraintes techniques :
    *   Utilise `utf-8` pour tous les fichiers.
    *   Dans `install.ps1`, assure-toi de vérifier l'existence des commandes `claude` et `gemini` dans le PATH. Si absentes, erreur explicite.
    *   Structure de dossiers à créer :
        ```
        NEXUS_V4/
          core/
            drivers/
            synapse/
            interfaces/
            ui/
          workspace/
            _IO/
            .nexus/
        ```

## TON FORMAT DE RÉPONSE
Ne bavarde pas. Exécute les actions de création de fichiers (`write_file`).
À la fin, confirme avec : "NEXUS V4 BOOTSTRAP COMPLETE. READY FOR INSTALL."

## IMPORTANT
Tu as la permission `--dangerously-skip-permissions`. N'attends pas de validation utilisateur pour écrire. Fonce.
