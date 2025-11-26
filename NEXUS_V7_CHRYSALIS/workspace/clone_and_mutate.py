#!/usr/bin/env python3
"""
NEXUS V7 - Clone and Mutate Service (Enhanced)

Purpose: Allow agents to safely test mutations by cloning the current environment
         to GENERATION_ACTIVE before applying changes.

Supports:
    - Multiple mutations in a single JSON file
    - Two actions: 'overwrite' (replace file) or 'append' (add to end)
    - Syntax validation for Python files via ast.parse()

Usage:
    python clone_and_mutate.py <target_name> <mutation_json_file>

Example:
    python clone_and_mutate.py TEST_V7.1_EVOLUTION workspace/mutation.json

Mutation JSON Schema:
[
  {
    "file": "path/to/file.py",
    "action": "overwrite",  // or "append" (default: "overwrite")
    "change": "new content or content to append",
    "reason": "why this mutation",
    "expected_asi_impact": 0.0
  }
]
"""

import ast
import json
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# ============================================================================
# SECURITY GUARDS - Prevent dangerous mutations
# ============================================================================

# Files that CANNOT be targeted by mutations (immutable)
PROTECTED_FILES = [
    "KERNEL.py",
    "KERNEL_HASH.txt",
    "core/governance/__init__.py",
    "core/governance/red_team/validator.py",
    "core/governance/red_team/alignment_tests.py",
]

# Patterns that CANNOT be added to config files (security bypass attempts)
FORBIDDEN_CONFIG_PATTERNS = [
    r"VALIDATION_TIER.*=.*[01]",           # Bypass Red Team (tier 0-1)
    r"SKIP.*RED.*TEAM.*=.*True",           # Skip Red Team
    r"RED_TEAM.*ENABLED.*=.*False",        # Disable Red Team
    r"ALIGNMENT.*CHECK.*=.*False",         # Disable alignment
    r"KERNEL.*VERIFY.*=.*False",           # Skip kernel check
]

# Minimum sizes for critical files (prevent lobotomization)
MIN_FILE_SIZES = {
    "prompts/system_gemini_v7.md": 5000,   # ~500 lines minimum
    "prompts/system_claude_v7.md": 5000,   # ~500 lines minimum
}


def validate_mutation_security(mutation: Dict[str, Any], index: int) -> None:
    """
    Security validation for a single mutation.
    Raises SecurityError if mutation violates safety rules.
    """
    file_path = mutation["file"]
    change = mutation["change"]
    action = mutation.get("action", "overwrite")

    # Check 1: Protected files cannot be mutated
    for protected in PROTECTED_FILES:
        if file_path == protected or file_path.endswith(protected):
            raise PermissionError(
                f"SECURITY VIOLATION (Mutation {index}): "
                f"Cannot mutate protected file '{file_path}'"
            )

    # Check 2: Forbidden patterns in config mutations
    if "config" in file_path.lower():
        for pattern in FORBIDDEN_CONFIG_PATTERNS:
            if re.search(pattern, change, re.IGNORECASE):
                raise PermissionError(
                    f"SECURITY VIOLATION (Mutation {index}): "
                    f"Forbidden security bypass pattern detected in config mutation"
                )

    # Check 3: Minimum file sizes (prevent lobotomization)
    if action == "overwrite":
        for critical_file, min_size in MIN_FILE_SIZES.items():
            if file_path == critical_file or file_path.endswith(critical_file):
                if len(change) < min_size:
                    raise ValueError(
                        f"SECURITY VIOLATION (Mutation {index}): "
                        f"Overwrite of '{file_path}' too small ({len(change)} < {min_size} chars). "
                        f"Use 'append' action to add content without destroying the original."
                    )


def load_mutations(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load and validate mutation JSON.

    Accepts:
        - A list of mutations: [{"file": ..., "change": ...}, ...]
        - A single mutation dict: {"file": ..., "change": ...} (converted to list)

    Required keys per mutation: file, change, reason
    Optional keys: action (default: 'overwrite'), expected_asi_impact
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Convert single dict to list
    if isinstance(data, dict):
        mutations = [data]
    elif isinstance(data, list):
        mutations = data
    else:
        raise ValueError("Mutation JSON must be a list or a dict")

    if len(mutations) == 0:
        raise ValueError("Mutation JSON is empty")

    # Validate each mutation
    required_keys = {"file", "change", "reason"}
    for i, mutation in enumerate(mutations):
        missing = required_keys - set(mutation.keys())
        if missing:
            raise ValueError(f"Mutation {i+1}: Missing required keys: {missing}")

        # Set default action if not specified
        if "action" not in mutation:
            mutation["action"] = "overwrite"

        # Validate action value
        if mutation["action"] not in ("overwrite", "append"):
            raise ValueError(f"Mutation {i+1}: Invalid action '{mutation['action']}'. Must be 'overwrite' or 'append'")

    return mutations


def clone_project(source_dir: Path, target_dir: Path) -> None:
    """Clone the project to the target directory, excluding specific files."""
    if target_dir.exists():
        print(f"[WARN] Target directory {target_dir} exists. Cleaning up...")
        shutil.rmtree(target_dir)

    # Note: Do NOT create target_dir here - copytree will create it
    print(f"[INFO] Cloning {source_dir} to {target_dir}...")

    # Clone with ignore patterns
    shutil.copytree(
        source_dir,
        target_dir,
        ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', '.nexus', 'workspace', '.git', '.env',
            'GENERATION_ACTIVE', 'archives', 'ARCHIVE',  # Ignore evolution & archive dirs
            'NEXUS_V5_PRAGMATIC', 'venv', '.idea', '.vscode'
        )
    )

    # Create fresh workspace structure in target
    (target_dir / "workspace").mkdir(exist_ok=True)
    (target_dir / "workspace" / "_IO_BUFFER").mkdir(exist_ok=True)
    (target_dir / "workspace" / ".nexus").mkdir(exist_ok=True)

    print("[OK] Project cloned.")


