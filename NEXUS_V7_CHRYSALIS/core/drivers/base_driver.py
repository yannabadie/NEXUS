"""
Abstract Driver Base Class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseDriver(ABC):
    @abstractmethod
    def invoke(self, context: str) -> Dict[str, Any]:
        """Send context to the model and return a structured response."""
        pass
