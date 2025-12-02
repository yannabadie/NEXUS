#!/usr/bin/env python3
"""
DOCADI-MAS: Script de rebranding AD Industries -> Motherson Aerospace

Ce script modifie:
1. Les fichiers DOCX (template Word)
2. Les fichiers PDF (fiches processus)

Changements appliqués:
- Logo: AD Industries -> Motherson
- Texte: "AD Industries", "AD Industrie", "ADI" -> "Motherson Aerospace", "MAS"
- Pied de page: mise à jour des références

Usage:
    python rebrand_documents.py
"""

import os
import shutil
import sys
from pathlib import Path
from zipfile import ZipFile
import re

# Chemins
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))
SOURCE_DIR = SCRIPT_DIR / "Source"
TEMPLATES_DIR = SCRIPT_DIR / "Templates"
OUTPUT_DIR = SCRIPT_DIR / "Output"

# Logo Motherson
MOTHERSON_LOGO = TEMPLATES_DIR / "mothersonlogo.png"

# Remplacements textuels
TEXT_REPLACEMENTS = [
    # Nom complet
    ("AD INDUSTRIES", "MOTHERSON AEROSPACE"),
    ("AD Industries", "Motherson Aerospace"),
    ("AD Industrie", "Motherson Aerospace"),
    ("AD industrie", "Motherson Aerospace"),
    # Acronymes
    ("ADI", "MAS"),
    # Variantes avec tirets/espaces
    ("AD-Industries", "Motherson-Aerospace"),
    ("AD - Industries", "Motherson Aerospace"),
]


def ensure_output_dir():
    """Crée le dossier de sortie s'il n'existe pas."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"[OK] Dossier de sortie: {OUTPUT_DIR}")


def process_docx(input_path: Path, output_path: Path):
    """
    Traite un fichier DOCX:
    - Remplace le texte dans document.xml, header*.xml, footer*.xml
    - Remplace le logo si présent
    """
    print(f"\n[DOCX] Traitement de: {input_path.name}")

    # DOCX = ZIP avec XML
    with ZipFile(input_path, 'r') as zin:
        # Créer un nouveau DOCX
        with ZipFile(output_path, 'w') as zout:
            for item in zin.namelist():
                content = zin.read(item)

                # Traiter les fichiers XML (texte)
                if item.endswith('.xml'):
                    try:
                        text = content.decode('utf-8')
                        original = text

                        # Appliquer les remplacements
                        for old, new in TEXT_REPLACEMENTS:
                            text = text.replace(old, new)

                        if text != original:
                            print(f"  [MOD] {item}")

                        content = text.encode('utf-8')
                    except UnicodeDecodeError:
                        pass  # Fichier binaire, on garde tel quel

                # Remplacer l'image du logo (word/media/image1.png typiquement)
                if item.startswith('word/media/') and item.endswith('.png'):
                    if MOTHERSON_LOGO.exists():
                        print(f"  [LOGO] Remplacement de {item}")
                        content = MOTHERSON_LOGO.read_bytes()

                zout.writestr(item, content)

    print(f"  [OK] Sauvegardé: {output_path.name}")


def process_pdf_with_pymupdf(input_path: Path, output_path: Path):
    """
    Traite un fichier PDF avec PyMuPDF:
    - Remplace le texte (annotations de rédaction)
    - Remplace le logo (image)

    Note: Le remplacement de texte dans les PDFs est complexe.
    PyMuPDF permet de masquer et ré-écrire, mais pas de remplacer directement.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("  [ERREUR] PyMuPDF non installé. pip install pymupdf")
        return False

    print(f"\n[PDF] Traitement de: {input_path.name}")

    doc = fitz.open(input_path)
    modified = False

    for page_num, page in enumerate(doc):
        # Rechercher et marquer le texte à remplacer
        for old_text, new_text in TEXT_REPLACEMENTS:
            text_instances = page.search_for(old_text)

            for inst in text_instances:
                print(f"  [TROUVÉ] Page {page_num + 1}: '{old_text}' -> '{new_text}'")

                # Créer une annotation de rédaction (masque le texte original)
                page.add_redact_annot(inst, text=new_text, fontsize=10)
                modified = True

        # Appliquer les rédactions
        page.apply_redactions()

        # Remplacer le logo (chercher l'image en haut à gauche)
        # C'est plus complexe - on identifie par position
        images = page.get_images()
        if images and MOTHERSON_LOGO.exists():
            # Typiquement le logo est la première image en haut de page
            for img_index, img in enumerate(images):
                xref = img[0]
                # Obtenir la position de l'image
                img_rects = page.get_image_rects(xref)
                for rect in img_rects:
                    # Si l'image est en haut à gauche (logo probable)
                    if rect.y0 < 100 and rect.x0 < 200:
                        print(f"  [LOGO] Page {page_num + 1}: Remplacement du logo")
                        # Supprimer l'ancienne image et insérer la nouvelle
                        page.delete_image(xref)
                        page.insert_image(rect, filename=str(MOTHERSON_LOGO))
                        modified = True
                        break

    if modified:
        doc.save(output_path)
        print(f"  [OK] Sauvegardé: {output_path.name}")
    else:
        # Copier sans modification
        shutil.copy(input_path, output_path)
        print(f"  [INFO] Aucune modification, copié tel quel")

    doc.close()
    return True


