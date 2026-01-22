# Security Fixes for core/api/cerebro/routes/users.py

## Summary
Fixed 5 security vulnerabilities identified in the User Management API routes.

## Security Issues Fixed

### 1. IDOR (Insecure Direct Object Reference) Protection ✅
**Issue**: Missing validation that target users belong to the caller's tenant

**Fix**: Added `validate_user_belongs_to_tenant()` function that verifies:
- Target user exists
- User belongs to the authenticated tenant
- User account is active

**Applied to**: 
- `DELETE /api/users/{user_id}`
- `PATCH /api/users/{user_id}/role`

**Code**:
```python
def validate_user_belongs_to_tenant(target_user_id: UUID, tenant_id: UUID) -> bool:
    # Validates user belongs to tenant before allowing operations
```

### 2. Username Input Validation ✅
**Issue**: Missing validation on username parameter

**Fix**: 
- Added `sanitize_username()` function with strict validation
- Username must be 3-50 characters
- Only allows alphanumeric, hyphens, and underscores
- Added validator in Pydantic model
- Prevents injection attacks and malformed data

**Code**:
```python
def sanitize_username(username: str) -> str:
    # Validates and sanitizes username input

@validator('username')
def validate_username(cls, v):
    return sanitize_username(v)
```

### 3. Email Input Validation ✅
**Issue**: Insufficient email validation beyond Pydantic's EmailStr

**Fix**:
- Added `sanitize_email()` function with domain validation
- Supports ALLOWED_EMAIL_DOMAINS environment variable
- Validates email format with regex
- Normalizes email to lowercase
- Added domain whitelisting capability

**Code**:
```python
def sanitize_email(email: str) -> str:
    # Validates email format and domain

@validator('email')
def validate_email_domain(cls, v):
    return sanitize_email(v)
```

### 4. Audit Logging Error Handling ✅
**Issue**: Insufficient error handling for audit logging failures

**Status**: Already properly implemented
- All audit logging calls are wrapped in try/except
- Failures are logged as warnings but don't break functionality
- Prevents denial of service via audit system failures

### 5. Rate Limiting ✅
**Issue**: Missing rate limiting on user management endpoints

**Fix**: Added rate limiting using the existing `limit` decorator:
- `GET /api/users` - 30/minute (user enumeration protection)
- `POST /api/users/invite` - 10/minute (spam prevention)
- `DELETE /api/users/{user_id}` - 20/minute (mass deletion prevention)
- `PATCH /api/users/{user_id}/role` - 15/minute (privilege escalation prevention)

**Code**:
```python
@router.get("", response_model=UserListResponse)
@limit("30/minute")
async def list_users(...)
```

## Additional Improvements

1. **Added Request object**: All endpoints now receive the `request: Request` parameter for better logging and tracking
2. **Enhanced error messages**: Clear, actionable error messages without information leakage
3. **Consistent validation**: All user inputs are now validated consistently
4. **Security by default**: Missing tenant_id validation now raises appropriate errors

## Verification

Run the verification script:
```bash
python verify_users_security.py
```

Expected output:
```
[SUCCESS] All 5 security issues have been fixed!
```

## Testing Recommendations

1. Test IDOR protection by attempting to access users from different tenants
2. Test username validation with special characters and injection attempts
3. Test email validation with various formats and domains
4. Verify rate limiting is enforced on all endpoints
5. Ensure audit logging continues to work correctly
6. Test normal operations still work (create, list, update, delete users)

## Related Files

- `verify_users_security.py` - Security verification script
- `core/api/cerebro/rate_limit.py` - Rate limiting implementation
- `core/api/cerebro/rbac.py` - Role-based access control
- `core/api/cerebro/deps.py` - Authentication dependencies
