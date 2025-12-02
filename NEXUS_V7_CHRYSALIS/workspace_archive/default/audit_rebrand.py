import fitz

def audit_logo_placement():
    # Dimensions from rebrand_pdf.py
    logo_rect = fitz.Rect(55, 60, 188, 82)
    
    print("--- Red Team Audit: Logo Placement Safety ---")
    print(f"New Logo Rect: {logo_rect}")
    print(f"  Bottom Y: {logo_rect.y1}")
    
    # Critical text zone from analyze_layout.py
    # Text Block: Rect(254.33, 45.28, 525.10, 63.76) -> 'PROCESSUS LOCAL...'
    # Wait, x=254 is far to the right. The logo is at x=55..188.
    # So horizontal overlap is impossible with 'PROCESSUS LOCAL'.
    
    # Let's check what is BELOW the logo.
    # Text Block: Rect(70.94, 123.79, 274.73, 137.17) -> '1. OBJET...'
    # Logo ends at y=82. Text starts at y=123.
    # Safety margin: 123 - 82 = 41 units. 
    # Result: SAFE.
    
    # Let's check what is to the RIGHT of the logo.
    # Text: 'PROCESSUS LOCAL' at x=254.
    # Logo ends at x=188.
    # Safety margin: 254 - 188 = 66 units.
    # Result: SAFE.
    
    print("Conclusion: Coordinates seem theoretically safe from overlap.")
    
    # Attack vector: Font mismatch.
    # User complained "polices ne sont pas les memes".
    # I changed it to "helv" (Helvetica). 
    # The original document likely uses Arial or a specific sans-serif.
    # Helvetica is the standard PDF Type1 font, close enough for a script without embedding fonts.
    # However, font SIZE 10 might be too small or large.
    # Original text "1. OBJET" height is ~14 units (137-123).
    # My inserted text is size 10. That seems plausible.
    
    print("Recommendation: Visual inspection required to confirm font weight/style match.")

if __name__ == "__main__":
    audit_logo_placement()
