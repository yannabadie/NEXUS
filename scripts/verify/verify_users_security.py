#!/usr/bin/env python3
"""
Security verification script for users.py 

This checks for 5 security issues that need to be fixed:
1. IDOR/Path Traversal in user_id parameter validation
2. Missing input validation on username
3. Missing input validation on email  
4. Insufficient audit logging error handling
5. Missing rate limiting on user endpoints
"""

import sys
import re
from pathlib import Path

def check_security_issues():
    """Check for the 5 security issues in users.py"""
    file_path = Path("core/api/cerebro/routes/users.py")
    content = file_path.read_text()
    lines = content.split('\n')
    
    issues_found = []
    
    # Issue 1: Check for proper user_id validation (IDOR protection)
    if "validate_user_belongs_to_tenant" not in content:
        issues_found.append("❌ ISSUE 1: Missing user_id validation - IDOR vulnerability")
    else:
        issues_found.append("✅ ISSUE 1: user_id validation present")
    
    # Issue 2: Check for username validation
    if len(re.findall(r'username.*validation|sanitize_username|_validate_username', content)) < 2:
        issues_found.append("❌ ISSUE 2: Missing username validation")
    else:
        issues_found.append("✅ ISSUE 2: Username validation present")
    
    # Issue 3: Check for email/domain validation
    if len(re.findall(r'email.*validation|sanitize_email|_validate_email', content)) < 2:
        issues_found.append("❌ ISSUE 3: Missing email validation")
    else:
        issues_found.append("✅ ISSUE 3: Email validation present")
    
    # Issue 4: Check audit logging is properly handled
    audit_log_checks = re.findall(r'audit.*log.*fail|AuditLogger.*except', content, re.IGNORECASE)
    if len(audit_log_checks) < 3:
        issues_found.append("❌ ISSUE 4: Insufficient audit logging error handling")
    else:
        issues_found.append("✅ ISSUE 4: Audit logging properly handled")
    
    # Issue 5: Check for rate limiting
    if "rate_limit" not in content.lower():
        issues_found.append("❌ ISSUE 5: Missing rate limiting")
    else:
        issues_found.append("✅ ISSUE 5: Rate limiting present")
    
    print("=" * 70)
    print("SECURITY VERIFICATION FOR core/api/cerebro/routes/users.py")
    print("=" * 70)
    for issue in issues_found:
        print(issue.encode('ascii', errors='ignore').decode('ascii'))
    print("=" * 70)
    
    return len([i for i in issues_found if i.startswith("❌")])

if __name__ == "__main__":
    bad_count = check_security_issues()
    if bad_count > 0:
        print(f"\n[FAIL] {bad_count} security issues found that need fixing")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All 5 security issues have been fixed!")
        sys.exit(0)
