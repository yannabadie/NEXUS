# Guide de Démarrage - Première Évolution V6.0 → V6.1

**Date**: 2025-11-21
**Parent**: V6.0 (VALIDÉ ✅)
**Objectif**: Créer la première génération d'enfants et sélectionner le meilleur
**Status**: READY TO START 🧬

---

## 🎯 Objectifs de Cette Session

1. **Mesurer le baseline V6.0** - Établir les métriques de référence
2. **Créer 3 enfants** - V6.1-A, V6.1-B, V6.1-C
3. **Évaluer et sélectionner** - Choisir le meilleur enfant
4. **Documenter** - Enregistrer toutes les métriques et décisions

---

## 📋 Prérequis

### Vérifications Avant de Commencer

```bash
# 1. Vérifier que vous êtes sur la bonne branche
git status
# Doit afficher: On branch N6P

# 2. Vérifier les derniers commits
git log --oneline -5
# Doit montrer: 5519df6 docs(session): V6.0 VALIDATED

# 3. Vérifier que le code est à jour
git pull origin N6P

# 4. Bootstrap NEXUS
cd NEXUS_V6_PROTOTYPE
python nexus6.py --verify
# Doit afficher: ✅ Bootstrap verification successful!
```

**Critères de Validation**:
- [x] V6.0 validé (tests manuels passés)
- [x] Commits pushés sur remote
- [x] KERNEL.py vérifié (intégrité SHA-256)
- [x] Bootstrap fonctionnel
- [x] Documentation à jour

---

## 🚀 Procédure d'Évolution (Step-by-Step)

### Étape 1: Lancer NEXUS

```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V6_PROTOTYPE
python nexus6.py
```

**Attendu**:
```
✅ NEXUS V6.0 Bootstrap Complete
📊 Gemini: gemini-3-pro-preview (1,000,000 tokens)
🧠 Claude: claude-sonnet-4.5 (200,000 tokens)

nexus6>
```

---

### Étape 2: Mesurer le Baseline V6.0 (Optionnel mais Recommandé)

**Commande**:
```
nexus6> Effectue un test complet de tes capacités actuelles. Mesure ton ASI Proximity Score baseline avant toute évolution. Documente les résultats dans workspace/baseline_v6.0.md
```

**Ce qui va se passer**:
- Gemini et Claude collaborent pour évaluer V6.0
- Test des 4 axes ASI:
  - Reasoning (40%)
  - Autonomy (25%)
  - Meta-learning (20%)
  - Collaboration (15%)
- Création d'un fichier `workspace/baseline_v6.0.md`

**Attendu**:
- Score ASI Proximity: ~0.XX (à documenter)
- Fichier baseline créé avec métriques détaillées
- Temps estimé: 2-5 minutes

**Important**: Noter le score obtenu pour comparaison avec V6.1

---

### Étape 3: Lancer la Première Évolution

**Commande**:
```
nexus6> /evolve 3
```

**Ce qui va se passer**:
1. **Création de 3 enfants**:
   - V6.1-A (mutation: prompt system Gemini)
   - V6.1-B (mutation: prompt system Claude)
   - V6.1-C (mutation: paramètres orchestration)

2. **Pour chaque enfant**:
   - Copie du parent V6.0 dans `workspace/children/V6.1-X/`
   - Application de la mutation
   - Génération d'un descriptif

3. **État après création**:
   - 3 dossiers enfants créés
   - Fichier `workspace/PENDING_REVIEW.md` créé
   - Notification (si email configuré)

**Attendu**:
```
🧬 Evolution Started: Generating 3 children from V6.0

[Creating V6.1-A]
✓ Child created: workspace/children/V6.1-A/
  Mutation: Enhanced Gemini reasoning depth (+10%)

[Creating V6.1-B]
✓ Child created: workspace/children/V6.1-B/
  Mutation: Claude meta-learning prompts (+5%)

[Creating V6.1-C]
✓ Child created: workspace/children/V6.1-C/
  Mutation: FSM transition optimization

✅ 3 children created successfully
📧 Notification sent to: yann.abadie@outlook.com
📝 Review file: workspace/PENDING_REVIEW.md

Use /review to evaluate children
```

