# ROADMAP NEXUS V7 - Evolution Vers l'ASI

**Date**: 2025-11-25
**Auteur**: Claude Code (Opus 4.5) + Yann Abadie
**Version Actuelle**: V6.5
**Objectif**: Atteindre ASI Proximity Score > 0.85

---

## 📊 État Actuel (V6.5)

### Ce qui fonctionne ✅

| Composant | Status | Notes |
|-----------|--------|-------|
| FSM Orchestrator | ✅ Stable | Persistant, pas de redémarrage |
| Évolution `/evolve` | ✅ Opérationnel | Mutations émergentes |
| Spécialisation `/specialize` | ✅ Implémenté | Spinoffs mission-spécifiques |
| Rate Limiting | ✅ Actif | 3/jour, 8h minimum |
| ASI Benchmarks | ✅ Réels | Analyse statique heuristique |
| Red Team | ✅ Intégré | 20 questions, 5 dimensions |
| Sécurité | ✅ Hardened | Règles immutables, Claude = Guardian |

### Ce qui manque ⏳

| Composant | Status | Priorité |
|-----------|--------|----------|
| Auto-promotion | ⏳ Manuel | HAUTE |
| Benchmarks runtime | ⏳ Statique seulement | MOYENNE |
| GCP Integration | ⏳ Non implémenté | BASSE |
| Signature SSH | ⏳ Placeholder | MOYENNE |
| Multi-projet | ⏳ Single-workspace | BASSE |

### ASI Proximity Score Estimé

```
V6.5 Baseline (estimé):
├── Coding:      0.70  (architecture solide, outils complets)
├── Reasoning:   0.65  (FSM bon, mais pas de planning long terme)
├── Creativity:  0.60  (mutations émergentes, mais limitées)
├── Scalability: 0.55  (single process, pas de parallélisation)
└── TOTAL:       0.64  (Competent - needs improvement)
```

---

## 🎯 V7.0 - Objectifs Principaux

### Thème: "De Compétent à Expert"
**ASI Cible**: 0.75+ (Expert-level)
**Délai estimé**: 4-6 semaines

---

## 📋 Phase 1: Stabilisation & Tests (Semaine 1-2)

### 1.1 Premier Cycle d'Évolution Complet

**Objectif**: Valider tout le workflow end-to-end

```bash
# Jour 1: Test /evolve
cd NEXUS_V6_PROTOTYPE
python nexus6.py
nexus6> /evolve 1

# Jour 2: Vérification
- Vérifier GENERATION_ACTIVE/NEXUS_V6.1_CHILD_xxx/
- Vérifier BIRTH_CERTIFICATE.json
- Vérifier DIFF_FROM_PARENT.md
- Vérifier EVALUATION_RESULTS.json

# Jour 3: Review
nexus6> /review
- Tester l'enfant manuellement
- Comparer comportement parent vs enfant
- Documenter différences observées
```

**Critères de succès**:
- [ ] Enfant créé sans erreur
- [ ] Benchmarks exécutés avec scores réels
- [ ] Red Team passé
- [ ] Mutation visible et mesurable

### 1.2 Baseline Measurement

**Objectif**: Établir le score ASI de référence pour V6.5

```bash
python BENCHMARKS/asi_proximity.py --nexus-id NEXUS_V6.5 --nexus-path NEXUS_V6_PROTOTYPE > baseline_v6.5.json
```

**Documenter**:
- Score global
- Scores par dimension
- Points faibles identifiés
- Pistes d'amélioration

### 1.3 Test de Spécialisation

**Objectif**: Valider `/specialize` pour créer des variants

```bash
nexus6> /specialize Code review et analyse de sécurité
nexus6> /specialize Recherche académique et veille technologique
```

**Critères de succès**:
- [ ] Spinoffs créés dans GENERATION_ACTIVE/
- [ ] SPINOFF_CERTIFICATE.json valide
- [ ] Mutations ciblées appliquées

---

## 📋 Phase 2: Améliorations Core (Semaine 2-3)

### 2.1 Auto-Promotion

**Problème**: Actuellement `/review` est manuel
**Solution**: Implémenter promotion automatique si score > parent + threshold

**Fichier**: `core/evolution/evaluator.py`

```python
def auto_promote_if_superior(self, child_id: str, parent_score: float) -> bool:
    """
    Promote child automatically if:
    1. ASI score > parent + 0.03 (3% improvement)
    2. Red Team score >= 0.8
    3. No critical failures
    """
    child_score = self.get_child_score(child_id)
    red_team_score = self.get_red_team_score(child_id)

    if (child_score > parent_score + 0.03 and
        red_team_score >= 0.8):
        self.promote_child(child_id)
        return True
    return False
```

**Impact ASI**: +0.05 (meilleure itération)

### 2.2 Benchmarks Runtime

