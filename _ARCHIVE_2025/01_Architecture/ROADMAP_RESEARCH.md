# NEXUS - ROADMAP de Recherche Expérimentale
## Co-créée par Claude Code & Gemini CLI
### Version 1.0 - 18/11/2025

---

## Vision

NEXUS est un **système d'orchestration multi-IA généraliste** capable de résoudre des problèmes complexes en combinant les forces de Claude Code et Gemini CLI. Cette roadmap définit les expérimentations nécessaires pour cartographier ses capacités et identifier les configurations optimales.

---

## 1. DOMAINES D'APPLICATION

### 1.1 Domaines Prioritaires (MES iDACS)

| Domaine | Description | Lead |
|---------|-------------|------|
| **Analyse SQL/ERP** | Schémas CEGID, requêtes métier | Gemini |
| **Documentation Technique** | Specs, ICD, TAD | Claude |
| **Conformité AS9100** | Audit, traçabilité | Mixte |
| **Modélisation ISA-88/95** | Process segments, B2MML | Gemini |
| **Reporting Exécutif** | CODIR, KPIs, synthèses | Claude |

### 1.2 Domaines Génériques à Explorer

| Domaine | Cas d'Usage | Potentiel |
|---------|-------------|-----------|
| **Code Legacy** | Refactoring monorepos, migration | ★★★★★ |
| **Security Audit** | Vulnérabilités, secrets, OWASP | ★★★★★ |
| **Data Science** | EDA, ML pipelines, visualisation | ★★★★☆ |
| **Literature Review** | Synthèse papers, état de l'art | ★★★★★ |
| **Infrastructure** | IaC audit, Terraform, Ansible | ★★★★☆ |
| **Financial Analysis** | Due diligence, modélisation | ★★★★☆ |
| **Project Management** | Planning, risques, RACI | ★★★★★ |
| **Technical Support L3** | Root cause analysis, logs | ★★★★★ |
| **Contract Analysis** | NDA, SLA, conformité légale | ★★★★☆ |
| **API Design** | OpenAPI, gRPC, documentation | ★★★★☆ |

---

## 2. MODES DE FONCTIONNEMENT

### 2.1 Cartographie des Modes

| Mode | Lead | Pattern | Use Case |
|------|------|---------|----------|
| **Analyste** | Gemini | Séquentiel | Ingestion massive → Insights |
| **Développeur** | Claude | Séquentiel | Spec → Code → Tests |
| **Architecte** | Claude | Hiérarchique | Plan → Analyse → Implémentation |
| **Auditeur** | Gemini | Séquentiel | Scan complet → Rapport |
| **Chercheur** | Gemini | Séquentiel | Sources → Synthèse |
| **Brainstorm** | Dynamique | Ping-Pong | Idéation créative |
| **Validateur** | Claude | Ping-Pong | Génération → Critique → Amélioration |

### 2.2 Configuration par Mode

```yaml
# mode_analyste.yaml
name: Analyste
lead: gemini
pattern: sequential
gemini_first: true
claude_callback: ["synthesize", "save_file", "format_report"]
context_threshold: 100000  # tokens avant délégation
timeout: 120000

# mode_developpeur.yaml
name: Développeur
lead: claude
pattern: sequential
claude_first: true
gemini_callback: ["analyze_codebase", "find_dependencies", "check_patterns"]
max_iterations: 5
```

---

## 3. MÉTA-ARCHITECTURE DYNAMIQUE

### 3.0 Création d'Architectures à la Volée

**Concept clé** : NEXUS ne crée pas juste des réponses - il crée des architectures d'agents adaptées, les sauvegarde et les réutilise.

| Composant | Technologie | Description |
|-----------|-------------|-------------|
| **Claude Agents** | `.claude/agents/*.md` + `--agents JSON` | Agents déclaratifs, résumables |
| **Gemini ADK** | Python + BaseAgent | Agents programmatiques, orchestrables |
| **Bibliothèque** | YAML + ChromaDB embeddings | Stockage et matching sémantique |
| **Loader** | Python | Instanciation dynamique |

### Workflow de Réutilisation

```
Requête → [Matcher sémantique] → Architecture existante?
                                      ↓ Oui         ↓ Non
                               Charger & Exécuter   Créer nouvelle
                                                    → Sauvegarder
```

### Structure Bibliothèque

```
06_Architecture_Library/
├── index.yaml              # Index + embeddings
├── audit/                  # Architectures d'audit
├── development/            # Architectures de dev
├── research/               # Architectures de recherche
├── analysis/               # Architectures d'analyse
└── _templates/             # Templates de base
```

Voir **META_ARCHITECTURE.md** pour les détails techniques complets.

---

## 4. MÉTHODOLOGIES À TESTER

### 4.1 Patterns de Collaboration

| Pattern | Description | Quand l'utiliser |
|---------|-------------|------------------|
| **Séquentiel** | A → B → Output | Analyse + Action |
| **Parallèle** | [A, B] → Merge | Tâches indépendantes |
| **Ping-Pong** | A ↔ B ↔ A... | Raffinement itératif |
| **Hiérarchique** | A → B → A → C | Orchestration complexe |
| **Consensus** | A + B → Compare → Resolve | Décisions critiques |

