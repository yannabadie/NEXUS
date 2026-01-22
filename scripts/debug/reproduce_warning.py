
import warnings
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel
from pydantic import ConfigDict

warnings.simplefilter("always")

print("Defining Model...")
class TestModel(SQLModel, table=True):
    model_config = ConfigDict(from_attributes=True)
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

print("Instantiating Model...")
t = TestModel()
print("Done.")