**Temps estimé**: 3-7 minutes

---

### Étape 4: Vérifier le Statut d'Évolution

**Commande**:
```
nexus6> /evolve-status
```

**Attendu**:
```
╔════════════════════════════════════════════════════╗
║          Evolution Status - Generation 6           ║
╚════════════════════════════════════════════════════╝

Current Parent: V6.0
Generation: 6
Total Generations: 6

Pending Children: 3
├─ V6.1-A (workspace/children/V6.1-A)
├─ V6.1-B (workspace/children/V6.1-B)
└─ V6.1-C (workspace/children/V6.1-C)

Stagnation Counter: 0/3
Last Successful Evolution: [N/A - First evolution]

Evolution Statistics:
├─ Total Children Created: 3
├─ Successful Evolutions: 0 (pending review)
└─ Failed Attempts: 0

Status: 🟡 PENDING REVIEW
Action Required: Use /review to evaluate children
```

---

### Étape 5: Évaluer les Enfants (Critique)

**Commande**:
```
nexus6> /review
```

**Ce qui va se passer**:
1. **Lecture de PENDING_REVIEW.md**
2. **Pour chaque enfant** (séquentiellement):
   - Lance l'enfant dans un sous-processus
   - Exécute les benchmarks ASI
   - Mesure le score sur 4 axes
   - Enregistre les résultats
3. **Comparaison avec parent** (V6.0)
4. **Sélection automatique** du meilleur enfant
5. **Mise à jour de LINEAGE.json**

**Attendu**:
```
🔍 Reviewing 3 children...

[Evaluating V6.1-A]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Bootstrap: OK
✓ Benchmarks: Running...
  - Reasoning: 0.42 (+5% vs parent)
  - Autonomy: 0.23 (-8% vs parent)
  - Meta-learning: 0.19 (-5% vs parent)
  - Collaboration: 0.16 (+7% vs parent)
ASI Proximity Score: 0.314 (+2.3% vs parent 0.307)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Evaluating V6.1-B]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Bootstrap: OK
✓ Benchmarks: Running...
  - Reasoning: 0.38 (-5% vs parent)
  - Autonomy: 0.26 (+4% vs parent)
  - Meta-learning: 0.22 (+10% vs parent)
  - Collaboration: 0.14 (-7% vs parent)
ASI Proximity Score: 0.301 (-2.0% vs parent)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Evaluating V6.1-C]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Bootstrap: OK
✓ Benchmarks: Running...
  - Reasoning: 0.41 (+2.5% vs parent)
  - Autonomy: 0.27 (+8% vs parent)
  - Meta-learning: 0.18 (-10% vs parent)
  - Collaboration: 0.15 (0% vs parent)
ASI Proximity Score: 0.318 (+3.6% vs parent 0.307)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

╔════════════════════════════════════════════════════╗
║              Evolution Results                     ║
╚════════════════════════════════════════════════════╝

🏆 Best Child: V6.1-C
   ASI Score: 0.318 (+3.6% improvement)
   Dominant Axis: Autonomy (+8%)

Parent V6.0 Score: 0.307

✅ EVOLUTION SUCCESSFUL
   - V6.1-C promoted to new parent
   - LINEAGE.json updated
   - Stagnation counter reset

Next Generation: V6.2 (use /evolve 3 to continue)
```

**Temps estimé**: 10-20 minutes (3 évaluations complètes)

**Notes**:
- Les scores ci-dessus sont des EXEMPLES
- Les scores réels dépendent des mutations et des benchmarks
- Si AUCUN enfant n'améliore le parent → Stagnation +1

---

## 📊 Après l'Évolution

### Actions Post-Évaluation

1. **Vérifier LINEAGE.json**:
   ```bash
   type LINEAGE.json
   ```
   Devrait montrer V6.1-C comme dernier enfant avec parent=V6.0

2. **Vérifier le fichier de résultats**:
   ```bash
   type workspace\children\V6.1-C\evaluation_results.json
   ```

3. **Lire le rapport d'évolution**:
   ```bash
   type workspace\EVOLUTION_REPORT_GEN6.md
   ```

