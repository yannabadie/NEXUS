import os
from docx import Document
from docx.shared import Inches

def rebrand_docx(input_path, output_path, logo_path):
    """
    Rebrands a DOCX file by replacing text and the logo.
    """
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return False
    
    try:
        doc = Document(input_path)
        
        # 1. Replace Text in Paragraphs
        for para in doc.paragraphs:
            if "AD Industries" in para.text:
                para.text = para.text.replace("AD Industries", "Motherson Aerospace")
            if "ADI" in para.text:
                para.text = para.text.replace("ADI", "MAS")

        # 2. Replace Text in Tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if "AD Industries" in para.text:
                            para.text = para.text.replace("AD Industries", "Motherson Aerospace")
                        if "ADI" in para.text:
                            para.text = para.text.replace("ADI", "MAS")
                            
        # 3. Header/Footer processing
        for section in doc.sections:
            header = section.header
            
            # ALWAYS insert Logo in Header (First paragraph)
            if os.path.exists(logo_path):
                # If header has paragraphs, use the first one. If not, create one.
                if len(header.paragraphs) == 0:
                    header.add_paragraph()
                
                p = header.paragraphs[0]
                # Optional: Clear existing content in first paragraph if it's just the logo
                # p.clear() # Be careful not to delete text if it's mixed.
                # For now, prepend/append. Let's prepend a run.
                r = p.add_run()
                r.add_picture(logo_path, width=Inches(1.5))
                # Add a tab or space
                r.add_text("\t") 

            for para in header.paragraphs:
                if "AD Industries" in para.text:
                    para.text = para.text.replace("AD Industries", "Motherson Aerospace")
                if "ADI" in para.text:
                    para.text = para.text.replace("ADI", "MAS")

            footer = section.footer
            for para in footer.paragraphs:
                 if "AD Industries" in para.text:
                    para.text = para.text.replace("AD Industries", "Motherson Aerospace")
                 if "ADI" in para.text:
                    para.text = para.text.replace("ADI", "MAS")

        doc.save(output_path)
        print(f"Successfully saved rebranded file to {output_path}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

if __name__ == "__main__":
    # Paths are relative to the workspace root where this script runs
    # Adjust these paths to match the actual location or copy files to workspace first
    BASE_DIR = r"C:\Code\NEXUS\20_NEXUS - Copie\external_sources\DOCADI-MAS"
    TEMPLATE_PATH = os.path.join(BASE_DIR, "Templates", "Template.docx")
    LOGO_PATH = os.path.join(BASE_DIR, "Templates", "mothersonlogo.png")
    OUTPUT_PATH = "Rebranded_Template.docx"
    
    rebrand_docx(TEMPLATE_PATH, OUTPUT_PATH, LOGO_PATH)