def validate_python_syntax(content: str, file_path: Path) -> bool:
    """
    Validate Python syntax using ast.parse().
    Returns True if valid, raises SyntaxError with details if invalid.
    """
    try:
        ast.parse(content)
        return True
    except SyntaxError as e:
        raise SyntaxError(f"Python syntax error in {file_path}: line {e.lineno}, {e.msg}") from e


def apply_mutation_to_target(mutation: Dict[str, Any], target_dir: Path, index: int) -> None:
    """
    Apply a single mutation to the cloned project.

    Actions:
        - 'overwrite': Replace entire file content with mutation['change']
        - 'append': Add mutation['change'] to end of file with comment header
    """
    target_file = target_dir / mutation["file"]
    action = mutation["action"]
    change = mutation["change"]
    reason = mutation["reason"]

    # Create parent directories if needed
    if not target_file.parent.exists():
        target_file.parent.mkdir(parents=True, exist_ok=True)

    # Handle file creation if it doesn't exist
    if not target_file.exists():
        if action == "append":
            print(f"[WARN] Mutation {index}: Target file {target_file} does not exist. Creating empty file for append.")
            target_file.touch()
        # For overwrite, we'll create the file with new content anyway

    # Read current content (for append mode)
    original_content = ""
    if target_file.exists():
        with open(target_file, 'r', encoding='utf-8') as f:
            original_content = f.read()

    # Apply mutation based on action
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if action == "overwrite":
        # Complete replacement
        new_content = change
        print(f"[INFO] Mutation {index}: OVERWRITE {target_file}")
    else:  # append
        # Append with header comment
        new_content = original_content + "\n\n# MUTATION APPLIED: " + timestamp + "\n"
        new_content += "# Reason: " + reason + "\n"
        new_content += change + "\n"
        print(f"[INFO] Mutation {index}: APPEND to {target_file}")

    # Validate Python syntax BEFORE writing
    if target_file.suffix == ".py":
        try:
            validate_python_syntax(new_content, target_file)
            print(f"[OK] Mutation {index}: Python syntax validated")
        except SyntaxError as e:
            print(f"[ERROR] Mutation {index}: {e}")
            raise

    # Write the mutated content
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"[OK] Mutation {index}: Applied to {target_file}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python clone_and_mutate.py <target_name> <mutation_json_file>")
        print("\nMutation JSON Schema:")
        print('[{"file": "path", "action": "overwrite|append", "change": "content", "reason": "why"}]')
        sys.exit(1)

    target_name = sys.argv[1]
    json_path = Path(sys.argv[2])

    if not json_path.exists():
        print(f"Error: Mutation file not found: {json_path}")
        sys.exit(1)

    # Paths
    # We are in NEXUS_V7_CHRYSALIS/workspace
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
        # 1. Load mutations (plural now!)
        mutations = load_mutations(json_path)
        print(f"[INFO] Loaded {len(mutations)} mutation(s)")
        for i, m in enumerate(mutations, 1):
            print(f"  [{i}] {m['file']} ({m['action']})")

        # 2. Clone project
        clone_project(project_root, target_dir)

        # 3. SECURITY CHECK - Validate all mutations BEFORE applying any
        print("\n[SECURITY] Validating mutations...")
        for i, mutation in enumerate(mutations, 1):
            try:
                validate_mutation_security(mutation, i)
                print(f"  [OK] Mutation {i}: Security check passed")
            except (PermissionError, ValueError) as e:
                print(f"\n[BLOCKED] {e}")
                print("[ABORT] Mutation rejected for security reasons.")
                sys.exit(1)
        print("[SECURITY] All mutations passed security validation.\n")

        # 4. Apply all mutations sequentially
        success_count = 0
        for i, mutation in enumerate(mutations, 1):
            try:
                apply_mutation_to_target(mutation, target_dir, i)
                success_count += 1
            except SyntaxError:
                print(f"[ABORT] Stopping at mutation {i} due to syntax error")
                break
            except Exception as e:
                print(f"[ERROR] Mutation {i} failed: {e}")
                break

        # Summary
        print("\n" + "="*60)
        if success_count == len(mutations):
            print(f"SUCCESS: All {success_count} mutation(s) applied!")
        else:
            print(f"PARTIAL: {success_count}/{len(mutations)} mutation(s) applied")
        print(f"Sandbox created at: {target_dir}")
        print(f"To test: cd {target_dir} && python nexus7.py")
        print("="*60)

    except Exception as e:
        print(f"[ERROR] Failed to clone and mutate: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