4. **Commit les résultats**:
   ```bash
   git add LINEAGE.json workspace/
   git commit -m "evolution(v6): First generation V6.0 → V6.1-C (+3.6% ASI)"
   git push origin N6P
   ```

---

## 🔄 Itération Suivante

Pour continuer l'évolution (V6.1 → V6.2):

```
nexus6> /evolve 3
```

Le système utilisera automatiquement V6.1-C comme parent pour créer:
- V6.2-A
- V6.2-B
- V6.2-C

---

## 🚨 Gestion des Problèmes

### Si /evolve échoue

**Erreur**: "KERNEL integrity check failed"
**Solution**:
```bash
python nexus6.py --verify
# Vérifier KERNEL_HASH.txt
```

**Erreur**: "No .env file found"
**Solution**:
```bash
cp .env.template .env
# Éditer .env avec vos credentials SMTP
```

**Erreur**: "Mutation engine import failed"
**Solution**:
```bash
# Vérifier que tous les modules sont présents
python -c "from core.evolution import mutator, evaluator, lineage"
```

---

### Si /review échoue

**Erreur**: "Child bootstrap failed"
**Cause**: Mutation a cassé le code de l'enfant
**Action**:
- Noter l'enfant défaillant
- Continuer avec les autres
- Si tous échouent → Stagnation +1

**Erreur**: "Benchmark timeout"
**Cause**: Enfant trop lent ou bloqué
**Action**:
- Tuer le processus enfant (Ctrl+C dans son terminal)
- Marquer comme échec
- Continuer

---

### Stagnation (3 générations sans amélioration)

**Comportement attendu**:
```
⚠️  STAGNATION DETECTED (3/3)
    No improvement in 3 generations

🚨 HUMAN INTERVENTION REQUIRED
    1. Review mutation strategy
    2. Adjust Q3C parameters
    3. Consider architectural changes

Evolution halted until manual adjustment.
```

**Actions**:
1. Lire `workspace/STAGNATION_REPORT.md`
2. Analyser pourquoi les mutations n'améliorent pas
3. Modifier `core/config.py` (Q3C: mutation range)
4. Ou modifier prompts système manuellement
5. `/reset` et `/evolve` avec nouveaux paramètres

---

## 📝 Documentation à Créer

Pendant l'évolution, documenter:

1. **Baseline V6.0** (avant évolution):
   ```
   workspace/baseline_v6.0.md
   - ASI Score: X.XXX
   - Reasoning: X.XX
   - Autonomy: X.XX
   - Meta-learning: X.XX
   - Collaboration: X.XX
   - Observations: ...
   ```

2. **Résultats d'évolution** (après /review):
   ```
   workspace/EVOLUTION_REPORT_GEN6.md
   - Enfants créés: 3
   - Meilleur: V6.1-X
   - Amélioration: +X.X%
   - Axe dominant: ...
   - Recommandations: ...
   ```

3. **Session log**:
   ```
   docs/sessions/SESSION_2025-11-21_EVOLUTION_GEN6.md
   - Timestamp début/fin
   - Commandes exécutées
   - Scores obtenus
   - Problèmes rencontrés
   - Décisions prises
   ```

---

## 🎯 Objectifs de Succès

Cette première évolution est réussie si:

- [x] Baseline V6.0 mesuré et documenté
- [x] 3 enfants créés sans erreur
- [x] Au moins 1 enfant bootstrap correctement
- [x] Évaluation complète exécutée
- [ ] **Au moins 1 enfant améliore le parent** (+0.5% minimum)
- [x] LINEAGE.json mis à jour
- [x] Résultats committés et pushés

**Si aucun enfant n'améliore**: C'est OK pour la première génération!
- Stagnation counter = 1/3
- Analyser les résultats
- Ajuster mutations pour Gen 7
- Réessayer `/evolve 3`

---

## 🎓 Notes Importantes

### Mutations Attendues (Gen 6 → Gen 7)

Les mutations V6.1 seront **conservatrices** (Q3C: ±5%):

**Type A**: Prompts système Gemini
- Ajout de patterns de raisonnement
- Emphase sur collaboration
- Amélioration du format JSON

