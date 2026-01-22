#!/usr/bin/env python3
"""
Verification script for the security fix in core/security/execution_policy.py

Security Issue Fixed: CWE-22 Path Traversal with Multiple Parent Directory Levels

Previously, the regex pattern only matched EXACTLY 3 levels of parent directory 
access (../../../), allowing attackers to bypass the check by using 4+ levels.

The fix changes the pattern from:
  r"\.\.(/|\\)\.\.(/|\\)\.\." (matches exactly 3 levels)
To:
  r"\.\.(/|\\)\.\." (matches 2 or more levels)
"""

import tempfile
from pathlib import Path
from core.security.execution_policy import ExecutionPolicy

def verify_path_traversal_fix():
    """Verify that path traversal with multiple parent directory levels is blocked."""
    print("=" * 70)
    print("VERIFYING PATH TRAVERSAL FIX")
    print("=" * 70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        policy = ExecutionPolicy(Path(tmpdir))
        
        # Test various levels of path traversal
        test_cases = [
            ("../../foo", "2 levels"),
            ("../../../foo", "3 levels"),
            ("../../../../foo", "4 levels"),
            ("../../../../../foo", "5 levels"),
        ]
        
        all_passed = True
        for path, description in test_cases:
            command = f"find . -name {path}"
            is_valid, error = policy.validate_command(command)
            
            if not is_valid and "traversal" in error.lower():
                print(f"[PASS] {description}: {path}")
            else:
                print(f"[FAIL] {description}: {path} - Not blocked by traversal pattern")
                all_passed = False
        
        print("\n" + "=" * 70)
        if all_passed:
            print("[SUCCESS] All path traversal levels blocked correctly!")
            print("=" * 70)
            return True
        else:
            print("[FAILURE] Some path traversal cases not blocked!")
            print("=" * 70)
            return False

if __name__ == "__main__":
    import sys
    success = verify_path_traversal_fix()
    sys.exit(0 if success else 1)
