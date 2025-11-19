"""
Calculator Tool for MCP Server
Sample tool implementation demonstrating the tool interface
"""

import logging
from typing import Any, Dict, List
from mcp.types import Tool

logger = logging.getLogger(__name__)


class CalculatorTool:
    """Simple calculator tool with basic arithmetic operations"""

    def __init__(self):
        self.name = "calculator"
        self.operations = {
            "add": self._add,
            "subtract": self._subtract,
            "multiply": self._multiply,
            "divide": self._divide,
            "power": self._power,
            "sqrt": self._sqrt
        }

    def get_tools(self) -> List[Tool]:
        """Return list of available calculator tools"""
        return [
            Tool(
                name="calculator.add",
                description="Add two numbers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="calculator.subtract",
                description="Subtract second number from first",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="calculator.multiply",
                description="Multiply two numbers",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="calculator.divide",
                description="Divide first number by second",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "a": {"type": "number", "description": "Dividend"},
                        "b": {"type": "number", "description": "Divisor (non-zero)"}
                    },
                    "required": ["a", "b"]
                }
            ),
            Tool(
                name="calculator.power",
                description="Raise first number to the power of second",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "base": {"type": "number", "description": "Base number"},
                        "exponent": {"type": "number", "description": "Exponent"}
                    },
                    "required": ["base", "exponent"]
                }
            ),
            Tool(
                name="calculator.sqrt",
                description="Calculate square root of a number",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "n": {"type": "number", "description": "Number (non-negative)"}
                    },
                    "required": ["n"]
                }
            )
        ]

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute the requested calculator operation"""
        # Extract operation from tool name (e.g., "calculator.add" -> "add")
        operation = tool_name.split(".")[-1]

        if operation not in self.operations:
            raise ValueError(f"Unknown operation: {operation}")

        logger.info(f"Executing {operation} with arguments: {arguments}")

        try:
            result = self.operations[operation](arguments)
            logger.info(f"Operation {operation} result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in {operation}: {e}")
            raise

    def _add(self, args: Dict[str, Any]) -> float:
        """Add two numbers"""
        return args["a"] + args["b"]

    def _subtract(self, args: Dict[str, Any]) -> float:
        """Subtract b from a"""
        return args["a"] - args["b"]

    def _multiply(self, args: Dict[str, Any]) -> float:
        """Multiply two numbers"""
        return args["a"] * args["b"]

    def _divide(self, args: Dict[str, Any]) -> float:
        """Divide a by b"""
        if args["b"] == 0:
            raise ValueError("Division by zero")
        return args["a"] / args["b"]

    def _power(self, args: Dict[str, Any]) -> float:
        """Raise base to exponent power"""
        return args["base"] ** args["exponent"]

    def _sqrt(self, args: Dict[str, Any]) -> float:
        """Calculate square root"""
        import math
        if args["n"] < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(args["n"])
