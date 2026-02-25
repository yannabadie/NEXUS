Voici mon audit **des modifications récentes** sur la branche **NX‑CG** (état visible au **17 février 2026**) + ce que je te recommande de faire ensuite, avec les **erreurs concrètes** que je vois et les **directions** à privilégier.

---

## 1) Modifications récentes majeures observées

### 1.1. Mémoire “V2” (LanceDB) : passage au **sémantique** + migration

Tu as introduit une **Memory V2** qui remplace une partie des heuristiques “hash/similarity” par une **recherche vectorielle** via l’architecture **ProjectMemory/LanceDB**.

* Le commit **Epic 1.4** ajoute **SuccessMemoryV2** et **StrategyBlacklistV2**, avec **migration automatique** depuis les fichiers V1 (markers `.migrated_to_v2`, `.blacklist_migrated_to_v2`) et stockage des entrées comme des **Chunk** enrichis de **metadata** (task_id, mode, score, domains, etc.). ([GitHub][1])
* Tu as ensuite des commits d’intégration “Phase 1 / Phase 7” et des tests autour de V2 (on voit clairement la séquence dans l’historique). ([GitHub][2])

**Ce que ça change architecturalement :** tu rapproches la mémoire “épisodique” (succès/échecs) du même moteur de retrieval que ta mémoire “RAG codebase”, ce qui est cohérent si tu veux une mémoire unifiée et interrogeable de manière homogène. ([GitHub][1])

---

### 1.2. Sagas durables + Redis event bus (résilience)

On voit passer **Epic 1.3 - Durable Sagas with Redis Event Bus** dans l’historique. Sans même entrer dans le code ici, c’est une bascule importante : tu vas vers une exécution **rejouable / reprise sur incident**, ce qui est exactement ce qu’il faut quand tu as plusieurs phases/agents/outils. ([GitHub][2])

---

### 1.3. Observabilité “production” : OTel Collector + Jaeger

Tu as ajouté une brique d’observabilité avec **OTel Collector + Jaeger**, et tu as branché l’infra via docker compose + variables d’environnement.

* L’historique montre clairement la livraison de l’“Epic 4.3 complete - OTel Collector + Jaeger observability”. ([GitHub][2])
* Le `docker-compose.yml` contient les services (collector/jaeger) et les profils associés. ([GitHub][3])
* `.env.example` expose les flags/variables OTel (donc ce n’est pas juste “dans les docs”, c’est prévu dans l’opérationnel). ([GitHub][4])
* Et côté LLM calls, tes drivers appellent un wrapper de trace (`trace_llm_call`) : donc tu instrumentes au bon endroit (au plus près des appels coûteux et critiques). ([GitHub][5])

---

### 1.4. Évolution : Fitness **déterministe** (anti “LLM-as-a-judge”)

C’est un changement très structurant pour fiabiliser une boucle d’auto‑évolution.

* Ajout de `core/evolution/fitness.py` avec une classe **DeterministicFitness** et un set de checks : **ruff**, **mypy**, **bandit**, **pytest** + reporting strict/non‑strict. ([GitHub][6])
* Intégration dans `tiered_validator.py` comme un “Tier 1.5” (après syntax, avant smoke test). ([GitHub][6])
* Ajout d’une suite de tests dédiée (`tests/test_evolution_fitness.py`). ([GitHub][6])

**Impact :** tu réduis fortement le risque de “model collapse” et d’évaluations instables, parce que la qualité de base du code est évaluée par des outils déterministes (ce qui est exactement le bon réflexe). ([GitHub][6])

---

### 1.5. Pipeline LLM : drivers SDK + tests E2E “pas de subprocess”

Tu es en train de consolider le pipeline “SDK-first” (plutôt que CLI subprocess), et ça se voit :

* `OrchestratorV7` passe par une factory async (`AsyncDriverFactory`). ([GitHub][7])
* Tu as un test E2E d’intégration qui vérifie explicitement **qu’aucun `subprocess.Popen` n’est appelé** en mode SDK. ([GitHub][8])
* Côté Claude : driver SDK Anthropic avec streaming, structured outputs via `messages.parse`, prompt caching, response cache, OTel, budget tracking. ([GitHub][5])
* Côté Gemini : driver SDK via `google genai Client`, et usage de l’API telle que documentée (incluant une surface async via `client.aio`). ([GitHub][9])

---

## 2) Mapping “récursif” des interactions (ce que le système fait réellement)

Je te le mappe en couches, du plus visible au plus “mécanique”.

### Niveau 0 — Produits / points d’entrée

D’après le README, tu as au moins :

