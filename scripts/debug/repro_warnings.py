import warnings
import sys
from datetime import datetime, timezone

# Filter to show all warnings
warnings.simplefilter('always')

try:
    print("Importing AuditLog...")
    from core.audit.models import AuditLog
    print("AuditLog imported.")
    
    print("Instantiating AuditLog...")
    log = AuditLog(
        tenant_id="123e4567-e89b-12d3-a456-426614174000",
        user_id="123e4567-e89b-12d3-a456-426614174001",
        action="test",
        resource_type="test",
        status="success"
    )
    print("AuditLog instantiated.")

    print("Importing HITLRequest...")
    from core.audit.models import HITLRequest
    print("HITLRequest imported.")
    
except Exception as e:
    print(f"Error: {e}")
