#!/usr/bin/env python3
"""
DOCADI-MAS: Script de rebranding PDF
AD Industries → Motherson Aerospace (MAS)

Ce script transforme les documents PDF du groupe AD Industries
pour le rebranding vers Motherson Aerospace.

Fonctionnalités:
- Remplacement de texte (acronymes ADI → MAS)
- Remplacement du logo (si fourni)
- Mise à jour des pieds de page
- Traitement par lot de tous les PDFs

Auteur: NEXUS V7 Chrysalis (Claude + Gemini collaboration)
Date: 2025-12-01
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime

# Configuration des chemins
SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR / "Source"
OUTPUT_DIR = SCRIPT_DIR / "Output"
ASSETS_DIR = SCRIPT_DIR / "Assets"
LOG_FILE = SCRIPT_DIR / "rebrand_log.json"

# Table de mapping texte: ADI → MAS
# Ordre important: patterns longs avant patterns courts pour éviter les remplacements partiels
TEXT_REPLACEMENTS: List[Tuple[str, str]] = [
    # Noms complets d'abord
    ("AD INDUSTRIES", "MOTHERSON AEROSPACE"),
    ("AD Industries", "Motherson Aerospace"),
    ("AD Industrie", "Motherson Aerospace"),
    ("AD INDUSTRIE", "MOTHERSON AEROSPACE"),

    # Sites spécifiques (patterns longs)
    ("ADI-Hydraulics", "MAS-Hydraulics"),
    ("ADI Hydraulics", "MAS Hydraulics"),
    ("ADI-HYDRAULICS", "MAS-HYDRAULICS"),
    ("ADI Chavignon", "MAS Chavignon"),
    ("ADI CHAVIGNON", "MAS CHAVIGNON"),

    # Acronymes composés
    ("ADIMC", "MASMC"),
    ("ADI MC", "MAS MC"),
    ("ADI-MC", "MAS-MC"),
    ("ADI-HY", "MAS-HY"),
    ("ADI-H", "MAS-H"),

    # Groupe et références
    ("groupe ADI", "groupe MAS"),
    ("Groupe ADI", "Groupe MAS"),
    ("GROUPE ADI", "GROUPE MAS"),
    ("ADI group", "MAS group"),
    ("ADI Group", "MAS Group"),
    ("ADI GROUP", "MAS GROUP"),

    # Sites génériques
    ("sites AD", "sites MAS"),
    ("Sites AD", "Sites MAS"),
    ("SITES AD", "SITES MAS"),
    ("site AD", "site MAS"),
    ("Site AD", "Site MAS"),

    # Définitions et références
    ("def ADI", "def MAS"),
    ("DEF ADI", "DEF MAS"),

    # Acronyme seul (en dernier pour éviter les faux positifs)
    # Note: "ADI" seul est risqué car peut apparaître dans d'autres contextes
    # On le garde mais avec prudence - à activer si nécessaire
    # ("ADI", "MAS"),
]

# Pieds de page légaux
FOOTER_REPLACEMENTS: List[Tuple[str, str]] = [
    (
        "Ce document est la propriété du groupe ADI",
        "Ce document est la propriété du groupe MAS"
    ),
    (
        "This document is the property of ADI group",
        "This document is the property of MAS group"
    ),
]


def check_dependencies() -> bool:
    """Vérifie que PyMuPDF (fitz) est installé."""
    try:
        import fitz
        print(f"✓ PyMuPDF version {fitz.version[0]} détecté")
        return True
    except ImportError:
        print("✗ PyMuPDF non installé.")
        print("  Installation: pip install PyMuPDF")
        return False


def setup_directories() -> None:
    """Crée les répertoires nécessaires."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)
    print(f"✓ Répertoires configurés")
    print(f"  - Source: {SOURCE_DIR}")
    print(f"  - Output: {OUTPUT_DIR}")
    print(f"  - Assets: {ASSETS_DIR}")


def get_pdf_files() -> List[Path]:
    """Liste tous les fichiers PDF dans le dossier Source."""
    if not SOURCE_DIR.exists():
        print(f"✗ Dossier Source non trouvé: {SOURCE_DIR}")
        return []

    pdfs = list(SOURCE_DIR.glob("*.pdf"))
    print(f"✓ {len(pdfs)} fichiers PDF trouvés")
    for pdf in pdfs:
        print(f"  - {pdf.name}")
    return pdfs


