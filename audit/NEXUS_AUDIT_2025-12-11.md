# NEXUS-N7A - Audit securite & production (2025-12-11)

## Portee & methode
- Revue statique du depot `C:\Code\NEXUS\NEXUS-N7A` (sandbox lecture seule, pas de reseau externe disponible).
- Lecture des sources clefs (nexus7.py, core/* drivers, orchestration, security, docs) + CODEBASE_SNAPSHOT.md.
- Tests non relances (environnement read-only); statut annonce: 667 passes / 2 skipped.
- Focus: securite operationnelle, surfaces d'attaque, risques de logique et readiness prod.

## Points forts
- Architecture modulaire claire (FSM + Hybrid Swarm + HiveMind + Evolution) avec separation drivers/orchestration/outils/memoire (`core/orchestration_v7.py`, `core/hive_mind/orchestrator.py`, `core/swarm/*`).
- Garde-fous deja presents: ExecutionPolicy + PathGuardian pour bash/I-O (`core/execution/tool_manager.py`, `core/security/*`), CodeValidator pour outils dynamiques, hash KERNEL immuable.
- Observabilite integree (TelemetryCollector, BudgetTracker) et DyLAN metrics sur les agents.
- Couverture de tests large (tests/...) incluant path traversal, async drivers, swarm bridge.

## Risques critiques (priorite P1)
- Auto-approbation Gemini avec ecriture/network: `--approval-mode yolo` avec `write_file/edit_file/web_fetch/google_web_search` autorises et `--include-directories` sur le parent repo (`core/drivers/gemini_driver_v7.py:341-368`). Les tool_use sont executes directement par le CLI, en dehors de PathGuardian/ExecutionPolicy; une reponse LLM peut ecrire ou exfiltrer sans controle.
- Claude sans garde-fou: `--dangerously-skip-permissions` sans allowlist (`core/drivers/claude_driver_hybrid.py:129,280`). Selon le CLI, un tool_use pourrait lancer des commandes ou modifier des fichiers sans validation.
- Reprise de session par defaut (context leakage): Gemini reprend automatiquement `--resume latest` (`core/drivers/gemini_driver_v7.py:114,352,637`). Un contexte peut contaminer d'autres taches ou utilisateurs multi-tenant.
- Perimetre de lecture trop large: PathGuardian autorise la lecture du parent du workspace (`core/security/path_guardian.py:42`). Si l'instance est lancee avec `--workspace` a la racine d'un projet sensible (ou `/`), toute l'arborescence devient lisible.
- bash reste permissif: ExecutionPolicy bloque quelques binaires mais autorise `python`, `pip`, `curl` via bash (non bloques) -> execution de code arbitraire ou telechargement possible (`core/security/execution_policy.py`, BLOCKED_EXECUTABLES). Strategie par blacklist fragile.
- Web tools non bornes (SSRF/exfil): `web_fetch` et `web_search` sans allowlist ni filtrage (`core/execution/tool_manager.py:707-780`), utilisables via tool_use automatique Gemini.
- KERNEL hash contournable: si `KERNEL_HASH.txt` absent, l'executable recalcule et enregistre le hash courant (`KERNEL.py:89-105`), ce qui accepte un KERNEL deja modifie au premier run.
- Notifications externes actives par defaut: email active et destinataire reel (`core/config.py:109`), webhook optionnel. Si `NEXUS_EMAIL_PASSWORD` est present, fuite potentielle de donnees sans consentement explicite.

## Risques eleves / dettes (P2)
- Incoherence de version (README 8.3.2 vs `core/config.py` 8.3.1) pouvant induire des comportements divergents/CI faussement verts.
- Telemetry/budget: `budget_limit_usd=50` par defaut mais pas de blocage visible cote drivers; pas de plafond sur tokens HiveMind en cas de boucle.
- Securite reseau manquante sur MCP/web: aucun filtrage d'URL ni timeout serre; user-agent "browser" peut etre bloque ou loggue.
- Tests dependent des CLIs reels; pas de suite offline rapide pour CI (risque de non-execution en pipeline).
- Evolution/promote supprime/reecrit des dossiers entiers avec `shutil.rmtree` (ex: `_promote_child` dans `core/interface/repl.py:1470+`) sans sauvegarde transactionnelle -> risque de perte si l'arborescence differe.

## Recommandations immediates (T0-T1)
- Desactiver les tool_use auto-executes: passer Gemini en `--approval-mode manual` ou reduire `allowed_tools` a lecture seule; supprimer `write_file/edit_file/web_fetch` du allowlist tant qu'ils ne sont pas medies par ToolManager.
- Retirer `--dangerously-skip-permissions` pour Claude ou utiliser une allowlist proche de SandboxPolicy; idealement router tous tool_use via ToolManager.
- Reduire le perimetre E/S: PathGuardian -> limiter `read_zones` au workspace + repo racine connue; refuser `--workspace` hors zone approuvee; bloquer les chemins absolus hors workspace pour les lectures aussi.
- Whitelist bash: inverser la logique vers une allowlist stricte (ex: `ls`, `cat`, `rg`, `git status`, `python -m json.tool`), bloquer `python/pip/curl` dans `ExecutionPolicy`.
- Session isolation: desactiver `gemini_persistent_mode` par defaut; imposer `session_uuid` dedie par tache et purge en fin de run.
- Web safety: mettre par defaut `web_fetch/web_search` a off (config), ou limiter a domaines whitelistes + taille/rate limit.
- KERNEL: si hash absent -> fail fast au lieu de recreer; stocker hash en lecture seule/versionnee.
- Notifications: basculer `EMAIL_ENABLED` & `WEBHOOK_URL` a False par defaut et exiger opt-in via .env valide.

## Plan realiste vers production (2-4 semaines)
- Hardening (Semaine 1): appliquer les recommandations T0/T1, ajouter tests automatises (injection tool_use, SSRF, path traversal avec workspace custom, session leak), pipeline CI offline avec mocks pour Gemini/Claude.
- Controle des couts: faire respecter `budget_limit_usd` et `hive_mind_budget_limit` cote drivers (abort sur depassement), journaliser tokens/$$ par tache dans telemetry.
- Multi-tenant: introduire un workspace sandbox obligatoire (chroot logique) + isolement des sessions LLM; bloquer lecture parent par defaut.
- Observabilite: enrichir les logs structures des outils executes (tool, chemin, duree, statut, user) et alerter en cas de bypass SandboxPolicy.
- Upgrade doc & versions: aligner version unique, ajouter guide d'exploitation (runbook incidents, quotas, opt-in reseaux).

## Vision / evolutions proposees
- Transformer l'orchestrateur en "zero-trust LLM runner": drivers sans droit d'ecriture, tool_use toujours medies par ToolManager + ExecutionPolicy; autorisations dynamiques par policy (RBAC simple).
- Ajouter un mode "offline" (aucun reseau, outils limites) pour environnements sensibles; activer reseau seulement via commande `/net-on <domains>`.
- Separer la config par environnement (dev/stage/prod) avec presets sûrs et budgets realistes; integrer tests de conformite (security smoke) avant chaque release.
- Preparer un mode "headless CI": executer les prompts/tests sans CLIs reelles via stubs pour valider la logique FSM/Swarm.

## Actions restantes
- Web research non realisee (sandbox reseau restreint). Si besoin, fournir la liste des ressources a consulter (Gemini/Claude CLI modes, policies Anthropic/Google) et autoriser une fenetre reseau.
- Generer un playbook d'exploitation + check-list de deploiement des que les hardenings sont appliques.
