#!/usr/bin/env python3
"""Test path traversal fix in execution_policy.py"""

from core.security.execution_policy import ExecutionPolicy
from pathlib import Path
import tempfile

def test_path_traversal_fix():
    with tempfile.TemporaryDirectory() as tmpdir:
        policy = ExecutionPolicy(Path(tmpdir))
        
        # Test various path traversal patterns
        test_cases = [
            ('../../foo', True, '2 levels'),
            ('../../../foo', True, '3 levels'),
            ('../../../../foo', True, '4 levels'),
            ('../../../etc/passwd', True, 'etc/passwd with 3 levels'),
            ('cat file', False, 'normal command'),
        ]
        
        all_passed = True
        print('Testing path traversal detection:')
        for pattern, should_block, desc in test_cases:
            cmd = f'ls {pattern}' if pattern != 'cat file' else pattern
            is_valid, error = policy.validate_command(cmd)
            blocked = not is_valid and 'traversal' in error.lower()
            
            status = '✓' if blocked == should_block else '✗'
            print(f'  [{status}] {desc}: {pattern}')
            if blocked != should_block:
                print(f'        Expected: block={should_block}, Got: block={blocked}')
                all_passed = False
        
        print(f'\nOverall Result: {"PASS" if all_passed else "FAIL"}')
        return all_passed

if __name__ == '__main__':
    import sys
    success = test_path_traversal_fix()
    sys.exit(0 if success else 1)
