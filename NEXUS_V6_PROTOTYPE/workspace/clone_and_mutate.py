#!/usr/bin/env python3
"""
NEXUS V6 - Clone and Mutate Service

Purpose: Allow agents to safely test mutations by cloning the current environment
         to GENERATION_ACTIVE before applying changes.

Usage:
    python clone_and_mutate.py <target_name> <mutation_json_file>

Example:
    python clone_and_mutate.py TEST_V6.1_FIX_MEMORY workspace/mutation.json
"""

import json
import sys
import shutil
import os
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


def clone_project(source_dir: Path, target_dir: Path) -> None:
    """Clone the project to the target directory, excluding specific files."""
    if target_dir.exists():
        print(f"[WARN] Target directory {target_dir} exists. Cleaning up...")
        shutil.rmtree(target_dir)
    
    target_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Cloning {source_dir} to {target_dir}...")

    def ignore_patterns(path, names):
        return {
            '__pycache__', '*.pyc', '.nexus', 'workspace', '.git',
            '.env', 'venv', '.idea', '.vscode'
        }

    # We manually copy to handle the workspace folder specially if needed, 
    # but shutil.copytree with ignore is cleaner for the main structure.
    # Note: we want to copy the PARENT of the workspace (the project root), 
    # but excluding the 'workspace' directory itself to avoid recursive loops 
    # if we are running from within it? 
    # No, we are in NEXUS_V6_PROTOTYPE/workspace. We want to copy NEXUS_V6_PROTOTYPE.
    
    # Source is the project root (parent of workspace)
    shutil.copytree(
        source_dir,
        target_dir,
        ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '.nexus', 'workspace', '.git', '.env', 
            'GENERATION_ACTIVE', 'NEXUS_V5_PRAGMATIC' # Explicitly ignore sibling projects
        )
    )
    
    # We also need to create a fresh workspace in the target
    (target_dir / "workspace").mkdir(exist_ok=True)
    (target_dir / "workspace" / "_IO_BUFFER").mkdir(exist_ok=True)
    (target_dir / "workspace" / ".nexus").mkdir(exist_ok=True)
    
    print("[OK] Project cloned.")


def apply_mutation_to_target(mutation: dict, target_dir: Path) -> None:
    """Apply mutation to the cloned project."""
    target_file = target_dir / mutation["file"]

    if not target_file.exists():
        print(f"[WARN] Target file {target_file} does not exist in clone. Creating it.")
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.touch()

    # Read current content
    with open(target_file, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Apply mutation (append)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_content = original_content + "\n\n# MUTATION APPLIED: " + timestamp + "\n"
    new_content += "# Reason: " + mutation["reason"] + "\n"
    new_content += mutation["change"] + "\n"

    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[OK] Mutation applied to: {target_file}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python clone_and_mutate.py <target_name> <mutation_json_file>")
        sys.exit(1)

    target_name = sys.argv[1]
    json_path = Path(sys.argv[2])

    if not json_path.exists():
        print(f"Error: Mutation file not found: {json_path}")
        sys.exit(1)

    # Paths
    # We are in NEXUS_V6_PROTOTYPE/workspace
    # Project root is ..
    project_root = Path(__file__).parent.parent.resolve()
    
    # Global root is ../.. (20_NEXUS)
    global_root = project_root.parent.resolve()
    
    # Generation Active dir
    gen_active_dir = global_root / "GENERATION_ACTIVE"
    if not gen_active_dir.exists():
        gen_active_dir.mkdir()
        
    target_dir = gen_active_dir / target_name

    try:
        # 1. Load mutation
        mutation = load_mutation(json_path)
        print(f"[INFO] Loaded mutation for file: {mutation['file']}")

        # 2. Clone project
        clone_project(project_root, target_dir)

        # 3. Apply mutation
        apply_mutation_to_target(mutation, target_dir)

        print("\n" + "="*60)
        print(f"SUCCESS: Sandbox created at {target_dir}")
        print(f"To test: cd {target_dir} && python nexus6.py")
        print("="*60)

    except Exception as e:
        print(f"[ERROR] Failed to clone and mutate: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
