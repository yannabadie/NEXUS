# ROADMAP NEXUS V7.5 "HIVE MIND"

**Version**: 7.5.1 | **Status**: Active | **Last Updated**: 2025-12-03
**Vision**: Cœur d'Intelligence Collaborative Générant des Agents Spécialisés

---

## 1. Vision Stratégique

**NEXUS n'est plus une quête vers l'ASI.**
NEXUS est une **plateforme de collaboration multi-agents** capable de:
1. **Analyser** les besoins complexes
2. **Générer** des agents spécialisés (enfants qui coexistent)
3. **Orchestrer** leur collaboration via Hybrid Swarm
4. **Évoluer** par sélection des meilleures configurations

### Coeur de Puissance
```
GEMINI 3 Pro  <═══════════════>  CLAUDE Opus 4.5
     │           SYMBIOSE            │
     │         COGNITIVE             │
     └──────────────┬────────────────┘
                    │
            6 MODES SWARM
     PARALLEL │ SEQUENTIAL │ LEAD_SUPPORT
     PING_PONG │ SPECIALIST │ RED_BLUE
```

---

## 2. Phases Complétées (V7.0 → V7.5)

### Phase 1: Activation Swarm ✅
- [x] Commandes `/swarm`, `/swarm-status` ajoutées
- [x] `swarm_auto_route=True` par défaut (MODERATE+ tasks)
- [x] 6 modes de collaboration fonctionnels

### Phase 2: Refonte Vision ✅
- [x] MISSION.md réécrit (exit ASI → Cœur Collaboratif)
- [x] CLAUDE.md mis à jour (Agent Factory Mission)

### Phase 3: Déblocage Évolution ✅
- [x] Red Team optionnel (`RED_TEAM_MANDATORY=False`)
- [x] Seuil abaissé à 0.60 (était 0.80)

### Phase 4: Architecture FSM ✅
- [x] États SWARM_* documentés comme [RESERVED]
- [x] Swarm fonctionne via `process_with_swarm()` (bypass FSM)

### Phase 5: Agent Factory ✅
- [x] `/spawn <role>` créé agents dans `workspace/agents/`
- [x] `/agents` liste les agents spawnés

### Phase 6: Robustesse JSON ✅
- [x] `core/utils/json_extractor.py` implémenté
- [x] Intégré dans Gemini driver et REPL
- [x] Support multi-format (markers, markdown, braces)

### Phase 7: Task Fitness (ex-ASI) ✅
- [x] Suppression benchmarks simulés
- [x] Implémentation scores baseline honnêtes
- [x] Préparation pour Auto-Memory

---

## 3. Phases À Venir (V7.5 → V8.0)

### Phase 9: Fast Path (UX)
**Objectif**: Réponses instantanées pour requêtes triviales

Source: ROADMAP_V7-stable.md

- [ ] Détection requêtes simples ("Hello", "Merci")
- [ ] Bypass FSM pour réponses directes
- [ ] Réduction latence perçue

### Phase 10: Auto-Mémoire des Succès (Priorité Haute)
**Objectif**: NEXUS se souvient de ce qui a fonctionné

UX cible: NEXUS apprend de ses succès et échecs pour s'améliorer.

- [ ] `workspace/memory/successes.jsonl` - Log des méthodes efficaces
- [ ] `workspace/memory/failures.jsonl` - Log des échecs à éviter
- [ ] Scoring automatique des patterns (mode swarm, agent, approche)
- [ ] Consultation mémoire avant délibération
- [ ] "J'ai résolu un problème similaire avec PING_PONG, je réutilise"

### Phase 11: Squad System (Topologies Dynamiques)
**Objectif**: Équipes d'agents configurables

Source: Analyse Gemini + GPTSwarm paper

- [ ] Commande `/squad <file>` pour charger définition équipe
- [ ] Format `squad.json` avec topologies (STAR, MESH, PIPELINE)
- [ ] Communication inter-agents via lead ou mesh

```json
{
  "name": "E-commerce Team",
  "lead": "Main_Nexus",
  "workers": ["SQL_Expert", "Vue_Expert"],
  "topology": "STAR"
}
```

---

## 4. Phase 12: Extensions Cognitives (Innovation)

Ces phases intègrent les concepts avancés identifiés dans les archives V8.

### Phase 12.1: MNEMOSYNE (Mémoire Sémantique)
**Objectif**: Remplacer la recherche exacte par une recherche sémantique.

*   **Concept**: Indexer les logs de succès (`successes.jsonl`) avec des embeddings.
*   **Apport**: "J'ai trouvé une tâche similaire résolue la semaine dernière" (même si les mots clés diffèrent).
*   **Tech**: ChromaDB (local) ou FAISS.

### Phase 12.2: OUROBOROS (Background Evolution)
**Objectif**: Auto-amélioration sans blocage utilisateur.

*   **Concept**: "Shadow Nexus" qui tourne en arrière-plan.
*   **Mécanisme**:
    *   Détection d'erreur récurrente (ex: tool failure).
    *   Lancement d'un worker détaché (`nexus7.py --worker`).
    *   Isolation dans `_shadow_workspace`.
    *   Notification utilisateur uniquement en cas de succès ("J'ai fixé mes prompts, appliquer ?").

### Phase 12.3: CORTEX (Pont MCP)
**Objectif**: Standardisation des outils via Model Context Protocol.

*   **Concept**: Remplacer les outils hardcodés par des clients MCP.
*   **Apport**: Connectivité universelle (GitHub, Drive, Postgres) via des serveurs standards.
*   **Tech**: `mcp-python` SDK, découverte dynamique des capacités.

---

## 5. Métriques de Succès HIVE MIND

| Métrique | Objectif |
|----------|----------|
| Swarm Task Success Rate | >90% |
| Agent Spawn Success | >95% |
| JSON Parse Errors | <1% |
| User Latency (trivial) | <2s |
| User Latency (complex) | <30s |
| Test Coverage | >70% |

---

## 6. Garde-fous Immuables

1. **KERNEL.py**: Jamais modifié
2. **Collaboration égalitaire**: Gemini + Claude = partenaires
3. **Coexistence**: Agents spawned persistent (pas de remplacement)
4. **Sécurité**: SandboxPolicy appliquée partout
5. **Simplicité**: Operation Ockham (supprimer avant d'ajouter)