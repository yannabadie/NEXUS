import re
from pathlib import Path

def scan(filename, pattern):
    try:
        content = Path(filename).read_text(encoding='utf-8', errors='ignore')
        matches = re.findall(pattern, content)
        unique = sorted(set(matches))
        print(f"--- {filename} Matches ---")
        for m in unique:
            print(m)
    except Exception as e:
        print(f"Error reading {filename}: {e}")

if __name__ == "__main__":
    scan("deepseek_docs.html", r"deepseek-[a-zA-Z0-9\-\.]+")
    scan("gemini_docs.html", r"gemini-[a-zA-Z0-9\-\.]+")