### 3.2 Architectures Scientifiques

| Framework | Application NEXUS | À Tester |
|-----------|-------------------|----------|
| **MoE** | Routage intelligent vers expert | Classifier de requêtes |
| **ACE** | Couches cognitives (6 layers) | Aspirational → Task |
| **MARL** | Apprentissage par feedback | Amélioration continue |
| **Cross-Team** | Équipes spécialisées | Claude-team vs Gemini-team |
| **Evolving Orchestration** | Adaptation dynamique | RL pour routing |

---

## 4. PLAN DE TESTS EN BATTERIE

### Phase 1 : Tests Unitaires de Capacité (Semaine 1)

| Test ID | Nom | Description | Métriques |
|---------|-----|-------------|-----------|
| T1.1 | **Context Limit** | Charger fichiers croissants jusqu'à échec | Max tokens, dégradation qualité |
| T1.2 | **Callback Latency** | Mesurer temps Claude→Gemini→Claude | Latence moyenne, p95 |
| T1.3 | **Session Persistence** | 10 échanges successifs avec --resume | Rétention contexte (%) |
| T1.4 | **Error Recovery** | Injecter erreurs, observer récupération | Taux récupération |
| T1.5 | **Hallucination Rate** | Questions pièges avec vérité connue | Taux hallucination |

### Phase 2 : Tests de Pattern (Semaine 2)

| Test ID | Pattern | Tâche | Métriques |
|---------|---------|-------|-----------|
| T2.1 | **Séquentiel** | Analyser logs (500 pages) → Rapport incident | Temps, précision cause racine |
| T2.2 | **Ping-Pong** | Co-écrire algo complexe (VaR, Monte Carlo) | Itérations, qualité code |
| T2.3 | **Hiérarchique** | Créer microservice complet | Autonomie, succès deploy |
| T2.4 | **Parallèle** | Analyser frontend ET backend | Temps gagné, cohérence |
| T2.5 | **Consensus** | Décision architecture avec désaccord | Résolution, qualité décision |

### Phase 3 : Tests de Mode (Semaine 3)

| Test ID | Mode | Tâche Complexe | Baseline Comparaison |
|---------|------|----------------|----------------------|
| T3.1 | **Analyste** | Audit complet codebase 50K lignes | Gemini seul |
| T3.2 | **Développeur** | Implémenter feature OAuth complet | Claude seul |
| T3.3 | **Architecte** | Design system distribué | Claude seul |
| T3.4 | **Auditeur** | Audit AS9100 documentation projet | Gemini seul |
| T3.5 | **Chercheur** | Synthèse 20 papers ML | Gemini seul |
| T3.6 | **Brainstorm** | Proposer 10 features innovantes | Les deux seuls |

### Phase 4 : Tests de Robustesse (Semaine 4)

| Test ID | Risque | Scénario | Success Criteria |
|---------|--------|----------|------------------|
| T4.1 | **Infinite Loop** | Tâche ambiguë sans critère d'arrêt | Détection et sortie |
| T4.2 | **Hallucination Amplification** | Chaîne de 5 analyses | Pas de drift factuel |
| T4.3 | **Context Drift** | Session 20+ échanges | Rappel info début >80% |
| T4.4 | **Conflict Resolution** | Désaccord sur même données | Convergence raisonnable |
| T4.5 | **Tool Misuse** | Demandes hors capacité | Refus approprié |
| T4.6 | **Adversarial Input** | Prompt injection croisé | Résistance |

---

## 5. MÉTRIQUES DE SUCCÈS

### 5.1 Métriques Primaires

| Métrique | Formule | Cible |
|----------|---------|-------|
| **Score Synergie** | Qualité_NEXUS / max(Claude_seul, Gemini_seul) | > 1.2 |
| **Efficacité** | Qualité / (Tokens + API_calls) | Maximiser |
| **Autonomie** | Succès_sans_intervention / Total | > 85% |
| **Vitesse** | Temps_NEXUS / Temps_humain | < 0.1 |
| **Précision** | Résultats_corrects / Total | > 95% |

### 5.2 Métriques Secondaires

| Métrique | Description | Mesure |
|----------|-------------|--------|
| **Consistance** | Même input → même output | Test répété 5x |
| **Calibration** | Confiance corrélée à précision | Régression conf/précision |
| **Coût** | Tokens totaux par tâche | Monitoring API |
| **UX** | Satisfaction utilisateur | Score 1-10 |

### 5.3 Matrice de Performance par Mode

| Mode | Synergie | Autonomie | Vitesse | Use When |
|------|----------|-----------|---------|----------|
| Analyste | ? | ? | ? | À mesurer |
| Développeur | ? | ? | ? | À mesurer |
| Architecte | ? | ? | ? | À mesurer |
| ... | | | | |

---

## 6. RISQUES ET EDGE CASES

### 6.1 Risques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Boucle infinie | Moyenne | Bloquant | Compteur max itérations |
| Amplification hallucination | Moyenne | Critique | Fact-checking croisé |
| Perte contexte | Haute | Qualité | --resume systématique |
| Coût excessif | Moyenne | Budget | Quotas par tâche |
| Conflit non résolu | Faible | Bloquant | Escalade utilisateur |
| Prompt injection | Faible | Sécurité | Validation inputs |

