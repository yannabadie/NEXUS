"""
Test file for NCM Phase 1 - mixed story types.

This file contains intentional issues for testing all SimpleExecutor handlers:
- Dead imports (for testing dead import removal)
- Functions without docstrings (for testing docstring addition)
- Parameters without type hints (for testing type hint addition)
- Deprecated patterns (for testing deprecation fixes)
"""

from pathlib import Path
from datetime import datetime
import json


def function_without_docstring(param1, param2):
    """TODO: Add function description."""
    return param1 + param2


def another_function_no_docs(x: int, y, z):
    """TODO: Add function description."""
    return x * y + z


class ClassWithoutDocstring:
    """TODO: Add class description."""
    def method_no_docs(self, value):
        return value * 2


def function_no_type_hints(name: str, age: int, active):
    """TODO: Add function description."""
    message = f"{name} is {age} years old"
    if active:
        return message
    return None


def function_with_deprecated_datetime():
    """TODO: Add function description."""
    # Uses deprecated datetime.utcnow()
    current = datetime.utcnow()
    return current


def helper_function(data, index):
    """TODO: Add function description."""
    if index < len(data):
        return data[index]
    return None


class AnotherClass:
    """TODO: Add class description."""
    def process(self, items, count):
        results = []
        for i in range(count):
            if i < len(items):
                results.append(items[i])
        return results


def main():
    """Main function with proper docstring."""
    print("NCM Phase 1 Test Target")

    # Test functions
    result1 = function_without_docstring(1, 2)
    result2 = another_function_no_docs(3, 4, 5)
    result3 = function_no_type_hints("Test", 25, True)
    result4 = function_with_deprecated_datetime()

    print(f"Results: {result1}, {result2}, {result3}, {result4}")

    # Test classes
    obj = ClassWithoutDocstring()
    val = obj.method_no_docs(10)

    obj2 = AnotherClass()
    items = obj2.process([1, 2, 3], 2)

    return True


if __name__ == "__main__":
    main()
