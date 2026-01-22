import warnings
from datetime import datetime, timezone, timedelta

# Filter always to see all warnings
warnings.simplefilter('always')

print("Testing datetime.now(timezone.utc).replace(tzinfo=None)...")
d = datetime.now(timezone.utc).replace(tzinfo=None)
print(f"Result: {d}")

print("Testing datetime.utcnow()...")
# This should trigger a DeprecationWarning in Python 3.12+
try:
    d2 = datetime.utcnow()
    print(f"Result: {d2}")
except Exception as e:
    print(e)
