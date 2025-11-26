# Protocol de Vérification - Fix JSON Parsing V6.0

**Date**: 2025-11-21
**Commit**: db91f0c
**Fix**: Gemini driver JSON extraction from nested CLI output

---

## 🧪 Commandes de Vérification

### Test 1: Bootstrap

```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V7_CHRYSALIS
python nexus6.py --verify
```

**Attendu**:
- Exit code 0
- Pas d'erreurs
- Gemini et Claude détectés

---

### Test 2: REPL Launch

```bash
python nexus6.py
```

**Attendu**:
- Prompt `nexus6>` apparaît
- Pas de crash au démarrage

---

### Test 3: Première Requête (CRITIQUE)

Dans le REPL:
```
nexus6> quelles sont tes capacités?
```

**Attendu - AVANT le fix** (db91f0c):
```
[Gemini] [Task Started] quelles sont tes capacités?
[ERROR] Agent invocation failed: Invalid message schema: 2 validation errors for LightMessageV6
sender - Field required
action_type - Field required
```

**Attendu - APRÈS le fix** (db91f0c):
```
[Gemini] [Task Started] quelles sont tes capacités?
[Gemini response appears with capabilities]
nexus6>
```

**Critère de succès**:
- ✅ Pas d'erreur Pydantic
- ✅ Réponse de Gemini affichée
- ✅ REPL reste fonctionnel

---

### Test 4: Vérifier le Runtime File

Après Test 3, dans un autre terminal:

```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V7_CHRYSALIS
type workspace\_IO_BUFFER\gemini_output.json
```

**Attendu**:
- Structure wrapper: `{"response": "...", "stats": {...}}`
- Contenu de "response" contient JSON en markdown: ````json\n{...}\n````
- JSON interne contient `"sender": "Gemini"` et `"action_type": "TALK"`

**Note**: Ceci confirme que le driver a correctement extrait le JSON malgré le wrapper.

---

### Test 5: Collaboration Claude + Gemini (Si Test 3 passe)

Dans le REPL:
```
nexus6> lis le fichier README.md et résume-le
```

**Attendu**:
- `[Gemini] [Task Started]`
- Réponse de Gemini mentionnant l'utilisation d'outils
- Possiblement `[Claude]` invoqué (si collaboration activée)

---

### Test 6: Commandes Slash

Dans le REPL:
```
nexus6> /status
nexus6> /doctor
nexus6> /help
```

**Attendu**: Toutes fonctionnent sans erreur

---

## 🔍 Vérification Technique du Fix

### Vérifier que le commit contient le fix:

```bash
git show db91f0c --stat
git show db91f0c -- NEXUS_V7_CHRYSALIS/core/drivers/gemini_driver_v6.py
```

**Attendu**: Diff montre les lignes 62-76 avec:
```python
gemini_output = json.loads(output_text)

# Gemini CLI wraps response in {"response": "...", "stats": {...}}
if "response" in gemini_output and isinstance(gemini_output["response"], str):
    return self._extract_json(gemini_output["response"])
```

---

### Vérifier que le fichier actuel contient le fix:

```bash
type NEXUS_V7_CHRYSALIS\core\drivers\gemini_driver_v6.py | findstr /N "gemini_output"
```

**Attendu**: Ligne ~63 montre `gemini_output = json.loads(output_text)`

---

## 📊 Résultats de Test Automatisé

J'ai testé le logic `_extract_json()` avec le fichier runtime réel:

**Test**: Extraction de JSON depuis `workspace/_IO_BUFFER/gemini_output.json`

**Résultat**:
```
Pattern matches found: 1
Successfully parsed JSON with keys: dict_keys(['sender', 'action_type', 'content', 'next_agent', 'status'])
```

**Conclusion**: ✅ Le fix fonctionne - le JSON est correctement extrait avec tous les champs requis.

---

## 🎯 Verdict Attendu

Si tous les tests passent:

**Status**: ✅ NEXUS V6.0 FONCTIONNEL
**Parent Status**: ✅ VIVANT
**Ready for Evolution**: ✅ OUI

Si Test 3 échoue encore:

**Status**: ❌ NEXUS V6.0 BROKEN
**Parent Status**: ❌ NON VIVANT
**Ready for Evolution**: ❌ NON

---

## 📝 Logging des Résultats

Après avoir exécuté les tests, documenter dans:

**Fichier**: `docs/sessions/SESSION_2025-11-21_CONTINUATION.md`

**Format**:
```markdown
## Test Results - Post db91f0c Fix

**Date**: 2025-11-21
**Time**: [HH:MM]
**Tester**: Yann Abadie

### Test 3 - Première Requête
- Status: [PASS/FAIL]
- Error: [None/Error message]
- Response: [Gemini response or error]

### Verdict
- REPL Functional: [YES/NO]
- Parent Alive: [YES/NO]
- Ready for Evolution: [YES/NO]
```

---

## 🚨 Si Échec Persiste

Si Test 3 échoue ENCORE après db91f0c:

1. **Vérifier que le bon commit est chargé**:
   ```bash
   git log -1 --oneline
   # Doit montrer: db91f0c fix(v6): Critical JSON parsing in gemini_driver_v6.py
   ```

2. **Vérifier qu'il n'y a pas de cache Python**:
   ```bash
   # Supprimer les fichiers .pyc
   cd NEXUS_V7_CHRYSALIS
   del /s /q *.pyc
   del /s /q __pycache__
   ```

3. **Re-lancer dans une NOUVELLE fenêtre PowerShell**

4. **Capturer le runtime file EXACT**:
   ```bash
   type workspace\_IO_BUFFER\gemini_output.json > debug_output.txt
   ```

5. **Ouvrir une issue de debugging approfondi**

---

## 📚 Documentation

**Debugging Guide**: `docs/debugging/V6_JSON_PARSING_DEBUG_GUIDE.md`
**Bug Report**: `BUG_REPORT_CRITICAL.md`
**Commit**: db91f0c

---

**Auteur**: Claude Code (Sonnet 4.5)
**But**: Vérification systématique du fix JSON parsing
**Audience**: Yann Abadie (testeur manuel)