* un **CLI/REPL** (`nexus7.py`)
* un **Research CLI + Evidence Pack** (`nexus_research.py`)
* un **serveur MCP** côté `core.mcp.server` ([GitHub][10])

👉 C’est important parce que ça te donne déjà une *stratégie produit* possible : “Evidence Pack” + “MCP server” sont des livrables concrets.

---

### Niveau 1 — Orchestration (FSM + phases)

Le flux typique (simplifié) ressemble à :

1. **User input** → REPL
2. REPL → **OrchestratorV7** (FSM)
3. Orchestrator → phases (analyse / exécution / consolidation…)
4. phases → **drivers LLM** (Claude/Gemini) + tools
5. tout est instrumenté → telemetry / logs / traces
6. résultat → retour user + mémorisation ([GitHub][10])

---

### Niveau 2 — Drivers LLM (SDK) + instrumentation + coûts

**AsyncDriverFactory** décide “quel driver concret” selon `driver_mode` + présence des API keys. ([GitHub][5])

Ensuite :

* **AnthropicSDKDriver** :

  * `messages.create()` + `messages.stream()` pour streaming
  * `messages.parse()` pour structured outputs (Pydantic)
  * `cache_control: ephemeral` quand caching activé
  * `trace_llm_call` pour OTel
  * `BudgetTracker.track_cost` (si injecté)
  * `response_cache` (cache applicatif côté NEXUS) ([GitHub][5])

* **GoogleGenAISDKDriver** :

  * `genai.Client(...).models.generate_content` + surface async possible via `client.aio`
  * instrumentation similaire (`trace_llm_call` côté NEXUS) ([GitHub][9])

---

### Niveau 3 — Mémoire (RAG + succès/échecs) devenue “unifiée”

**Memory V2** fait un truc très intéressant : elle encode des succès/échecs comme des “documents virtuels” (chunks) afin de pouvoir les retrouver par sémantique.

* `SuccessMemoryV2.record_success()` → crée un `Chunk(file_path="success_memory://...")` avec `metadata`
* `find_similar_tasks(query)` → `ProjectMemory.retrieve(query)` → filtre les chunks “success_memory://” → reconstruit `SuccessEntry` ([GitHub][11])

**Effet de bord désiré :** tu peux influencer automatiquement le choix de mode (parallel/red_blue/etc.) et éviter les stratégies déjà toxiques via blacklist sémantique. ([GitHub][1])

---

### Niveau 4 — Auto‑évolution durcie par validation déterministe

La pipeline évolution gagne un “garde‑fou” :

* `TieredValidator` appelle `DeterministicFitness`
* `DeterministicFitness` exécute ruff/mypy/bandit/pytest et rend un résultat structuré
* si ok → la mutation passe au niveau suivant, sinon rejet / downgrade ([GitHub][6])

---

### Niveau 5 — Observabilité de bout en bout

Les drivers génèrent des spans OTel (via `trace_llm_call`), ton infra docker peut exporter vers un collector/Jaeger, donc tu as la base pour :

* tracer un “turn” complet (phases → appels LLM → tools)
* corréler coûts/latence/erreurs par provider/model ([GitHub][3])

---

## 3) Erreurs / incohérences à corriger (priorité haute)

### 3.1. **FinOps : BudgetTracker a des prix faux / obsolètes**

Ton `BudgetTracker` mentionne des prix qui ne collent pas à la tarification officielle récente côté Anthropic (Opus 4.6 = **$5 / $25** par million tokens). ([GitHub][12])

Et côté Sonnet 4.5, Anthropic annonce **$3 / $15** par million tokens (pricing “reste le même”). ([Anthropic][13])

Côté Gemini, tu as une page officielle de pricing “Gemini Developer API pricing” — donc tu peux aligner ton tracker sur une source stable. ([Google AI for Developers][14])

**Pourquoi c’est critique :** tout ton contrôle de budgets, early exit, routing économique, alerting OTel, etc., dépend de ces chiffres.

✅ À faire :

* remplacer la table codée en dur par :

  * un fichier `pricing.yaml` versionné + override par env
  * et/ou une “pricing registry” par provider (avec date d’édition)
* ajouter un test unitaire qui échoue si les prix ne matchent pas les valeurs attendues (avec un mécanisme de “valid until date”)
* logguer dans les traces OTel le “pricing_version” utilisé (sinon debugging impossible). ([GitHub][12])

---

### 3.2. Memory V2 : ton scoring “similarité” est **positionnel**, pas sémantique

