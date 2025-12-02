"""
NEXUS Rebranding Solution v2.0
==============================
Robust PDF rebranding for AD Industries → Motherson Aerospace

Solution Design:
1. Extract exact text positions and font info from source
2. Redact old content with white rectangles
3. Insert new text matching original font characteristics as closely as possible
4. Insert new logo at exact original logo position
5. Handle all pages, not just first

Key Improvements over v1:
- Uses proper text extraction with font/size info
- Redacts then inserts at exact positions
- Handles ADI vs ADI-as-substring distinction
- Preserves layout by matching original text metrics
"""

import fitz  # PyMuPDF
import os
import re


def get_text_replacements():
    """Define all text replacements needed."""
    return {
        # Full company name
        "AD Industries": "Motherson Aerospace",
        # French variants
        "groupe ADI": "groupe MAS",
        "ADI group": "MAS group",
        # Location-specific (preserve the location part)
        # We'll handle ADIMC, ADIHB etc. specially
    }


def should_replace_adi(context_before, context_after):
    """
    Determine if 'ADI' should be replaced based on context.
    We want to replace standalone ADI, but not substrings like 'TRADITION'.
    """
    # Check if it's part of a larger word
    if context_before and context_before[-1].isalpha():
        return False
    if context_after and context_after[0].isalpha() and context_after[0] not in ('M', 'H'):
        # Allow ADIMC, ADIHB (site codes) - these become MASMC, MASHB
        if not context_after.startswith(('MC', 'HB', ' ')):
            return False
    return True


def find_and_replace_text(page, old_text, new_text, preserve_style=True):
    """
    Find all instances of old_text and replace with new_text.
    Returns list of areas that were modified.
    """
    modified_areas = []

    # Search for text instances
    text_instances = page.search_for(old_text)

    for rect in text_instances:
        # Get the text block info at this location to determine font/size
        blocks = page.get_text("dict", clip=rect)["blocks"]

        # Determine font properties from original
        font_name = "helv"  # Default fallback
        font_size = 10
        text_color = (0, 0, 0)

        for block in blocks:
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if old_text in span.get("text", ""):
                            font_size = span.get("size", 10)
                            # Try to preserve color
                            color_int = span.get("color", 0)
                            text_color = (
                                ((color_int >> 16) & 0xFF) / 255,
                                ((color_int >> 8) & 0xFF) / 255,
                                (color_int & 0xFF) / 255
                            )
                            break

        # Expand rect slightly to ensure complete coverage
        expanded_rect = fitz.Rect(
            rect.x0 - 1,
            rect.y0 - 1,
            rect.x1 + 1,
            rect.y1 + 1
        )

        # Redact the old text (white fill)
        page.add_redact_annot(expanded_rect, fill=(1, 1, 1))
        page.apply_redactions()

        # Insert new text at same position
        # Adjust position for text baseline
        text_point = fitz.Point(rect.x0, rect.y1 - 2)  # Baseline adjustment

        try:
            page.insert_text(
                text_point,
                new_text,
                fontname="helv",  # Standard font that works
                fontsize=font_size,
                color=text_color
            )
        except Exception as e:
            print(f"  Warning: Could not insert text '{new_text}': {e}")

        modified_areas.append(rect)

    return modified_areas


def replace_logo(page, old_logo_rect, new_logo_path):
    """
    Remove old logo and insert new one at the same position.
    """
    if not os.path.exists(new_logo_path):
        print(f"  Warning: Logo file not found: {new_logo_path}")
        return False

    # Redact old logo area
    page.add_redact_annot(old_logo_rect, fill=(1, 1, 1))
    page.apply_redactions()

    # Insert new logo, scaled to fit original area
    try:
        page.insert_image(old_logo_rect, filename=new_logo_path)
        return True
    except Exception as e:
        print(f"  Warning: Could not insert logo: {e}")
        return False


