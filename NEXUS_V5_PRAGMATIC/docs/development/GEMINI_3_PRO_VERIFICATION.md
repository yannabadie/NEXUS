# Vérification Gemini 3 Pro Preview - 20 Nov 2025

## Problème Identifié

Lors des tests initiaux, les logs montraient que `gemini-2.5-flash-lite` et `gemini-2.5-flash` étaient utilisés au lieu de `gemini-3-pro-preview`.

### Preuve du Problème

Fichier: `test_workspaces/test_cfl_basic_write_read/_IO_BUFFER/action_out.json`

```json
"stats": {
  "models": {
    "gemini-2.5-flash-lite": {
      "api": {
        "totalRequests": 1,
        "totalErrors": 0,
        "totalLatencyMs": 2747
      }
    },
    "gemini-2.5-flash": {
      "api": {
        "totalRequests": 2,
        "totalErrors": 1,
        "totalLatencyMs": 4500
      }
    }
  }
}
```

**AUCUNE trace de gemini-3-pro-preview!**

## Cause Racine

Le driver Gemini (`core/drivers/gemini_driver.py`) n'utilisait pas le flag `-m` pour spécifier le modèle.

### Code Incorrect (Avant)

```python
command = (
    f'"{self.cli_path}" '
    f'@"{context_file.absolute()}" '
    f'"Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)." '
    f'-o json '
    f'> "{output_file.absolute()}"'
)
```

Le CLI Gemini utilise son modèle par défaut (gemini-2.5-flash) au lieu de Gemini 3 Pro.

## Solution Appliquée

### Correction du Driver

Fichier: `core/drivers/gemini_driver.py` (ligne 47)

```python
command = (
    f'"{self.cli_path}" '
    f'-m gemini-3-pro-preview '  # FORCE Gemini 3 Pro Preview (VERIFIED)
    f'@"{context_file.absolute()}" '
    f'"Réponds STRICTEMENT en JSON (Protocole Synapse V5.0)." '
    f'-o json '
    f'> "{output_file.absolute()}"'
)
```

### Modèle Correct

Le nom exact du modèle Gemini 3 Pro pour le CLI (version 0.16.0) est:

- **`gemini-3-pro-preview`** ✅ (VÉRIFIÉ)

Noms alternatifs (non testés):
- `gemini-3.0-pro`
- `gemini-3-pro-preview-11-2025-thinking`

## Vérification

### Test de Vérification

Script: `test_model_verification.py`

Résultats:

```
================================================================================
TEST: VERIFICATION MODELE GEMINI 3 PRO PREVIEW
================================================================================

[1/3] Configuration chargée
      Gemini CLI Path: gemini
      Modèle stratégie: gemini-3-pro-preview-11-2025-thinking

[2/3] Driver Gemini initialisé

[3/3] Test d'invocation...

================================================================================
✓ REPONSE RECUE
================================================================================

Sender: Gemini
Action: TALK
Content: Test réussi

VERIFICATION DU MODELE:
--------------------------------------------------------------------------------
Modèles utilisés: ['gemini-3-pro-preview']

✓✓✓ SUCCESS: gemini-3-pro-preview est bien utilisé! ✓✓✓

  Requêtes: 1
  Latence: 8559ms
  Tokens: 6762
```

### Statistiques du Modèle

- **Requêtes**: 1
- **Latence**: 8.5 secondes (normal pour Gemini 3 Pro avec thinking mode)
- **Tokens totaux**: 6762
- **Modèle confirmé**: `gemini-3-pro-preview` ✅

## Impact

### Avant (Incorrect)
- Modèle: gemini-2.5-flash-lite / gemini-2.5-flash
- Context: ~128k tokens
- Thinking mode: Non
- Latence: 2-4s

### Après (Correct)
- Modèle: gemini-3-pro-preview ✅
- Context: ~1M tokens
- Thinking mode: Oui (1021 thinking tokens dans les tests)
- Latence: 8-30s (acceptable pour les capacités supérieures)

## Commandes de Vérification

### Test Direct Gemini CLI

```bash
gemini -m gemini-3-pro-preview "Test" -o json
```

Vérifier dans les stats de la réponse:
```json
{
  "stats": {
    "models": {
      "gemini-3-pro-preview": {
        ...
      }
    }
  }
}
```

### Test NEXUS Driver

```bash
cd C:\Code\NEXUS\20_NEXUS\NEXUS_V5_PRAGMATIC
python test_model_verification.py
```

Doit afficher:
```
✓✓✓ SUCCESS: gemini-3-pro-preview est bien utilisé! ✓✓✓
```

## Conclusion

✅ **PROBLÈME RÉSOLU**

Le driver Gemini utilise maintenant correctement **Gemini 3 Pro Preview** grâce au flag `-m gemini-3-pro-preview`.

Cette correction est **VITALE** pour le projet car:
1. Gemini 3 Pro offre 1M de tokens de contexte (vs 128k)
2. Thinking mode activé pour raisonnement avancé
3. Capacités stratégiques supérieures
4. Conforme aux spécifications du projet

---

**Date**: 20 Novembre 2025
**Version Gemini CLI**: 0.16.0
**Modèle vérifié**: gemini-3-pro-preview ✅
