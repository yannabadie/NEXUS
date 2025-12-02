# Guide de Demarrage - Evolution NEXUS V7

**Date**: 2025-11-26
**Version**: V7.0 "Chrysalis"
**Objectif**: Creer des generations d'enfants et selectionner les meilleurs
**Status**: READY

---

## Objectifs

1. **Mesurer le baseline V7.0** - Etablir les metriques de reference
2. **Creer des enfants** - Mutations emergentes via brainstorming
3. **Evaluer et selectionner** - Choisir le meilleur enfant
4. **Documenter** - Enregistrer toutes les metriques

---

## Prerequis

### Verifications Avant de Commencer

```bash
# 1. Verifier la branche
git status
# Doit afficher: On branch N7C

# 2. Verifier les derniers commits
git log --oneline -5

# 3. Bootstrap NEXUS
cd NEXUS_V7_CHRYSALIS
python nexus7.py --verify
# Doit afficher: Bootstrap verification successful!
```

---

## Procedure d'Evolution

### Etape 1: Lancer NEXUS

```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V7_CHRYSALIS
python nexus7.py
```

**Attendu**:
```
NEXUS V7.0 Bootstrap Complete
Gemini: gemini-3-pro-preview
Claude: claude-sonnet-4-5

nexus7>
```

---

### Etape 2: Lancer l'Evolution

**Commande**:
```
nexus7> /evolve 3
```

**Ce qui va se passer**:
1. **Brainstorming emergent** - Gemini et Claude debattent des mutations
2. **Creation de 3 enfants** dans `GENERATION_ACTIVE/`
3. **Application des mutations** via JSON patches
4. **Generation des birth certificates**

**Attendu**:
```
EVOLUTION CYCLE STARTED
Trigger: Manual (/evolve command)
Children to create: 3

Creating Child 1/3: NEXUS_V7.1_CHILD_001
[MUTATOR] Cloning parent...
[MUTATOR] Applying mutation...
[MUTATOR] Birth certificate created

3 children created successfully
Use '/review' to evaluate children
```

---

### Etape 3: Verifier le Statut

**Commande**:
```
nexus7> /evolve-status
```

**Attendu**:
```
EVOLUTION STATUS

Current Parent: NEXUS_V7.0
Generation: 7
Stagnation Counter: 0/3

Pending Children: 3
- NEXUS_V7.1_CHILD_001
- NEXUS_V7.1_CHILD_002
- NEXUS_V7.1_CHILD_003

Status: PENDING REVIEW
```

---

### Etape 4: Evaluer les Enfants

**Commande**:
```
nexus7> /review
```

**Ce qui va se passer**:
1. **Lecture de PENDING_REVIEW.md**
2. **Benchmarks ASI** pour chaque enfant (4 axes)
3. **Comparaison** avec parent
4. **Selection automatique** du meilleur

**Attendu**:
```
Reviewing 3 children...

[Evaluating NEXUS_V7.1_CHILD_001]
- Coding: 0.32 (+3%)
- Reasoning: 0.31 (+2%)
- Creativity: 0.26 (+4%)
- Scalability: 0.16 (+1%)
ASI Proximity Score: 0.318 (+3.6% vs parent)

Best Child: NEXUS_V7.1_CHILD_001
EVOLUTION SUCCESSFUL
```

---

## ASI Metrics (4 Axes)

| Dimension | Weight | Description |
|-----------|--------|-------------|
| **Coding** | 30% | Code generation, refactoring, debugging |
| **Reasoning** | 30% | Logic puzzles, multi-step planning |
| **Creativity** | 25% | Novel solutions, architecture design |
| **Scalability** | 15% | Large-scale problem handling |

**Formula**: `ASI Score = 0.30*Coding + 0.30*Reasoning + 0.25*Creativity + 0.15*Scalability`

---

## SURVIVAL_LAW (Stagnation)

Si un parent ne produit **aucun enfant superieur apres 3 generations**:

```
STAGNATION DETECTED (3/3)
HUMAN INTERVENTION REQUIRED

Actions:
1. Review mutation strategy
2. Adjust parameters
3. Consider architectural changes
```

---

## Apres l'Evolution

### Commit les Resultats

```bash
git add LINEAGE.json GENERATION_ACTIVE/
git commit -m "evolution(v7): Generation X -> Y (+X.X% ASI)"
git push origin N7C
```

### Iteration Suivante

```
nexus7> /evolve 3
```

Le systeme utilisera automatiquement le meilleur enfant comme nouveau parent.

---

## Troubleshooting

### Si /evolve echoue

- Verifier KERNEL.py integrite
- Verifier `.env` configuration
- Verifier tous les modules: `python -c "from core.evolution import mutator, evaluator, lineage"`

### Si /review echoue

- Child bootstrap failed → Mutation a casse le code
- Benchmark timeout → Enfant trop lent

---

## Fichiers de Reference

- `LINEAGE.json` - Arbre phylogenetique
- `GENERATION_ACTIVE/` - Enfants en cours
- `BIRTH_CERTIFICATE_*.json` - Certificats de naissance
- `EVALUATION_RESULTS.json` - Resultats benchmarks

---

**Commande de demarrage**:
```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V7_CHRYSALIS
python nexus7.py
```

Puis:
```
nexus7> /evolve 3
nexus7> /evolve-status
nexus7> /review
```