def detect_logo_position(page):
    """
    Detect the position of the AD Industries logo (usually top-left header).
    Returns the Rect of the logo, or a default position.
    """
    # Get all images on the page
    images = page.get_images(full=True)

    for img in images:
        xref = img[0]
        rects = page.get_image_rects(xref)
        for rect in rects:
            # Logo is typically in top-left area (y < 120, x < 250)
            if rect.y0 < 120 and rect.x0 < 250:
                return rect

    # Default position based on analysis
    return fitz.Rect(55, 59, 188, 83)


def rebrand_pdf_v2(input_path, output_path, logo_path):
    """
    Main rebranding function - V2 with improved accuracy.
    """
    print(f"Processing: {input_path}")

    if not os.path.exists(input_path):
        print(f"  ERROR: Input file not found")
        return False

    try:
        doc = fitz.open(input_path)

        # Text replacements to make
        replacements = get_text_replacements()

        for page_num, page in enumerate(doc):
            print(f"  Page {page_num + 1}/{len(doc)}")

            # 1. Replace logo on first page (or all pages if logo appears on all)
            logo_rect = detect_logo_position(page)
            if logo_rect:
                print(f"    - Replacing logo at {logo_rect}")
                replace_logo(page, logo_rect, logo_path)

            # 2. Replace text strings
            for old_text, new_text in replacements.items():
                areas = find_and_replace_text(page, old_text, new_text)
                if areas:
                    print(f"    - Replaced '{old_text}' -> '{new_text}' ({len(areas)} instances)")

            # 3. Handle ADI -> MAS with context awareness
            # Search for ADI and check each instance
            adi_instances = page.search_for("ADI")
            for rect in adi_instances:
                # Get surrounding context
                expanded = fitz.Rect(rect.x0 - 20, rect.y0, rect.x1 + 20, rect.y1)
                context = page.get_text(clip=expanded)

                # Check if this ADI should be replaced
                adi_pos = context.find("ADI")
                if adi_pos >= 0:
                    before = context[:adi_pos]
                    after = context[adi_pos + 3:]

                    if should_replace_adi(before, after):
                        # Check if it's a site code like ADIMC, ADIHB
                        if after.startswith(("MC", "HB")):
                            new_text = "MAS" + after[:2]
                            search_text = "ADI" + after[:2]
                            areas = find_and_replace_text(page, search_text, new_text)
                            if areas:
                                print(f"    - Replaced site code '{search_text}' -> '{new_text}'")

        # Save the result
        doc.save(output_path, garbage=4, deflate=True)
        doc.close()
        print(f"  Saved to: {output_path}")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def rebrand_all_pdfs(source_dir, output_dir, logo_path):
    """
    Process all PDFs in source directory.
    """
    import glob

    pdf_files = glob.glob(os.path.join(source_dir, "*.pdf"))

    print(f"\n=== NEXUS PDF Rebranding v2.0 ===")
    print(f"Source: {source_dir}")
    print(f"Output: {output_dir}")
    print(f"Logo: {logo_path}")
    print(f"Files to process: {len(pdf_files)}")
    print("=" * 40)

    results = []
    for pdf_file in pdf_files:
        filename = os.path.basename(pdf_file)
        output_path = os.path.join(output_dir, f"Rebranded_{filename}")

        success = rebrand_pdf_v2(pdf_file, output_path, logo_path)
        results.append((filename, success))

    print("\n=== SUMMARY ===")
    for filename, success in results:
        status = "OK" if success else "FAILED"
        print(f"  [{status}] {filename}")

    return results


if __name__ == "__main__":
    # Paths
    BASE_DIR = r"C:\Code\NEXUS\20_NEXUS - Copie\external_sources\DOCADI-MAS"
    SOURCE_DIR = os.path.join(BASE_DIR, "Source")
    LOGO_PATH = os.path.join(BASE_DIR, "Templates", "mothersonlogo.png")
    OUTPUT_DIR = os.getcwd()

    # Run rebranding
    rebrand_all_pdfs(SOURCE_DIR, OUTPUT_DIR, LOGO_PATH)
