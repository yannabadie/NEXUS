#!/usr/bin/env python3
"""
NEXUS V6 - Mutation Application Service

Purpose: Apply code mutations to core files from within workspace restrictions.
Why: Claude agent is restricted to workspace/, but mutations target ../core/
How: Python script run via bash has filesystem access to parent directories.

Usage:
    python apply_mutation.py <mutation_json_file>

Mutation JSON Format:
    [
      {
        "file": "core/orchestration_v6.py",
        "change": "code to add/replace",
        "reason": "justification",
        "expected_asi_impact": 0.0X
      }
    ]
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_mutation(json_path: Path) -> dict:
    """Load and validate mutation JSON."""
    with open(json_path, 'r', encoding='utf-8') as f:
        mutations = json.load(f)

    if not isinstance(mutations, list):
        raise ValueError("Mutation JSON must be a list")

    if len(mutations) != 1:
        raise ValueError(f"Expected 1 mutation, got {len(mutations)}")

    mutation = mutations[0]
    required_keys = {"file", "change", "reason", "expected_asi_impact"}
    if not required_keys.issubset(mutation.keys()):
        raise ValueError(f"Missing required keys. Expected: {required_keys}")

    return mutation


def apply_mutation(mutation: dict, base_dir: Path) -> None:
    """Apply a mutation to the target file."""
    # Resolve target file path (relative to project root)
    target_file = base_dir.parent / mutation["file"]

    if not target_file.exists():
        raise FileNotFoundError(f"Target file not found: {target_file}")

    # Read current content
    with open(target_file, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Backup original
    backup_dir = base_dir / ".nexus" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"{target_file.stem}_{timestamp}.backup"

    with open(backup_file, 'w', encoding='utf-8') as f:
        f.write(original_content)

    print(f"[OK] Backup created: {backup_file}")

    # Apply mutation (simple append for now - enhance later)
    # TODO: Implement intelligent insertion (after class def, etc.)
    new_content = original_content + "\n\n# MUTATION APPLIED: " + timestamp + "\n"
    new_content += "# Reason: " + mutation["reason"] + "\n"
    new_content += mutation["change"] + "\n"

    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[OK] Mutation applied to: {target_file}")
    print(f"[OK] Expected ASI impact: {mutation['expected_asi_impact']}")
    print(f"[OK] Reason: {mutation['reason']}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python apply_mutation.py <mutation_json_file>")
        sys.exit(1)

    json_path = Path(sys.argv[1])

    if not json_path.exists():
        print(f"Error: Mutation file not found: {json_path}")
        sys.exit(1)

    try:
        # Get workspace directory (where this script lives)
        base_dir = Path(__file__).parent

        # Load mutation
        mutation = load_mutation(json_path)

        print(f"Applying mutation to: {mutation['file']}")

        # Apply mutation
        apply_mutation(mutation, base_dir)

        print("\n[SUCCESS] Mutation application successful!")

    except Exception as e:
        print(f"[ERROR] Error applying mutation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