Dans `SuccessMemoryV2.find_similar_tasks`, tu reconstruis un score via `1.0 - 0.1 * index` au lieu d’utiliser **le score réel** de retrieval. Ça fausse :

* les seuils `min_score`
* le `domain_boost`
* la sélection de `best_mode_for_similar` ([GitHub][11])

✅ À faire :

* faire remonter depuis `ProjectMemory.retrieve()` un tuple `(chunk, score)` (ou enrichir `Chunk` avec `retrieval_score` de façon non persistée)
* propager ce score jusqu’au choix de mode
* ajouter un test “paraphrase” : query A ≈ query B doit rendre un score > X.

---

### 3.3. Memory V2 : extraction de termes via un **ProjectMemory temp** (coût inutile)

`_index_success_entry()` instancie un `ProjectMemory` temporaire juste pour `_extract_terms`. Ça risque d’être :

* coûteux
* source de bugs (config/backends différents)
* non déterministe si la config bouge ([GitHub][11])

✅ À faire :

* extraire `_extract_terms` dans une fonction utilitaire pure (ou la rendre `@staticmethod`)
* ou appeler `self.project_memory._extract_terms` (même si “private”, c’est interne au module).

---

### 3.4. Prompt caching : gros gain… mais attention au **risque multi-tenant**

Anthropic pousse fort le prompt caching (jusqu’à ~90% de savings annoncés). ([Anthropic][15])
Mais des travaux de recherche ont montré que le prompt caching peut créer des **variations de timing** et potentiellement ouvrir des **side-channels** / fuites si caches partagés. ([arXiv][16])

✅ À faire (si NEXUS vise l’entreprise) :

* isoler strictement cache par tenant/workspace (clé = tenant_id + model + system_prompt_hash + prompt_hash)
* option “cache off” quand données sensibles
* monitoring de “cache hit rate” + latence différenciée (sinon tu ne verras pas les leaks potentiels). ([GitHub][5])

---

### 3.5. Tests SDK : tu as 2 tests skip → il faut les “dé-skip”

Ton fichier E2E pipeline a des tests marqués `skip` (streaming + fail-fast sans API key). ([GitHub][8])

✅ À faire :

* corriger l’itération async du mock (`AsyncMock` + async iterator)
* rendre le fail-fast “simple” : si `driver_mode="sdk"` et pas de clé → exception explicite, testable.

---

### 3.6. Fitness déterministe : “graceful degradation” peut devenir un trou de sécurité

Le commit mentionne une dégradation “gracieuse” si les outils ne sont pas dispo. ([GitHub][6])

⚠️ Pour une pipeline d’évolution, “fail open” = tu peux accepter une mutation non évaluée.

✅ À faire :

* en environnement prod : **fail-closed** (si bandit/mypy/pytest introuvables → rejet mutation)
* en dev : fail-open acceptable, mais log + trace OTel “fitness_check_skipped=true”. ([GitHub][6])

---

## 4) Ce qu’il faut faire ensuite (plan d’action concret)

Je te propose un plan en 4 jalons (court → moyen terme). L’idée : **réduire le risque**, **verrouiller les invariants**, puis **accélérer**.

### Jalon 1 — “Truth & Stability” (très court terme)

Objectif : tout ce qui est mesuré et annoncé doit être vrai et reproductible.

1. **Fix BudgetTracker pricing + tests**

* Mettre les prix à jour (Opus 4.6 $5/$25, Sonnet 4.5 $3/$15, Gemini via page pricing officielle). ([GitHub][12])

2. **Fix scoring Memory V2**

* Propager score retrieval réel au lieu du score positionnel. ([GitHub][11])

3. **Dé-skip 2 tests SDK**

* streaming + fail-fast. ([GitHub][8])

**Definition of Done :** un run local “SDK mode” + “mock mode” qui passe sans skip sur un subset.

---

### Jalon 2 — “FinOps + contrôle de thrashing” (court terme)

Objectif : empêcher l’essaim de se ruiner en tokens et de boucler.

Actions :

* exploiter `BudgetTracker` pour déclencher :

  * **early exit** de débat
  * “judge/fast path” quand budget atteint
* renforcer le routing économique : modèles cheap pour validation/tests, chers pour synthèse finale (ton infra drivers + router s’y prête). ([GitHub][5])

---

### Jalon 3 — “Confiance & debug” (moyen terme)

Objectif : rendre explicable et déboggable.

* tirer parti d’OTel + event logs pour faire du **time-travel debugging** (rejouer un turn à partir d’un `trace_id`)
* exposer dans l’UI (Cerebro) au minimum :

  * timeline phases
  * appels LLM (coût/latence/erreur)
  * décisions (mode choisi + justification mémoire V2) ([GitHub][3])

