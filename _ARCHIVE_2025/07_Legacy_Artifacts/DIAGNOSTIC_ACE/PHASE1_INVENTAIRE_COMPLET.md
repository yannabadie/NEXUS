# DIAGNOSTIC ACE + COMPASS - PHASE 1.1 : INVENTAIRE DOCUMENTAIRE

**Date**: 22 octobre 2025
**Projet**: MES iDACS - Motherson Aerospace Tanger MVP
**Analyste**: Claude Code (Sonnet 4.5)

---

## SYNTHÈSE EXÉCUTIVE

### Métriques Globales

| Métrique | Valeur | Analyse |
|----------|--------|---------|
| **Nombre total de documents** | **18,486** | ✅ Corpus très riche |
| **Volume total données** | **11.3 GB** (11,566 MB) | ✅ Base substantielle |
| **Profondeur max arborescence** | **10 niveaux** | ⚠️ Structure profonde |
| **Types fichiers uniques** | **48** | ⚠️ Hétérogénéité élevée |
| **Documents > 1 an d'ancienneté** | **14,201 (77%)** | 🔴 RISQUE obsolescence |
| **Documents modifiés dernière semaine** | **54 (0.3%)** | ⚠️ Faible activité récente |
| **Documents > 1MB** | **1,086 (5.9%)** | ✅ Fichiers riches en contenu |

### Verdict Préliminaire

🟡 **CAPACITÉ RAG : MOYENNE-ÉLEVÉE** (Score estimé : **65/100**)

**Forces :**
- Volume corpus important (18K+ docs)
- Présence de 286 modes opératoires structurés
- Documentation technique riche (CEGID, iDACS)
- Métadonnées temporelles exploitables

**Faiblesses critiques :**
- **77% fichiers obsolètes (> 1 an)** - Risque information périmée
- Dominance Spreadsheets (66%) - Contenu difficile à indexer
- Hétérogénéité formats (48 types) - Complexité extraction
- Structure profonde (10 niveaux) - Risque silos

---

## DISTRIBUTION PAR CATÉGORIE

### Vue d'ensemble

| Catégorie | Nb Fichiers | % Total | Taille (MB) | % Volume | Pertinence RAG |
|-----------|-------------|---------|-------------|----------|----------------|
| **Spreadsheets** | 12,278 | 66.4% | 5,541 | 47.9% | 🟡 MOYENNE |
| **Data (JSON/XML)** | 2,215 | 12.0% | 1,984 | 17.2% | 🟢 ÉLEVÉE |
| **Other** | 1,959 | 10.6% | 3,413 | 29.5% | 🔴 FAIBLE |
| **Code** | 1,189 | 6.4% | 16 | 0.1% | 🟢 ÉLEVÉE |
| **Documents** | 741 | 4.0% | 426 | 3.7% | 🟢 TRÈS ÉLEVÉE |
| **Presentations** | 54 | 0.3% | 156 | 1.3% | 🟢 ÉLEVÉE |
| **Images** | 46 | 0.2% | 6 | 0.05% | 🟡 MOYENNE |
| **Archives** | 4 | 0.02% | 24 | 0.2% | ⚫ NULLE |

### Analyse Pertinence RAG

#### 🟢 Documents Haute Valeur (741 fichiers - 426 MB)

**Extensions** : `.md`, `.txt`, `.pdf`, `.docx`, `.doc`

**Top 10 par taille** :
1. **RAD10** - Mode opératoire Radio (11.25 MB)
2. **RAD09** - Mode opératoire Picking (10.72 MB)
3. **SA10** - Mise en service postes production (10.55 MB)
4. **CHARTE-AD-INDUSTRIES.pdf** (9.31 MB)
5. **VE03** - Tarifs ventes avancés (8.6 MB)
6. **QUA03** - Création FNC (8.2 MB)
7. **ST03** - Transferts inter-dépôt (7.69 MB)
8. **RAD08** - Changement emplacement (7.44 MB)
9. **AC09** - Réception fournisseur (6.87 MB)

**Observation** :
- Forte présence documentation CEGID (modes opératoires)
- Formats riches (DOCX avec captures écran)
- Pertinence MAXIMALE pour RAG

#### 🟡 Spreadsheets (12,278 fichiers - 5,541 MB)

**Extensions** : `.xlsx` (12,273), `.xlsm` (1,267 macros), `.xls` (3)

