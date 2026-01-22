import inspect
from core.audit.models import AuditLog, HITLRequest
from datetime import datetime, timezone

def check_field_defaults(model):
    print(f"Checking {model.__name__}...")
    for name, field in model.model_fields.items():
        if field.default_factory:
            try:
                # Get source code of the lambda/function
                source = inspect.getsource(field.default_factory)
                print(f"  Field {name} default_factory source: {source.strip()}")
                if "utcnow" in source:
                    print(f"  !! Found utcnow in {name}")
                if "utcfromtimestamp" in source:
                    print(f"  !! Found utcfromtimestamp in {name}")
            except Exception as e:
                print(f"  Field {name} default_factory: <could not get source> ({e})")

try:
    check_field_defaults(AuditLog)
    check_field_defaults(HITLRequest)
except Exception as e:
    print(f"Error: {e}")
