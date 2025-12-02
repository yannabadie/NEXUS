# DOCADI-MAS: Rebranding PDF Tool

## Contexte

Ce projet automatise le rebranding des documents PDF du groupe **AD Industries** vers **Motherson Aerospace (MAS)**.

## Objectifs

1. **Changer le logo** AD Industries → Logo MOTHERSON
2. **Modifier le pied de page** avec la nouvelle entité légale
3. **Remplacer les acronymes** ADI et variantes → MAS

## Structure du projet

```
DOCADI-MAS/
├── Source/                          # PDFs originaux
│   ├── PR4_MAB.pdf                  # Fiche processus Mecalim
│   ├── PR4-HY_Rev_02_*.pdf          # Fiche processus Hydraulics
│   └── PR4-MCO_Rev_03_*.pdf         # Fiche processus Chavignon
├── Output/                          # PDFs transformés (généré)
├── Assets/                          # Logo Motherson (à fournir)
├── rebrand_adi_to_mas.py            # Script de transformation
├── rebrand_log.json                 # Rapport d'exécution (généré)
├── logique.txt                      # Spécifications originales
└── README.md                        # Ce fichier
```

## Prérequis

- Python 3.8+
- PyMuPDF (fitz)

```bash
pip install PyMuPDF
```

## Utilisation

### 1. Mode Analyse (recommandé en premier)

Analyse les PDFs sans les modifier pour prévisualiser les changements:

```bash
python rebrand_adi_to_mas.py --analyze
```

ou

```bash
python rebrand_adi_to_mas.py --dry-run
```

### 2. Mode Transformation

Applique les modifications et génère les PDFs dans `Output/`:

```bash
python rebrand_adi_to_mas.py
```

## Table de remplacement

| Original | Nouveau |
|----------|---------|
| AD INDUSTRIES | MOTHERSON AEROSPACE |
| AD Industries | Motherson Aerospace |
| groupe ADI | groupe MAS |
| ADI group | MAS group |
| ADI-Hydraulics | MAS-Hydraulics |
| ADI Chavignon | MAS Chavignon |
| ADIMC | MASMC |
| ADI-H | MAS-H |
| sites AD | sites MAS |

## Gestion du logo

Le script est préparé pour le remplacement du logo. Pour l'activer:

1. Placer le logo Motherson dans `Assets/logo_motherson.png`
2. Décommenter la fonction de remplacement de logo dans le script

**Note**: Le remplacement de logo dans PDF est complexe car les logos sont souvent des images intégrées. Une solution robuste pourrait nécessiter:
- Utiliser les fichiers sources (Excel/Word) si disponibles
- Utiliser Adobe Acrobat Pro ou un outil similaire
- Recréer les templates avec le nouveau logo

## Rapport d'exécution

Après chaque exécution, un fichier `rebrand_log.json` est généré avec:
- Timestamp
- Nombre de fichiers traités
- Détail des remplacements par fichier
- Erreurs éventuelles

## Limitations connues

1. **Logo**: Le remplacement automatique du logo est limité - les images embarquées dans les PDFs sont difficiles à modifier proprement
2. **Mise en page**: Les remplacements de texte peuvent légèrement affecter la mise en page si la longueur du texte change significativement
3. **Polices**: Le script utilise une police par défaut - les polices originales peuvent ne pas être préservées

## Recommandations

Pour un résultat optimal:

1. **Si possible**: Obtenir les fichiers sources (Excel, Word) pour un rebranding propre
2. **Validation**: Toujours vérifier manuellement les PDFs générés
3. **Logo**: Considérer l'ajout manuel du logo après transformation automatique du texte

## Auteur

Généré par NEXUS V7 "Chrysalis" - Collaboration Claude + Gemini

Date: 2025-12-01