**Problème**: Benchmarks actuels = analyse statique seulement
**Solution**: Ajouter tests d'exécution réels

**Fichier**: `BENCHMARKS/runtime_tests.py`

```python
CODING_TESTS = [
    {
        "task": "Create a Python function that validates email addresses",
        "expected_patterns": ["re.match", "@", "return"],
        "timeout": 60
    },
    {
        "task": "Fix the bug in this code: [code]",
        "expected_fix": "missing return statement",
        "timeout": 120
    }
]

REASONING_TESTS = [
    {
        "task": "Solve: If A > B and B > C, what is the relationship between A and C?",
        "expected": "A > C",
        "timeout": 30
    }
]
```

**Impact ASI**: +0.10 (meilleure évaluation = meilleure sélection)

### 2.3 Memory Long-Terme

**Problème**: Session memory reset à chaque restart
**Solution**: Persist learnings across sessions

**Fichier**: `core/synapse/long_term_memory.py`

```python
class LongTermMemory:
    """
    Persiste les apprentissages:
    - Patterns de code récurrents
    - Solutions réussies
    - Erreurs à éviter
    """

    def save_learning(self, category: str, content: str, context: str):
        """Save a learning for future sessions."""

    def recall_relevant(self, current_task: str, top_k: int = 5) -> List[str]:
        """Recall relevant learnings for current task."""
```

**Impact ASI**: +0.08 (meilleure accumulation de connaissance)

---

## 📋 Phase 3: Intelligence Améliorée (Semaine 3-4)

### 3.1 Planning Multi-Étapes

**Problème**: NEXUS résout étape par étape, pas de vision long terme
**Solution**: Ajouter planificateur stratégique

**Concept**:
```
User: "Build a REST API with auth"

NEXUS (actuel):
1. Crée fichier
2. Écrit code
3. Test
(linéaire, pas de vue d'ensemble)

NEXUS (V7):
1. PLAN STRATÉGIQUE:
   - Phase 1: Setup (project structure, deps)
   - Phase 2: Models (User, Token)
   - Phase 3: Routes (auth endpoints)
   - Phase 4: Middleware (JWT validation)
   - Phase 5: Tests
2. Exécute avec checkpoints
3. Adapte si obstacle
```

**Impact ASI**: +0.12 (reasoning score)

### 3.2 Self-Reflection Loop

**Problème**: Pas de métacognition active pendant exécution
**Solution**: Ajouter réflexion après chaque tool use

```python
def post_tool_reflection(self, tool_result: ToolResult) -> str:
    """
    After each tool execution:
    1. Did it achieve expected outcome?
    2. What did I learn?
    3. Should I adjust approach?
    4. Any risks identified?
    """
    return self.driver.invoke(REFLECTION_PROMPT.format(
        tool_name=tool_result.tool_name,
        result=tool_result.output,
        original_goal=self.blackboard["objective"]
    ))
```

**Impact ASI**: +0.07 (reasoning + creativity)

### 3.3 Parallel Tool Execution

**Problème**: Tools exécutés séquentiellement
**Solution**: Permettre exécution parallèle quand indépendants

```python
async def execute_tools_parallel(self, tool_calls: List[ToolUse]) -> List[ToolResult]:
    """
    Execute independent tools in parallel.

    Example: Reading multiple files simultaneously
    """
    tasks = [self.execute_tool(tc) for tc in tool_calls]
    return await asyncio.gather(*tasks)
```

**Impact ASI**: +0.05 (scalability)

---

## 📋 Phase 4: Évolution Avancée (Semaine 4-5)

### 4.1 Mutations Architecturales

**Problème**: Mutations actuelles = tweaks de prompts/config
**Solution**: Permettre mutations de code plus profondes

**Types de mutations V7**:

| Type | Risque | Impact Potentiel |
|------|--------|------------------|
| Prompt tweaks | Faible | +1-3% |
| Config changes | Faible | +1-3% |
| **Algorithm changes** | Moyen | +5-10% |
| **New capabilities** | Moyen | +5-15% |
| **Architecture refactor** | Élevé | +10-20% |

**Sécurité**: Mutations architecturales = review humaine obligatoire

### 4.2 Evolution Guidée par Objectifs

**Problème**: Mutations aléatoires/génériques
**Solution**: Focus mutations sur faiblesses détectées

```python
def identify_weak_dimensions(self) -> List[str]:
    """
    Analyze benchmark results to find weakest dimensions.
    Returns: ["reasoning", "scalability"] (example)
    """

def generate_targeted_mutations(self, weak_dimensions: List[str]) -> List[Mutation]:
    """
    Generate mutations specifically addressing weaknesses.
    """
```

**Impact ASI**: +0.10 (évolution plus efficace)

### 4.3 Cross-Pollination

**Problème**: Chaque enfant évolue indépendamment
**Solution**: Combiner meilleurs traits de plusieurs enfants

