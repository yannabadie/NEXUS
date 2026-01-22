
import warnings
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

# Filter warnings to ensure we see them
warnings.simplefilter('always')

print("Importing AuditLogger...")
try:
    from core.audit.audit_logger import AuditLogger
    print("Import successful.")
except Exception as e:
    print(f"Import failed: {e}")

from core.audit.models import AuditLog
print("Creating AuditLog instance...")
try:
    log = AuditLog(tenant_id="123e4567-e89b-12d3-a456-426614174000", user_id="123e4567-e89b-12d3-a456-426614174000", action="test", resource_type="test")
    print("Instance created.")
except Exception as e:
    print(f"Creation failed: {e}")
