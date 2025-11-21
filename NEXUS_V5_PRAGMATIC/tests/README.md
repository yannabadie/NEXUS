# NEXUS V5.1 - Tests

## Tests Automatisés

### Test Suite Complète (Unit Tests)
```bash
python tests/test_protocol_complete.py
```
- 82 tests unitaires
- Vérifie architecture, imports, protocoles
- Pas besoin de CLIs Gemini/Claude
- **Pass rate: 96.3%**

### Tests End-to-End (E2E) ⭐ NOUVEAU
```bash
# Depuis la racine du projet:
run_e2e_tests.bat

# Ou directement:
python tests/test_automated_e2e.py
```

**Pré-requis:**
- Gemini CLI installé et configuré
- Claude Code CLI installé et configuré

**Tests E2E:**
1. ✅ Conversation simple (greeting)
2. ✅ Question sur capacités NEXUS
3. ✅ Greeting + tâche technique
4. ✅ Tâche technique complète (création fichier)

**Critères de succès:**
- ✅ Conversations → réponse directe, pas d'orchestration
- ✅ Tâches → orchestration déclenchée
- ✅ Pas d'erreur "Expecting value: line 1 column 1"
- ✅ Pas d'erreur "État corrompu"
- ✅ Pas d'erreur Pydantic enum
- ✅ Fichier créé avec bon contenu

## Autres Tests

### Vérification Modèle
- `test_model_verification.py` - Vérifie quel modèle Gemini est utilisé

### Test Suite Legacy
- `test_suite.py` - Ancienne suite de tests

### Analyseur de Logs
- `log_analyzer.py` - Analyse les logs de session NEXUS

## Rapports de Tests

Les rapports JSON sont sauvegardés dans:
- `TEST_REPORT_YYYYMMDD_HHMMSS.json` - Résultats détaillés