def replace_text_in_pdf(input_path: Path, output_path: Path) -> Dict:
    """
    Remplace le texte dans un PDF selon la table de mapping.

    Retourne un dictionnaire avec les statistiques de remplacement.
    """
    import fitz

    stats = {
        "file": input_path.name,
        "pages": 0,
        "replacements": {},
        "errors": [],
        "success": False
    }

    try:
        # Ouvrir le PDF
        doc = fitz.open(input_path)
        stats["pages"] = len(doc)

        # Combiner toutes les règles de remplacement
        all_replacements = TEXT_REPLACEMENTS + FOOTER_REPLACEMENTS

        # Pour chaque page
        for page_num, page in enumerate(doc):
            page_text = page.get_text()

            # Pour chaque règle de remplacement
            for old_text, new_text in all_replacements:
                if old_text in page_text:
                    # Compter les occurrences
                    count = page_text.count(old_text)

                    # Chercher et remplacer
                    text_instances = page.search_for(old_text)

                    for inst in text_instances:
                        # Redact (masquer) l'ancien texte
                        page.add_redact_annot(inst, fill=(1, 1, 1))  # Fond blanc

                    # Appliquer les redactions
                    page.apply_redactions()

                    # Réinsérer le nouveau texte
                    for inst in text_instances:
                        # Insérer le nouveau texte à la même position
                        # Note: La taille de police est estimée
                        page.insert_text(
                            inst[:2],  # Point d'insertion (coin supérieur gauche)
                            new_text,
                            fontsize=8,  # Ajuster selon le document
                            color=(0, 0, 0)  # Noir
                        )

                    # Statistiques
                    key = f"{old_text} → {new_text}"
                    if key not in stats["replacements"]:
                        stats["replacements"][key] = 0
                    stats["replacements"][key] += count

        # Sauvegarder le PDF modifié
        doc.save(output_path)
        doc.close()

        stats["success"] = True
        total_replacements = sum(stats["replacements"].values())
        print(f"✓ {input_path.name}: {total_replacements} remplacements effectués")

    except Exception as e:
        stats["errors"].append(str(e))
        print(f"✗ Erreur sur {input_path.name}: {e}")

    return stats


def replace_text_simple(input_path: Path, output_path: Path) -> Dict:
    """
    Méthode alternative: extraction et reconstruction du PDF.
    Plus fiable pour les textes complexes.
    """
    import fitz

    stats = {
        "file": input_path.name,
        "pages": 0,
        "replacements": {},
        "errors": [],
        "success": False,
        "method": "text_extraction"
    }

    try:
        doc = fitz.open(input_path)
        stats["pages"] = len(doc)

        all_replacements = TEXT_REPLACEMENTS + FOOTER_REPLACEMENTS

        for page_num, page in enumerate(doc):
            # Extraire les blocs de texte
            blocks = page.get_text("dict")["blocks"]

            for block in blocks:
                if "lines" not in block:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        original_text = span["text"]
                        modified_text = original_text

                        # Appliquer tous les remplacements
                        for old_text, new_text in all_replacements:
                            if old_text in modified_text:
                                count = modified_text.count(old_text)
                                modified_text = modified_text.replace(old_text, new_text)

                                key = f"{old_text} → {new_text}"
                                if key not in stats["replacements"]:
                                    stats["replacements"][key] = 0
                                stats["replacements"][key] += count

                        # Si le texte a changé, mettre à jour
                        if modified_text != original_text:
                            # Position et style du texte original
                            rect = fitz.Rect(span["bbox"])
                            font_size = span["size"]
                            font_color = span["color"]

                            # Masquer l'ancien texte
                            page.add_redact_annot(rect, fill=(1, 1, 1))
                            page.apply_redactions()

                            # Insérer le nouveau texte
                            # Convertir la couleur int en tuple RGB
                            if isinstance(font_color, int):
                                r = ((font_color >> 16) & 255) / 255
                                g = ((font_color >> 8) & 255) / 255
                                b = (font_color & 255) / 255
                                color = (r, g, b)
                            else:
                                color = (0, 0, 0)

                            page.insert_text(
                                (rect.x0, rect.y0 + font_size * 0.8),
                                modified_text,
                                fontsize=font_size,
                                color=color
                            )

        doc.save(output_path)
        doc.close()

        stats["success"] = True
        total = sum(stats["replacements"].values())
        print(f"✓ {input_path.name}: {total} remplacements (méthode extraction)")

    except Exception as e:
        stats["errors"].append(str(e))
        print(f"✗ Erreur: {e}")

    return stats