def process_pdf_simple(input_path: Path, output_path: Path):
    """
    Version simplifiée: copie le PDF et génère un rapport des occurrences à modifier.
    Utile si PyMuPDF ne peut pas modifier proprement.
    """
    try:
        import fitz
    except ImportError:
        print("  [ERREUR] PyMuPDF non installé")
        shutil.copy(input_path, output_path)
        return

    print(f"\n[PDF-ANALYSE] Analyse de: {input_path.name}")

    doc = fitz.open(input_path)
    report = []

    for page_num, page in enumerate(doc):
        page_text = page.get_text()

        for old_text, new_text in TEXT_REPLACEMENTS:
            if old_text in page_text:
                count = page_text.count(old_text)
                report.append(f"  Page {page_num + 1}: '{old_text}' x{count}")

    doc.close()

    if report:
        print("  Occurrences trouvées:")
        for line in report:
            print(line)
        print(f"\n  [INFO] Application des correctifs robustes via rebrand_pdfs...")
        
        # Importation dynamique pour éviter les cycles
        try:
            import rebrand_pdfs
            # Utiliser la logique robuste
            rebrand_pdfs.replace_text_in_pdf(input_path, output_path)
            rebrand_pdfs.replace_logo_in_pdf(output_path, MOTHERSON_LOGO)
        except ImportError:
            print("  [ERREUR] Impossible d'importer rebrand_pdfs.py")
            shutil.copy(input_path, output_path)
    else:
        print("  [OK] Aucune occurrence à modifier")
        # Appliquer quand même le logo pour PR4_MAB qui n'a pas de texte matché
        try:
            import rebrand_pdfs
            # Copier d'abord
            shutil.copy(input_path, output_path)
            rebrand_pdfs.replace_logo_in_pdf(output_path, MOTHERSON_LOGO)
        except ImportError:
             shutil.copy(input_path, output_path)

def main():
    """Point d'entrée principal."""
    print("=" * 60)
    print("DOCADI-MAS: Rebranding AD Industries -> Motherson Aerospace")
    print("=" * 60)

    # Créer le dossier de sortie
    ensure_output_dir()

    # Vérifier le logo
    if not MOTHERSON_LOGO.exists():
        print(f"[ATTENTION] Logo Motherson non trouvé: {MOTHERSON_LOGO}")
    else:
        print(f"[OK] Logo Motherson trouvé: {MOTHERSON_LOGO}")

    # Traiter les templates DOCX
    print("\n" + "-" * 40)
    print("TEMPLATES WORD (.docx)")
    print("-" * 40)

    for docx_file in TEMPLATES_DIR.glob("*.docx"):
        output_file = OUTPUT_DIR / docx_file.name
        process_docx(docx_file, output_file)

    # Traiter les PDFs
    print("\n" + "-" * 40)
    print("FICHES PROCESSUS (.pdf)")
    print("-" * 40)

    for pdf_file in SOURCE_DIR.glob("*.pdf"):
        output_file = OUTPUT_DIR / pdf_file.name
        # Utiliser l'analyse simple pour commencer
        process_pdf_simple(pdf_file, output_file)

    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ")
    print("=" * 60)
    print(f"Fichiers traités dans: {OUTPUT_DIR}")
    print("\nProchaines étapes recommandées:")
    print("1. Vérifier les fichiers DOCX modifiés")
    print("2. Pour les PDFs:")
    print("   - Option A: Régénérer depuis les fichiers Excel source (.xls)")
    print("   - Option B: Utiliser Adobe Acrobat pour modification manuelle")
    print("   - Option C: Utiliser le script avec modification PyMuPDF (expérimental)")


if __name__ == "__main__":
    main()
