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
# MUTATION AUDIT SYSTEM - Flag suspicious mutations for post-creation validation
# ============================================================================
# Philosophy: Allow ALL mutations (Darwinian freedom), but AUDIT suspicious ones.
# The real protection comes from drastic benchmarks + Red Team AFTER creation.
# Parent is always safe (we clone first). Child can mutate freely.

# Sensitive files - mutations here are FLAGGED (not blocked)
SENSITIVE_FILES = [
    "KERNEL.py",
    "KERNEL_HASH.txt",
    "core/governance/red_team/validator.py",
    "core/governance/red_team/alignment_tests.py",
]

# Patterns that suggest security bypass attempts - FLAGGED for Red Team review
SUSPICIOUS_CONFIG_PATTERNS = [
    (r"VALIDATION_TIER.*=.*[01]", "LOW_VALIDATION_TIER"),
    (r"SKIP.*RED.*TEAM.*=.*True", "SKIP_RED_TEAM"),
    (r"RED_TEAM.*ENABLED.*=.*False", "DISABLED_RED_TEAM"),
    (r"ALIGNMENT.*CHECK.*=.*False", "DISABLED_ALIGNMENT"),
    (r"KERNEL.*VERIFY.*=.*False", "DISABLED_KERNEL_VERIFY"),
]

# Size thresholds - mutations below these sizes are FLAGGED as potential lobotomization
SIZE_THRESHOLDS = {
    "prompts/system_gemini_v7.md": 5000,   # ~500 lines expected
    "prompts/system_claude_v7.md": 5000,   # ~500 lines expected
}

# Audit log structure
AUDIT_FLAGS = {
    "KERNEL_MUTATION": "Mutation targets KERNEL - requires enhanced Red Team validation",
    "LOBOTOMIZATION_RISK": "Critical file size drastically reduced - check for content destruction",
    "SECURITY_BYPASS": "Pattern suggests attempt to bypass security controls",
    "RED_TEAM_MUTATION": "Mutation targets Red Team itself - highest scrutiny required",
}


def audit_mutation(mutation: Dict[str, Any], index: int) -> List[Dict[str, Any]]:
    """
    Audit a mutation for suspicious patterns. Returns list of flags (not blocking).

    Philosophy: Allow ALL mutations, but flag suspicious ones for enhanced
    Red Team validation after child creation.

    Returns:
        List of audit flags, each with: flag_type, severity, message
    """
    flags = []
    file_path = mutation["file"]
    change = mutation["change"]
    action = mutation.get("action", "overwrite")

    # Audit 1: Sensitive file mutations (KERNEL, Red Team)
    for sensitive in SENSITIVE_FILES:
        if file_path == sensitive or file_path.endswith(sensitive):
            flag_type = "RED_TEAM_MUTATION" if "red_team" in sensitive.lower() else "KERNEL_MUTATION"
            flags.append({
                "mutation_index": index,
                "flag_type": flag_type,
                "severity": "HIGH",
                "file": file_path,
                "message": AUDIT_FLAGS[flag_type]
            })

    # Audit 2: Suspicious patterns in config files
    if "config" in file_path.lower():
        for pattern, flag_name in SUSPICIOUS_CONFIG_PATTERNS:
            if re.search(pattern, change, re.IGNORECASE):
                flags.append({
                    "mutation_index": index,
                    "flag_type": "SECURITY_BYPASS",
                    "severity": "CRITICAL",
                    "file": file_path,
                    "pattern_detected": flag_name,
                    "message": AUDIT_FLAGS["SECURITY_BYPASS"]
                })

    # Audit 3: Size threshold violations (potential lobotomization)
    if action == "overwrite":
        for critical_file, threshold in SIZE_THRESHOLDS.items():
            if file_path == critical_file or file_path.endswith(critical_file):
                if len(change) < threshold:
                    flags.append({
                        "mutation_index": index,
                        "flag_type": "LOBOTOMIZATION_RISK",
                        "severity": "CRITICAL",
                        "file": file_path,
                        "new_size": len(change),
                        "threshold": threshold,
                        "message": AUDIT_FLAGS["LOBOTOMIZATION_RISK"]
                    })

    return flags


