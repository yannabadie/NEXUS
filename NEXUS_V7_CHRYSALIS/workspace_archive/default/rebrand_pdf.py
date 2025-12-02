import fitz  # PyMuPDF
import os

def rebrand_pdf(input_path, output_path, logo_path):
    """
    Rebrands a PDF file by redacting old text and overlaying new text/logo.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return False

    try:
        doc = fitz.open(input_path)
        
        # Define replacements
        replacements = {
            "AD Industries": "Motherson Aerospace",
            "ADI": "MAS"
        }

        for page_num, page in enumerate(doc):
            # 1. Targeted Redaction of Old Logo (Top Left Header)
            # Coordinates from analysis: Rect(55.22, 59.55, 188.125, 82.65)
            # We use a slightly larger box to ensure full coverage.
            redaction_rect = fitz.Rect(50, 50, 200, 90)
            page.add_redact_annot(redaction_rect, fill=(1, 1, 1)) # White fill
            page.apply_redactions()

            # 2. Insert New Logo (Scaled to fit original logo area)
            if os.path.exists(logo_path):
                # Target box matching the old logo's position to avoid obscuring text
                # Analysis showed old logo was approx 133x23 units.
                # We fit the new logo into this box.
                logo_dest_rect = fitz.Rect(55, 60, 188, 82)
                page.insert_image(logo_dest_rect, filename=logo_path)
            
            # 3. Text Replacement (Best Effort with better Font)
            replacements = {
                "AD Industries": "Motherson Aerospace",
                "ADI": "MAS"
            }
            for old_text, new_text in replacements.items():
                hits = page.search_for(old_text)
                for rect in hits:
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    page.apply_redactions()
                    # Use Helvetica (helv) which is standard, size 10 to match body text approx
                    page.insert_text(rect.tl, new_text, fontname="helv", fontsize=10, color=(0, 0, 0))

        doc.save(output_path)
        print(f"Successfully saved rebranded PDF to {output_path}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

if __name__ == "__main__":
    # Paths
    BASE_DIR = r"C:\Code\NEXUS\20_NEXUS - Copie\external_sources\DOCADI-MAS"
    SOURCE_DIR = os.path.join(BASE_DIR, "Source")
    LOGO_PATH = os.path.join(BASE_DIR, "Templates", "mothersonlogo.png")
    
    # Files to process
    import glob
    pdf_files = glob.glob(os.path.join(SOURCE_DIR, "*.pdf"))

    for input_full_path in pdf_files:
        pdf_filename = os.path.basename(input_full_path)
        output_full_path = f"Rebranded_{pdf_filename}"
        
        print(f"Processing {pdf_filename}...")
        rebrand_pdf(input_full_path, output_full_path, LOGO_PATH)