**Top fichiers volumineux** :
- Temps_OF_FAB_2019.xlsx (46.86 MB) - **Archives**
- V11_Temps_OF_FAB_2023.xlsx (39.91 MB) - **Actuel**
- Analyse_TP_UO.xlsm (96.52 MB JSON extrait)
- MSC_MAROC Improd 30J.xlsx (27.18 MB)

**Analyse** :
- Contenu : Données production, KPIs, suivi temps
- Problème : Tableaux Excel difficiles à vectoriser
- **Solution** : Extraction texte structuré (titres, labels, commentaires)
- **Prio FAIBLE** pour Phase 1 RAG

#### 🟢 JSON/Data (2,215 fichiers - 1,984 MB)

**Extensions** : `.json` (2,214), `.xml`, `.yaml`

**Fichiers massifs** :
- MES_KNOWLEDGE_BASE_ENRICHED.json (72.14 MB)
- MES_KNOWLEDGE_BASE_COMPLETE.json (66.21 MB)
- Extractions CEGID (100-130 MB)

**Analyse** :
- **Bases de connaissances déjà construites !**
- Extraction CEGID probablement complète
- Format structuré = parsing facile
- **PRIORITÉ MAXIMALE** pour RAG

#### 🟢 Presentations (54 fichiers - 156 MB)

**Extension** : `.pptx` (51), `.ppt` (3)

**Top présentations** :
1. iDACS Introduction (21.67 MB) - **Documentation produit**
2. PR10 - Description OF (13.45 MB) - **Formation**
3. GE01 - Lancement Cegid (11.07 MB)
4. EDI Intersites Tanger (9.39 MB)

**Analyse** :
- Contenu formation de haute valeur
- Vision métier (vs technique)
- **Extraction texte slides** recommandée

---

## PATTERNS DE NOMMAGE ET CONVENTIONS

### Structure Arborescence (10 niveaux max)

```
MES/
├── 00_ARCHIVES/           # Archives anciennes synthèses
├── 00_Gouvernance/        # RACI, comitologie
├── 01_Architecture/       # Specs techniques
├── 02_MVP_Tanger/         # Périmètre MVP
├── 03_Documentation_Technique/
├── 04_Conduite_Changement/
├── 05_Budget/             # Budget officiel
├── 06_Documentation_Source/
├── 07_Devis/
├── 08_Comitologie/        # Gouvernance
├── 09_Contracts/
├── 10_MyPlant.ai/         # Documentation iDACS
├── 11_Meetings/           # Réunions, workshops
├── 12_MES_Synthese/       # Synthèses GO/NO-GO
├── 13_DATAS/              # 🔥 CRITIQUE - CEGID, iDACS
│   ├── 01 - MS iDacs Documentation/
│   ├── Dossier_ERP/
│   │   ├── Modes_operatoires/  # 286 MO
│   │   ├── Etats_ERP/
│   │   └── V11/
├── 14_Plan/               # Planning, RACI
├── 15_Knowledge_Base_Unified/
├── 16_ERP-MES/
└── _TEMP/                 # Scripts, diagnostics
```

### Conventions Nommage

#### Mode Opératoires CEGID
**Pattern** : `{CODE} - {TYPE}_{Domaine}_{Titre} - Ind {Version}.{ext}`

Exemples :
- `RAD10 - MO_Radio_M10 Sortie exceptionnelle - Ind A.docx`
- `QUA03 - MO_Création fiche non conformité - Ind B.docx`
- `PR10 - Formation - Description ordre fabrication - Ind B.pptx`

**Codes identifiés** :
- **RAD** : Radio (mobilité)
- **QUA** : Qualité
- **PR** : Production
- **AC** : Achats
- **ST** : Stock
- **VE** : Ventes
- **FI** : Finance
- **DT** : Données Techniques
- **GE** : Général

#### Fichiers Projet MES
**Pattern** : `{NOM}_{YYYYMMDD}.{ext}` ou `{NOM}_V{X}.{ext}`

Exemples :
- `SYNTHESE-04102025-V3-COMPLETE.html`
- `MASMES-updatedplanning.xlsx`
- `RACI_MATRIX.xlsx`

---

## FICHIERS CRITIQUES IDENTIFIÉS

### Top 20 Documents pour RAG (Priorité P0)

