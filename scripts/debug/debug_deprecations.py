
import warnings
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Filter warnings to ensure we see them
warnings.simplefilter('always')

print("Importing models...")
from core.audit.models import AuditLog, HITLRequest

print("Imported models successfully.")

# Trigger model instantiation
try:
    from uuid import uuid4
    log = AuditLog(
        tenant_id=uuid4(),
        user_id=uuid4(),
        action="test",
        resource_type="test"
    )
    print("AuditLog instantiated.")
except Exception as e:
    print(f"Error instantiating AuditLog: {e}")

try:
    req = HITLRequest(
        tenant_id=uuid4(),
        workspace_id="default",
        request_type="ask",
        prompt="hello"
    )
    print("HITLRequest instantiated.")
except Exception as e:
    print(f"Error instantiating HITLRequest: {e}")
