import os
import glob
from rebrand_docx import rebrand_docx
from rebrand_pdf import rebrand_pdf

def main():
    base_dir = r"C:\Code\NEXUS\20_NEXUS - Copie\external_sources\DOCADI-MAS"
    output_dir = os.getcwd() # Save to current workspace
    
    # Paths
    template_path = os.path.join(base_dir, "Templates", "Template.docx")
    logo_path = os.path.join(base_dir, "Templates", "mothersonlogo.png")
    pdf_source_dir = os.path.join(base_dir, "Source")

    print("=== Starting Rebranding Project ===")

    # 1. Process DOCX
    if os.path.exists(template_path):
        print("\n--- Processing DOCX ---")
        docx_output = os.path.join(output_dir, "Rebranded_Template.docx")
        rebrand_docx(template_path, docx_output, logo_path)
    else:
        print(f"Warning: DOCX Template not found at {template_path}")

    # 2. Process PDFs
    print("\n--- Processing PDFs ---")
    pdf_files = glob.glob(os.path.join(pdf_source_dir, "*.pdf"))
    if not pdf_files:
        print(f"Warning: No PDF files found in {pdf_source_dir}")
    
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        pdf_output = os.path.join(output_dir, f"Rebranded_{filename}")
        rebrand_pdf(pdf_file, pdf_output, logo_path)

    print("\n=== Rebranding Complete ===")

if __name__ == "__main__":
    main()