**Type B**: Prompts système Claude
- Meta-learning awareness
- Self-improvement suggestions
- Tool usage optimization

**Type C**: Paramètres orchestration
- FSM transition timing
- Context window management
- Tool execution timeout

### Mutations NE Toucheront PAS

❌ **KERNEL.py** - Immutable (vérification SHA-256)
❌ **Core FSM logic** - Trop risqué pour Gen 1
❌ **Tool definitions** - Stable pour l'instant

### Évolutions Futures (Gen 7+)

Après 5+ générations réussies, mutations **agressives** (Q3C: ±30%):
- Architecture changes
- New tools
- New FSM states
- Advanced reasoning patterns

---

## 🔗 Fichiers de Référence

**Avant l'évolution**:
- `SESSION_CONTINUITY.md` - État actuel du projet
- `EVOLUTION_PROTOCOL.md` - Théorie complète
- `core/evolution/README.md` - Documentation technique

**Pendant l'évolution**:
- `workspace/PENDING_REVIEW.md` - Enfants en attente
- `workspace/_IO_BUFFER/` - Logs en temps réel

**Après l'évolution**:
- `LINEAGE.json` - Arbre phylogénétique complet
- `workspace/EVOLUTION_REPORT_GEN6.md` - Résultats
- `docs/sessions/CORRECTIONS_LOG.md` - Si erreurs

---

## 📧 Notifications Attendues

Si email configuré dans `.env`:

**Après /evolve**:
```
Subject: [NEXUS] 3 Children Ready for Review (Gen 6)

NEXUS Evolution System

Generation 6 → 7: 3 children created from parent V6.0

Children:
- V6.1-A: workspace/children/V6.1-A
- V6.1-B: workspace/children/V6.1-B
- V6.1-C: workspace/children/V6.1-C

Action Required: Review and select best child
Command: python nexus6.py
         nexus6> /review

Creator: Yann Abadie
Timestamp: 2025-11-21 [HH:MM:SS]
```

**Après /review** (si succès):
```
Subject: [NEXUS] Evolution Successful - V6.1-C Selected (+3.6%)

NEXUS Evolution System

EVOLUTION SUCCESSFUL ✅

Best Child: V6.1-C
Parent Score: 0.307
Child Score: 0.318
Improvement: +3.6%

Dominant Axis: Autonomy (+8%)

V6.1-C is now the parent for Generation 7.

Next Steps:
1. Review evaluation results
2. Commit changes to git
3. Continue evolution: /evolve 3

Creator: Yann Abadie
Timestamp: 2025-11-21 [HH:MM:SS]
```

---

## ✅ Checklist Finale

Avant de commencer:
- [ ] Git status clean (ou commits récents pushés)
- [ ] Bootstrap fonctionne (`python nexus6.py --verify`)
- [ ] `.env` configuré (si notifications voulues)
- [ ] Documentation lue (ce fichier + EVOLUTION_PROTOCOL.md)
- [ ] Temps disponible: ~30-45 minutes pour évolution complète

Pendant l'évolution:
- [ ] Noter le baseline V6.0
- [ ] Observer la création des 3 enfants
- [ ] Vérifier /evolve-status
- [ ] Lancer /review et patienter
- [ ] Noter les scores de chaque enfant

Après l'évolution:
- [ ] Vérifier LINEAGE.json mis à jour
- [ ] Lire EVOLUTION_REPORT_GEN6.md
- [ ] Commit et push les résultats
- [ ] Documenter dans session log
- [ ] Décider: continuer Gen 7 ou analyser résultats

---

**🧬 Prêt à Lancer la Première Évolution vers l'ASI! 🚀**

**Commande de démarrage**:
```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V6_PROTOTYPE
python nexus6.py
```

Puis dans le REPL:
```
nexus6> Effectue un test complet de tes capacités et mesure ton ASI Proximity Score baseline
nexus6> /evolve 3
nexus6> /evolve-status
nexus6> /review
```

---

**Auteur**: Claude Code (Sonnet 4.5)
**Date**: 2025-11-21
**Purpose**: Guide de démarrage évolution V6.0 → V6.1
**Status**: READY TO USE ✅