---

### Jalon 4 — “Sécurité continue + évolution gouvernée” (moyen/long terme)

Objectif : éviter qu’une évolution + outils = surface d’attaque.

* verrouiller les politiques : sandbox obligatoire en prod, fail-closed si indispo
* ajouter un “shadow red-team agent” qui teste prompt injections / SSRF / escalade tool sur un environnement isolé (surtout si MCP/tools).
* faire que toute mutation passe : deterministic fitness + policy checks + review gates. ([GitHub][6])

---

## 5) Direction à suivre (vision “future-proof” mais pragmatique)

Tu as deux chemins possibles. Le bon choix dépend de ton objectif (R&D vs produit).

### Direction A — “Produit” (recommandée si tu veux livrer en 2026)

Se concentrer sur ce que ton README vend déjà :

* **Research CLI + Evidence Pack**
* **MCP Server**
  → c’est vendable comme “moteur de recherche et d’audit LLM traçable”, et l’OTel + mémoire V2 + budgets servent directement ce produit. ([GitHub][10])

### Direction B — “AI‑OS / Hive Mind” (recommandée si objectif labo)

Tu continues à empiler : essaim, auto‑évolution, meta‑raisonnement, etc.
→ mais il faut alors **institutionnaliser** : invariants, budgets, replay, gouvernance des mutations, sécurité continue. Le deterministic fitness est un énorme pas dans cette direction. ([GitHub][6])

---

## Synthèse ultra-pratique

1. **Corrige BudgetTracker** (prix Anthropic/Gemini) + tests → sinon toute ta FinOps est fausse. ([GitHub][12])
2. **Corrige Memory V2 scoring** (score réel, pas position) + évite `ProjectMemory` temp. ([GitHub][11])
3. **Dé-skip les tests SDK** (streaming + fail-fast). ([GitHub][8])
4. **Fail-closed en prod** sur deterministic fitness & sandbox. ([GitHub][6])
5. **Cap produit** : Evidence Pack + MCP comme “offre 2026”, et tu utilises OTel + budgets + mémoire V2 pour la crédibilité entreprise. ([GitHub][10])

Si tu veux, je peux te produire ensuite une **checklist “Definition of Done v12.4.2”** (format ticketing) en priorisant ce qui débloque le plus vite une version réellement exploitable (avec critères testables et traces attendues).

[1]: https://github.com/yannabadie/NEXUS/commit/155626748f722adb2375a4d2b17c32d95c0eff71 "feat(V12.4.1): Epic 1.4 - LanceDB-backed memory V2 with semantic retr… · yannabadie/NEXUS@1556267 · GitHub"
[2]: https://github.com/yannabadie/NEXUS/commits/NX-CG/ "Commits · yannabadie/NEXUS · GitHub"
[3]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/docker-compose.yml "raw.githubusercontent.com"
[4]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/.env.example "raw.githubusercontent.com"
[5]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/core/drivers/anthropic_sdk_driver.py "raw.githubusercontent.com"
[6]: https://github.com/yannabadie/NEXUS/commit/6eaf1e6 "feat(V12.4): Epic 4.2 - Deterministic Fitness Function for Evolution · yannabadie/NEXUS@6eaf1e6 · GitHub"
[7]: https://github.com/yannabadie/NEXUS/commit/ad1fea8b01f8910d104824a3e27fe7e94a097a85 "feat(V12.4): Epic 4.3 complete - OTel Collector + Jaeger observability · yannabadie/NEXUS@ad1fea8 · GitHub"
[8]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/tests/test_sdk_e2e_pipeline.py "raw.githubusercontent.com"
[9]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/core/drivers/google_genai_sdk_driver.py "raw.githubusercontent.com"
[10]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/README.md "raw.githubusercontent.com"
[11]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/core/memory/success_memory_v2.py "raw.githubusercontent.com"
[12]: https://raw.githubusercontent.com/yannabadie/NEXUS/NX-CG/core/telemetry/budget_tracker.py "raw.githubusercontent.com"
[13]: https://www.anthropic.com/news/claude-sonnet-4-5?utm_source=chatgpt.com "Introducing Claude Sonnet 4.5"
[14]: https://ai.google.dev/gemini-api/docs/pricing?utm_source=chatgpt.com "Gemini Developer API pricing"
[15]: https://www.anthropic.com/claude/opus?utm_source=chatgpt.com "Claude Opus 4.6"
[16]: https://arxiv.org/abs/2502.07776?utm_source=chatgpt.com "Auditing Prompt Caching in Language Model APIs"