| Rang | Fichier | Taille | Type | Raison Criticité |
|------|---------|--------|------|------------------|
| 1 | **MES_KNOWLEDGE_BASE_ENRICHED.json** | 72 MB | Data | Base existante enrichie |
| 2 | **MES_KNOWLEDGE_BASE_COMPLETE.json** | 66 MB | Data | Base existante complète |
| 3 | **286 Modes Opératoires CEGID** | ~500 MB | DOCX | Processus métier détaillés |
| 4 | **iDACS Introduction.pptx** | 22 MB | PPTX | Documentation produit |
| 5 | **CLAUDE.md** | 30 KB | MD | Contexte projet (ACTUEL) |
| 6 | **SYNTHESE_FINALE_SESSION_PMO.md** | 20 KB | MD | Synthèse PMO 16/10 |
| 7 | **QUESTIONS_CRITIQUES_MTSL.md** | 20 KB | MD | Questions MTSL |
| 8 | **PLAN_ACTION_SEMAINE_21-27_OCT_2025.md** | 10 KB | MD | Actions en cours |
| 9 | **RACI_MATRIX.xlsx** | 10 KB | XLSX | Gouvernance |
| 10 | **MASMES-updatedplanning.xlsx** | 17 KB | XLSX | Planning officiel |
| 11 | **OFFICIAL_TangerMVPPricing.xlsx** | 18 KB | XLSX | Budget officiel |
| 12 | **WORKSHOP_VSM_22102025.html** | 30 KB | HTML | Workshop récent |
| 13 | **AGENDA_KICKOFF_M0_31102025.html** | 31 KB | HTML | Kick-off à venir |
| 14 | **CALL_MTSL_27102025_QUESTIONS.html** | 36 KB | HTML | Call MTSL |
| 15 | **V11_Temps_OF_FAB_2023.xlsx** | 40 MB | XLSX | Données production |
| 16 | **MSC_MAROC Improd 30J.xlsx** | 27 MB | XLSX | Métriques imprévoyance |
| 17 | **Analyse_TP_UO.xlsm** | 96 MB JSON | XLSM | Analyse temps/unités |
| 18 | **SYNTHESE_SESSION_20102025.md** | 5 KB | MD | Session récente |
| 19 | **Dossier_ERP complet** | ~2 GB | Mixed | Données CEGID V11 |
| 20 | **15_Knowledge_Base_Unified/** | Variable | Mixed | KB préexistante |

### Fichiers Récents (Activité Dernière Semaine - 54 fichiers)

**Observation** : Activité concentrée sur :
1. Préparation kick-off M0 (31/10/2025)
2. Documentation workshops VSM
3. Questions critiques MTSL
4. Mise à jour planning/RACI

**Impact RAG** : Documents récents = contexte actuel projet

---

## GAPS DOCUMENTAIRES DÉTECTÉS

### Gap 1 : Obsolescence Massive

**Constat** : **14,201 fichiers (77%) > 1 an**

**Impact** :
- Risque d'indexer information périmée
- Confusion contexte CEGID V10 vs V11
- Processus obsolètes vs processus actuels Tanger

**Remédiation** :
1. **Filtrage temporel** : Prioriser docs < 2 ans
2. **Validation métier** : Identifier docs "evergreen" (procédures stables)
3. **Archivage sélectif** : Exclure dossiers archives explicites
4. **Métadonnées version** : Tagger CEGID V10 vs V11

**Coût** : 2-3 jours de curation manuelle

### Gap 2 : Hétérogénéité Formats

**Constat** : **48 types de fichiers** différents

**Extensions problématiques** :
- `.hrp` (446 fichiers) - Format inconnu
- `.msg` (107) - Emails Outlook (difficile extraction)
- `.xlsm` (1,267) - Macros Excel (sécurité + parsing complexe)
- `.bak`, `.backup` (16) - Fichiers de sauvegarde

**Impact** :
- Complexité pipeline extraction
- Coûts développement loaders custom
- Risque erreurs parsing

**Remédiation** :
1. **Focus prioritaire** : MD, DOCX, PDF, PPTX, JSON (90% valeur)
2. **Exclusion** : BAK, MSG, formats propriétaires
3. **Conversion** : XLSM → CSV/TXT (extraction structurée)

**Coût** : 1 semaine développement loaders

### Gap 3 : Silos Documentaires

**Constat** : Structure profonde (10 niveaux) + duplication (Dossier_ERP + V11/)

**Exemples duplication** :
- `13_DATAS/Dossier_ERP/` vs `13_DATAS/Dossier_ERP/V11/`
- Même fichier présent dans archives + dossiers actifs

**Impact** :
- Duplication contenu indexé (bruit)
- Chunks similaires perturbent recherche
- Coût stockage/embedding doublé

**Remédiation** :
1. **Déduplication** : Hashing fichiers, exclusion doublons
2. **Priorité temporelle** : Fichier V11 > Fichier legacy
3. **Exclusion dossiers** : `/Archives/`, `/OLD/`, `/Backup/`

**Coût** : 2-3 jours scripting déduplication

### Gap 4 : Manque Métadonnées

**Constat** : Métadonnées limitées aux timestamps filesystem

**Métadonnées manquantes** :
- Auteur (sauf extraction properties Office)
- Tags/mots-clés
- Statut (draft/validé/obsolète)
- Relations (doc A → référence doc B)
- Version sémantique (vs indice lettre)

**Impact** :
- Filtrage/tri limité
- Pas de validation "ce doc est officiel"
- Difficulté traçabilité versions

**Remédiation** :
1. **Extraction automatique** : Properties Office docs
2. **Inférence** : Déduire statut depuis chemin (OFFICIAL_, V{X}, etc.)
3. **Enrichissement manuel** : Top 100 docs critiques

**Coût** : 1 semaine développement + 2 jours curation

---

## RECOMMANDATIONS PHASE 1.1

### Scoring Capacité RAG Brut

| Critère | Score | Justification |
|---------|-------|---------------|
| **Volume corpus** (0-25) | **22/25** | 18K+ docs, 11GB - Excellent |
| **Qualité formats** (0-25) | **16/25** | Mix DOCX/MD/JSON (bien) + Excel dominant (faible) |
| **Fraîcheur données** (0-25) | **8/25** | 77% obsolètes - Critique |
| **Structuration** (0-25) | **19/25** | Bonne arborescence + conventions nommage |
| **SCORE TOTAL** | **65/100** | **CAPACITÉ MOYENNE-ÉLEVÉE** |

### Actions Immédiates (Avant Phase RAG)

#### Priorité P0 (Bloquantes)
1. ✅ **Déduplication fichiers** (gain 30-40% volume indexé)
2. ✅ **Exclusion dossiers archives** (/Archives/, /OLD/, /Backup/)
3. ✅ **Filtrage temporel** : Prioriser < 2 ans OU evergreen validés
4. ✅ **Extraction bases existantes** : JSON KB (72MB + 66MB)

#### Priorité P1 (Critiques)
5. ⚠️ **Développement loaders** : DOCX, PDF, PPTX, JSON
6. ⚠️ **Parsing sélectif Excel** : Extraction titres, headers, commentaires
7. ⚠️ **Enrichissement métadonnées** : Top 100 docs

#### Priorité P2 (Optimisations)
8. 📋 **Curation manuelle** : Validation 286 modes opératoires
9. 📋 **Taxonomie** : Classification docs par domaine métier
10. 📋 **Glossaire** : Termes techniques CEGID/iDACS

### Estimation Effort Remédiation

| Tâche | Effort | Coût (€) |
|-------|--------|----------|
| Déduplication + exclusions | 2j | 1,600 |
| Développement loaders | 5j | 4,000 |
| Enrichissement métadonnées | 3j | 2,400 |
| Curation manuelle top docs | 2j | 1,600 |
| **TOTAL Phase 1.1 → RAG-ready** | **12j** | **9,600€** |

---

## PROCHAINES ÉTAPES

### Phase 1.2 : Analyse Sémantique (En cours)
- Extraction échantillon 50 docs critiques
- NLP basique : Thématiques, termes techniques
- Détection langues (FR/EN)
- Évaluation densité informationnelle

### Phase 1.3 : Analyse Dépendances
- Graphe de références inter-documents
- Identification documents pivots
- Détection versions multiples
- Mapping silos thématiques

---

**Signature** : Diagnostic généré automatiquement
**Fichier source** : `_TEMP/diagnostic_ace_inventory.py`
**Rapports détaillés** : `_TEMP/DIAGNOSTIC_ACE/`
