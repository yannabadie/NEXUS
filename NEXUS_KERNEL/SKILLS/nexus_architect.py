#!/usr/bin/env python3
"""
NEXUS Architect - Code Architecture Mapping Tool
Uses pymermaider CLI to generate Mermaid diagrams of code structure
"""

import argparse
import os
import sys
import subprocess
import shutil
from pathlib import Path


def create_architecture_map(target_path: str, output_file: str = "ARCHITECTURE_MAP.md"):
    """
    Generate architecture map for a given directory.

    Args:
        target_path: Path to analyze
        output_file: Name of output file (default: ARCHITECTURE_MAP.md)
    """
    target = Path(target_path).resolve()

    if not target.exists():
        print(f"ERROR: Path does not exist: {target}")
        sys.exit(1)

    if not target.is_dir():
        print(f"ERROR: Path is not a directory: {target}")
        sys.exit(1)

    print(f"[*] Analyzing architecture: {target}")
    print(f"[*] Generating Mermaid diagram...")

    # Create temporary output directory
    temp_output = target / ".nexus_temp_output"
    temp_output.mkdir(exist_ok=True)

    try:
        # Run pymermaider CLI
        result = subprocess.run(
            ["uv", "run", "pymermaider", str(target), "-o", str(temp_output)],
            capture_output=True,
            text=True,
            check=True
        )

        print(f"[OK] pymermaider completed")

        # Find generated mermaid file (can be .mmd or .md)
        mermaid_files = list(temp_output.glob("*.mmd")) + list(temp_output.glob("*.md"))

        if not mermaid_files:
            print("[WARNING] No mermaid files generated. Checking output...")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            sys.exit(1)

        # Read the first mermaid file
        mermaid_file = mermaid_files[0]
        with open(mermaid_file, 'r', encoding='utf-8') as f:
            diagram = f.read()

        # Remove existing mermaid code fences if present
        if diagram.startswith("```mermaid"):
            diagram = diagram[len("```mermaid"):].lstrip('\n')
        if diagram.endswith("```"):
            diagram = diagram[:-3].rstrip('\n')

        # Create output file path
        output_path = target / output_file

        # Write diagram to markdown file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Architecture Map\n\n")
            f.write(f"Generated for: `{target}`\n\n")
            from datetime import datetime
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("```mermaid\n")
            f.write(diagram)
            if not diagram.endswith('\n'):
                f.write("\n")
            f.write("```\n")

        print(f"[OK] Architecture map saved to: {output_path}")
        print(f"[*] Diagram size: {len(diagram)} characters")

        # Cleanup temporary directory
        shutil.rmtree(temp_output, ignore_errors=True)

        return output_path

    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR running pymermaider: {e}")
        print(f"STDOUT: {e.stdout}")
        print(f"STDERR: {e.stderr}")
        shutil.rmtree(temp_output, ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR generating diagram: {e}")
        shutil.rmtree(temp_output, ignore_errors=True)
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="NEXUS Architect - Generate code architecture maps using Mermaid",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python nexus_architect.py /path/to/project
  python nexus_architect.py . -o CUSTOM_MAP.md
        """
    )

    parser.add_argument(
        "path",
        help="Path to analyze (directory)"
    )

    parser.add_argument(
        "-o", "--output",
        default="ARCHITECTURE_MAP.md",
        help="Output filename (default: ARCHITECTURE_MAP.md)"
    )

    args = parser.parse_args()

    create_architecture_map(args.path, args.output)


if __name__ == "__main__":
    main()