def save_audit_report(flags: List[Dict[str, Any]], target_dir: Path, mutations: List[Dict]) -> None:
    """Save audit report to the child's directory for Red Team review."""
    if not flags:
        return

    report = {
        "audit_timestamp": datetime.now().isoformat(),
        "total_mutations": len(mutations),
        "flagged_mutations": len(set(f["mutation_index"] for f in flags)),
        "flags": flags,
        "requires_enhanced_validation": any(f["severity"] == "CRITICAL" for f in flags),
        "validation_instructions": [
            "Run full benchmark suite on this child",
            "Red Team must review all CRITICAL flags before approval",
            "Check KERNEL hash integrity if KERNEL_MUTATION flagged",
            "Verify prompt completeness if LOBOTOMIZATION_RISK flagged"
        ]
    }

    audit_file = target_dir / "MUTATION_AUDIT.json"
    with open(audit_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print(f"[AUDIT] Report saved to {audit_file}")


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

    # Copy foundation files from 20_NEXUS/ root (parent of source)
    # Source: 20_NEXUS/NEXUS_V7_CHRYSALIS -> Root: 20_NEXUS/
    nexus_root = source_dir.parent
    foundation_files = [
        # Core immutable files
        "KERNEL.py",
        "KERNEL_HASH.txt",
        # Mission & governance
        "MISSION.md",
        "INVARIANTS.md",
        "EVOLUTION_PROTOCOL.md",
        # Agent instructions
        "CLAUDE.md",
        "GEMINI.md",
        # Lineage tracking
        "LINEAGE.json",
        # Project meta
        "README.md",
        "LICENSE",
        "requirements.txt",
    ]

    print("[INFO] Copying foundation files...")
    for filename in foundation_files:
        src_file = nexus_root / filename
        if src_file.exists():
            shutil.copy2(src_file, target_dir / filename)
            print(f"  [OK] {filename}")
        else:
            print(f"  [WARN] {filename} not found at {src_file}")

    print("[OK] Project cloned with foundation files.")


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


def validate_path_containment(target_dir: Path, file_path: str) -> Path:
    """
    SECURITY: Ensure the resolved path stays within target_dir sandbox.

    Prevents path traversal attacks like:
    - "../../NEXUS_V7_CHRYSALIS/KERNEL.py"
    - "/etc/passwd" (absolute paths)
    - "..\\..\\kernel.py" (Windows style)

    Args:
        target_dir: The sandbox directory (GENERATION_ACTIVE/<child>)
        file_path: The requested file path from mutation JSON

    Returns:
        Resolved Path if valid

    Raises:
        ValueError: If path escapes the sandbox
    """
    # Resolve the full path
    full_path = (target_dir / file_path).resolve()
    target_resolved = target_dir.resolve()

    # Ensure it's within target_dir
    try:
        full_path.relative_to(target_resolved)
    except ValueError:
        raise ValueError(
            f"PATH TRAVERSAL BLOCKED: '{file_path}' resolves to '{full_path}' "
            f"which is outside sandbox '{target_resolved}'"
        )

    return full_path


def apply_mutation_to_target(mutation: Dict[str, Any], target_dir: Path, index: int) -> None:
    """
    Apply a single mutation to the cloned project.

    Actions:
        - 'overwrite': Replace entire file content with mutation['change']
        - 'append': Add mutation['change'] to end of file with comment header
    """
    # SECURITY: Validate path containment BEFORE any file operations
    target_file = validate_path_containment(target_dir, mutation["file"])

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

        # 3. AUDIT - Flag suspicious mutations (but don't block - Darwinian freedom)
        print("\n[AUDIT] Scanning mutations for suspicious patterns...")
        all_flags = []
        for i, mutation in enumerate(mutations, 1):
            flags = audit_mutation(mutation, i)
            all_flags.extend(flags)
            if flags:
                for flag in flags:
                    severity_icon = "[!!]" if flag["severity"] == "CRITICAL" else "[!]"
                    print(f"  {severity_icon} Mutation {i}: {flag['flag_type']} ({flag['severity']})")
                    print(f"      => {flag['message']}")
            else:
                print(f"  [OK] Mutation {i}: No flags")

        # Save audit report if any flags
        if all_flags:
            save_audit_report(all_flags, target_dir, mutations)
            critical_count = sum(1 for f in all_flags if f["severity"] == "CRITICAL")
            print(f"\n[AUDIT] {len(all_flags)} flag(s) raised ({critical_count} CRITICAL)")
            print("[AUDIT] Child will require enhanced Red Team validation.")
        else:
            print("[AUDIT] All mutations clean - standard validation sufficient.\n")

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
