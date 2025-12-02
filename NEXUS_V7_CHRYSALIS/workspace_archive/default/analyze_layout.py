import fitz
import os

def analyze_pdf_layout(pdf_path):
    print(f"Analyzing layout for: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    # Analyze first 3 pages if available
    for i in range(min(3, len(doc))):
        print(f"\n=== PAGE {i+1} ===")
        page = doc[i]
        
        # Dump Images
        print("--- Images ---")
        image_list = page.get_images(full=True)
        for img in image_list:
            xref = img[0]
            rects = page.get_image_rects(xref)
            for r in rects:
                print(f"Image: {r} (xref={xref})")
if __name__ == "__main__":
    base_dir = r"C:\\Code\\NEXUS\\20_NEXUS - Copie\\external_sources\\DOCADI-MAS\\Source"
    # Analyze one of the problematic files
    target_pdf = os.path.join(base_dir, "PR4-MCO_Rev_03_Fiche Processus Industrialiser.pdf")
    analyze_pdf_layout(target_pdf)
