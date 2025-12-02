#!/usr/bin/env python3
"""
DOCADI-MAS: Script de rebranding PDF avec PyMuPDF (ROBUST)

Ce script modifie les PDFs en:
1. Remplaçant le texte "ADI" par "MAS" (avec gestion de l'espace)
2. Remplaçant le logo AD Industries par Motherson (avec meilleure détection)

Usage:
    python rebrand_pdfs.py
"""

import fitz  # PyMuPDF
from pathlib import Path
import shutil

# Chemins
SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR / "Source"
TEMPLATES_DIR = SCRIPT_DIR / "Templates"
OUTPUT_DIR = SCRIPT_DIR / "Output"

# Logo Motherson
MOTHERSON_LOGO = TEMPLATES_DIR / "mothersonlogo.png"

# Remplacements textuels
TEXT_REPLACEMENTS = [
    ("AD INDUSTRIES", "MOTHERSON AEROSPACE"),
    ("AD Industries", "Motherson Aerospace"),
    ("AD Industrie", "Motherson Aerospace"),
    ("AD industrie", "Motherson Aerospace"),
    ("ADI", "MAS"),
]

def replace_text_in_pdf(input_path: Path, output_path: Path):
    """
    Remplace le texte dans un PDF en utilisant redaction + insertion.
    Cela permet d'éviter que le texte soit coupé si la nouvelle chaîne est plus longue.
    """
    print(f"\n[PDF] Traitement de: {input_path.name}")

    doc = fitz.open(input_path)
    changes_made = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # On collecte toutes les zones à modifier d'abord
        replacements_on_page = []

        for old_text, new_text in TEXT_REPLACEMENTS:
            text_instances = page.search_for(old_text)

            for rect in text_instances:
                replacements_on_page.append((rect, old_text, new_text))

        # Appliquer les modifications
        for rect, old_text, new_text in replacements_on_page:
            # 1. Masquer l'ancien texte (Redaction avec fond blanc)
            page.add_redact_annot(rect, fill=(1, 1, 1))
            
            # 2. Calculer la position d'insertion (bas gauche du rect)
            insert_point = rect.bl
            # Remonter légèrement pour l'alignement de base (ajustement empirique)
            insert_point.y -= 2 

            # 3. Estimer la taille de police (hauteur du rect * 0.8 environ)
            fontsize = rect.height * 0.75
            if fontsize < 6: fontsize = 8 # Minimum de lisibilité
            
            # 4. Préparer l'insertion du nouveau texte
            # On le fera APRES avoir appliqué les rédactions pour éviter les conflits
            
        # Appliquer TOUTES les rédactions (efface le texte visuellement)
        page.apply_redactions()

        # Maintenant, insérer le nouveau texte
        for rect, old_text, new_text in replacements_on_page:
            insert_point = rect.bl
            insert_point.y -= (rect.height * 0.15) # Ajustement fin
            
            fontsize = rect.height * 0.85
            
            # Insérer le texte
            page.insert_text(
                insert_point,
                new_text,
                fontsize=fontsize,
                fontname="helv",
                color=(0, 0, 0)
            )
            changes_made += 1
            print(f"  Page {page_num + 1}: Remplacement '{old_text}' -> '{new_text}'")

    # Sauvegarder
    doc.save(output_path)
    doc.close()
    print(f"  [OK] Sauvegardé: {output_path.name} ({changes_made} modifs)")
    return changes_made


def replace_logo_in_pdf(pdf_path: Path, logo_path: Path):
    """
    Remplace le logo dans un PDF.
    Cherche TOUTES les images dans le quadrant haut-gauche.
    """
    if not logo_path.exists():
        print(f"  [SKIP] Logo non trouvé: {logo_path}")
        return 0

    doc = fitz.open(pdf_path)
    logos_replaced = 0

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        
        # Zone de recherche du logo: Haut Gauche
        # x < 200, y < 150 (plus large que précedemment)
        logo_area = fitz.Rect(0, 0, 200, 150)
        
        candidates = []

        for img_index, img in enumerate(images):
            xref = img[0]
            try:
                rects = page.get_image_rects(xref)
                for rect in rects:
                    # Intersection avec la zone logo
                    if rect.intersects(logo_area):
                        # C'est un candidat logo
                        candidates.append((rect, xref))
            except:
                pass
        
        if candidates:
            # Trier par position (le plus en haut à gauche est prioritaire)
            candidates.sort(key=lambda x: (x[0].y0, x[0].x0))
            
            # On remplace le PREMIER candidat trouvé (le vrai logo)
            # Et on supprime les autres s'ils sont très proches (superposition?)
            
            primary_rect, primary_xref = candidates[0]
            print(f"  [LOGO] Page {page_num + 1}: Remplacement à {primary_rect}")

            # 1. Masquer l'ancien logo (Redaction blanche)
            page.draw_rect(primary_rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # 2. Insérer le nouveau logo
            # On garde le ratio d'aspect du nouveau logo si possible, ou on fit au rect?
            # Mieux: Fit au rect de l'ancien logo pour conserver la mise en page
            page.insert_image(primary_rect, filename=str(logo_path))
            logos_replaced += 1

            # Si d'autres images "parasites" sont dans la zone logo, on peut les masquer aussi?
            # Pour l'instant, on ne touche qu'au principal pour éviter de casser le header.

    doc.saveIncr()
    doc.close()
    return logos_replaced

def main():
    print("=" * 60)
    print("DOCADI-MAS: Rebranding PDF (Robust)")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    pdf_files = list(SOURCE_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("Aucun PDF trouvé.")
        return

    for pdf_file in pdf_files:
        output_file = OUTPUT_DIR / pdf_file.name
        
        # 1. Remplacement Texte
        replace_text_in_pdf(pdf_file, output_file)
        
        # 2. Remplacement Logo (sur le fichier de sortie)
        replace_logo_in_pdf(output_file, MOTHERSON_LOGO)

if __name__ == "__main__":
    main()