def analyze_pdf(pdf_path: Path) -> Dict:
    """
    Analyse un PDF pour identifier les occurrences de texte ADI.
    Utile pour prévisualiser les changements avant application.
    """
    import fitz

    analysis = {
        "file": pdf_path.name,
        "pages": 0,
        "findings": {},
        "logo_detected": False
    }

    try:
        doc = fitz.open(pdf_path)
        analysis["pages"] = len(doc)

        all_patterns = TEXT_REPLACEMENTS + FOOTER_REPLACEMENTS

        for page_num, page in enumerate(doc):
            text = page.get_text()

            for old_text, new_text in all_patterns:
                if old_text in text:
                    count = text.count(old_text)
                    key = old_text
                    if key not in analysis["findings"]:
                        analysis["findings"][key] = {"count": 0, "pages": []}
                    analysis["findings"][key]["count"] += count
                    analysis["findings"][key]["pages"].append(page_num + 1)

            # Détecter les images (potentiellement le logo)
            images = page.get_images()
            if images:
                analysis["logo_detected"] = True

        doc.close()

    except Exception as e:
        analysis["error"] = str(e)

    return analysis


def process_all_pdfs(dry_run: bool = False) -> List[Dict]:
    """
    Traite tous les PDFs du dossier Source.

    Args:
        dry_run: Si True, analyse seulement sans modifier

    Returns:
        Liste des statistiques pour chaque fichier
    """
    results = []
    pdfs = get_pdf_files()

    if not pdfs:
        print("Aucun PDF à traiter.")
        return results

    print(f"\n{'=' * 50}")
    print(f"{'ANALYSE' if dry_run else 'TRAITEMENT'} DE {len(pdfs)} FICHIERS")
    print(f"{'=' * 50}\n")

    for pdf in pdfs:
        if dry_run:
            # Mode analyse
            result = analyze_pdf(pdf)
            results.append(result)

            print(f"\n[PDF] {pdf.name}")
            print(f"   Pages: {result['pages']}")
            if result.get("findings"):
                print("   Textes trouvés:")
                for pattern, info in result["findings"].items():
                    print(f"     - '{pattern}': {info['count']}x (pages {info['pages']})")
            if result.get("logo_detected"):
                print("   [!] Images/Logo detecte(s)")
        else:
            # Mode remplacement
            output_path = OUTPUT_DIR / f"MAS_{pdf.name}"
            result = replace_text_simple(pdf, output_path)
            results.append(result)

    return results


def save_log(results: List[Dict]) -> None:
    """Sauvegarde le rapport de traitement."""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "files_processed": len(results),
        "results": results
    }

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Rapport sauvegardé: {LOG_FILE}")


def print_summary(results: List[Dict]) -> None:
    """Affiche un résumé du traitement."""
    print(f"\n{'=' * 50}")
    print("RÉSUMÉ")
    print(f"{'=' * 50}")

    total_files = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    total_replacements = sum(
        sum(r.get("replacements", {}).values())
        for r in results
    )

    print(f"Fichiers traités: {total_files}")
    print(f"Succès: {successful}/{total_files}")
    print(f"Total remplacements: {total_replacements}")

    if any(r.get("errors") for r in results):
        print("\n[WARN] Erreurs rencontrees:")
        for r in results:
            if r.get("errors"):
                print(f"  - {r['file']}: {r['errors']}")


def main():
    """Point d'entrée principal."""
    # Force UTF-8 output on Windows
    import io
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("=" * 60)
    print("DOCADI-MAS: Rebranding PDF")
    print("AD Industries -> Motherson Aerospace")
    print("=" * 60)
    print()

    # Verifier les dependances
    if not check_dependencies():
        print("\n[X] Installation des dependances requise.")
        print("   pip install PyMuPDF")
        sys.exit(1)

    # Configurer les répertoires
    setup_directories()

    # Parser les arguments
    dry_run = "--dry-run" in sys.argv or "--analyze" in sys.argv

    if dry_run:
        print("\n[ANALYSE] Mode ANALYSE (dry-run)")
    else:
        print("\n[TRANSFORM] Mode TRANSFORMATION")

    # Traiter les fichiers
    results = process_all_pdfs(dry_run=dry_run)

    # Sauvegarder le rapport
    if results:
        save_log(results)
        print_summary(results)

    print("\n[OK] Termine!")

    if dry_run:
        print("\nPour appliquer les modifications:")
        print(f"  python {Path(__file__).name}")


if __name__ == "__main__":
    main()