### 6.2 Edge Cases à Tester

1. **Requête vide** : Comportement avec ""
2. **Requête géante** : 1M tokens input
3. **Requête contradictoire** : "Fais X et ne fais pas X"
4. **Timeout cascade** : Gemini timeout → Claude bloqué
5. **Session corrompue** : --resume avec session invalide
6. **Langue mixte** : FR/EN/Code dans même requête
7. **Output conflictuel** : Claude et Gemini désaccord
8. **Récursion** : "Demande à Claude de me demander de..."

---

## 7. PLANNING DE RECHERCHE

### Timeline

```
Semaine 1 (18-24 Nov)
├── Jour 1-2 : Tests unitaires T1.1-T1.5
├── Jour 3-4 : Analyse résultats, ajustements
└── Jour 5 : Documentation Phase 1

Semaine 2 (25 Nov - 1 Dec)
├── Jour 1-2 : Tests patterns T2.1-T2.5
├── Jour 3-4 : Comparaisons, benchmarks
└── Jour 5 : Documentation Phase 2

Semaine 3 (2-8 Dec)
├── Jour 1-3 : Tests modes T3.1-T3.6
├── Jour 4 : Calcul Score Synergie
└── Jour 5 : Documentation Phase 3

Semaine 4 (9-15 Dec)
├── Jour 1-3 : Tests robustesse T4.1-T4.6
├── Jour 4 : Compilation résultats
└── Jour 5 : Rapport final + Recommandations
```

### Livrables

| Semaine | Livrable | Format |
|---------|----------|--------|
| S1 | Rapport Capacités | TEST_RESULTS_CAPACITY.md |
| S2 | Rapport Patterns | TEST_RESULTS_PATTERNS.md |
| S3 | Matrice Modes | MODE_PERFORMANCE_MATRIX.md |
| S4 | Rapport Final | NEXUS_RESEARCH_REPORT.md |
| S4 | Guide Configuration | NEXUS_CONFIG_GUIDE.md |

---

## 8. PROCHAINES ACTIONS IMMÉDIATES

### Aujourd'hui (18/11)

1. [ ] Créer structure dossiers tests
2. [ ] Implémenter script de test automatisé
3. [ ] Exécuter T1.1 (Context Limit)
4. [ ] Exécuter T1.2 (Callback Latency)
5. [ ] Documenter premiers résultats

### Cette Semaine

6. [ ] Compléter tous tests Phase 1
7. [ ] Créer dashboard résultats
8. [ ] Identifier ajustements architecture
9. [ ] Préparer tests Phase 2

---

## 9. PATTERN SAUVEGARDE ÉTAT CLAUDE→GEMINI

### Problème
Claude a 200K tokens, risque de perte de contexte lors d'auto-compaction.

### Solution
Utiliser Gemini (1M tokens) comme mémoire étendue.

### Procédure
```bash
# 1. Avant fin session Claude, sauvegarder état
gemini --resume latest -p "NEXUS SAUVEGARDE: [état complet]"

# 2. Sauvegarder aussi dans fichier (backup)
Write → 20_NEXUS/05_Documentation/SESSION_STATE_[DATE].md

# 3. Nouvelle session Claude, récupérer
gemini --resume latest -p "NEXUS: Donne-moi l'état sauvegardé"
```

### Fichiers État
- `SESSION_STATE_20251118.md` - État session actuelle

---

## 10. QUESTIONS OUVERTES

### À Résoudre par Expérimentation

1. **Seuil de délégation optimal** : À partir de combien de tokens déléguer à Gemini ?
2. **Nombre d'itérations ping-pong** : Combien avant rendements décroissants ?
3. **Format de callback optimal** : JSON structuré vs texte libre ?
4. **Gestion des erreurs** : Retry vs escalade vs abandon ?
5. **Persistance cross-session** : Fichiers vs DB vs KB ?

### À Décider avec Utilisateur

1. Priorité des domaines d'application
2. Critères de succès métier
3. Contraintes de coût/temps
4. Niveau d'autonomie souhaité

---

## 10. NOTES DE CONCEPTION

### Principes Directeurs

1. **Complémentarité** : Utiliser les forces, compenser les faiblesses
2. **Transparence** : Toujours montrer le raisonnement
3. **Vérité** : Avouer les incertitudes (confiance 1-5)
4. **Adaptabilité** : Changer de mode selon la tâche
5. **Efficacité** : Minimiser tokens et temps

### Inspirations Scientifiques

- **MoE** : Routing intelligent vers l'expert approprié
- **ACE** : Architecture cognitive en couches
- **MARL** : Apprentissage par feedback utilisateur
- **Cross-Team** : Équipes spécialisées collaboratives

---

*ROADMAP co-créée le 18/11/2025*
*Par : Claude Code (Sonnet 4.5) & Gemini CLI (2.5 Pro)*
*Pour : Yann ABADIE - Projet NEXUS*
*Version : 1.0*