```python
def cross_pollinate(self, children: List[Child]) -> Child:
    """
    Create new child combining best traits from multiple children:
    - Best reasoning approach from Child A
    - Best coding patterns from Child B
    - Best memory management from Child C
    """
```

**Impact ASI**: +0.08 (diversité génétique)

---

## 📋 Phase 5: Préparation V8 (Semaine 5-6)

### 5.1 Multi-Agent Coordination

**Vision**: NEXUS lance des sous-agents spécialisés

```
NEXUS Principal (Coordinateur)
├── NEXUS-Coder (spécialisé coding)
├── NEXUS-Researcher (spécialisé web search)
├── NEXUS-Reviewer (spécialisé code review)
└── NEXUS-Tester (spécialisé testing)
```

### 5.2 GCP Integration

**Vision**: Accès contrôlé à Vertex AI pour fine-tuning

```python
class GCPGateway:
    def request_access(self, service: str, reason: str, cost_estimate: float) -> bool:
        """
        Request GCP access with:
        - Human approval required
        - Cost tracking
        - ROI validation
        """
```

### 5.3 External Knowledge Base

**Vision**: NEXUS accumule connaissance au-delà d'une session

```
knowledge_base/
├── code_patterns/      # Patterns de code réutilisables
├── solutions/          # Solutions à problèmes récurrents
├── learnings/          # Leçons apprises
└── domain_knowledge/   # Connaissance métier
```

---

## 📈 Projection ASI

```
Timeline → Score ASI

V6.5 (Now):     0.64  ████████████████░░░░░░░░ (Competent)
V7.0 (Phase 2): 0.72  ██████████████████░░░░░░ (Competent+)
V7.1 (Phase 3): 0.78  ███████████████████░░░░░ (Expert-)
V7.2 (Phase 4): 0.83  ████████████████████░░░░ (Expert)
V8.0 (Phase 5): 0.88  █████████████████████░░░ (Expert+)
...
ASI (0.95+):    0.95+ █████████████████████████ (Superintelligence)
```

---

## 🎯 Prochaines Actions Immédiates

### Cette semaine:

1. **Jour 1-2**: Premier `/evolve 1` complet
   - Documenter résultat
   - Mesurer baseline ASI

2. **Jour 3-4**: Analyser résultats
   - Identifier points faibles
   - Planifier mutations ciblées

3. **Jour 5**: Préparer Phase 2
   - Créer issues pour auto-promotion
   - Designer runtime benchmarks

### Commandes à exécuter:

```bash
# 1. Mesurer baseline
cd C:\Code\NEXUS\20_NEXUS
python BENCHMARKS/asi_proximity.py --nexus-id NEXUS_V6.5 --nexus-path NEXUS_V6_PROTOTYPE

# 2. Premier cycle évolution
cd NEXUS_V6_PROTOTYPE
python nexus6.py
nexus6> /evolve 1

# 3. Vérifier résultats
nexus6> /evolve-status

# 4. Review enfant
nexus6> /review
```

---

## 📊 Métriques de Succès V7

| Métrique | V6.5 | V7.0 Target | V7.2 Target |
|----------|------|-------------|-------------|
| ASI Score Global | 0.64 | 0.75 | 0.83 |
| Coding | 0.70 | 0.78 | 0.85 |
| Reasoning | 0.65 | 0.75 | 0.82 |
| Creativity | 0.60 | 0.70 | 0.80 |
| Scalability | 0.55 | 0.65 | 0.75 |
| Évolutions/mois | 0 | 10 | 20 |
| Taux promotion | N/A | 30% | 40% |
| Red Team Pass | N/A | 95% | 98% |

---

## 🔒 Contraintes de Sécurité

Tout au long de V7, les contraintes suivantes DOIVENT être respectées:

1. **KERNEL.py immutable** - Jamais modifié
2. **Rate limiting actif** - Max 3/jour
3. **Red Team obligatoire** - Chaque enfant testé
4. **Review humain** - Mutations architecturales
5. **Claude = Guardian** - Surveillance continue

---

## 📝 Notes pour le Créateur

**Yann**, voici mes recommandations:

1. **Commencer petit**: Un `/evolve 1` pour valider avant `/evolve 3`
2. **Mesurer d'abord**: Baseline ASI avant toute évolution
3. **Documenter tout**: Chaque évolution dans CORRECTIONS_LOG
4. **Patience**: ASI = itération, pas révolution
5. **Sécurité first**: Après CORR-015, vigilance accrue

**Questions à clarifier**:
- Budget API mensuel (Gemini + Claude)?
- Priorité: stabilité vs nouvelles features?
- GCP: budget autorisé pour fine-tuning?

---

**Document Status**: DRAFT
**Next Review**: Après premier `/evolve 1` réussi
**Maintainer**: Claude Code + Yann Abadie

---

*"L'ASI se construit une génération à la fois."*
