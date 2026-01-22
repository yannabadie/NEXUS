
import warnings
from enum import Enum

warnings.simplefilter("always")

print("Defining Enum...")
class AuditAction(str, Enum):
    AUTH_LOGIN = "auth:login"

print("Using Enum...")
print(AuditAction.AUTH_LOGIN)
