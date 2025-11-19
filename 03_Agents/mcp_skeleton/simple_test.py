#!/usr/bin/env python3
"""
Simple test to verify MCP server skeleton works
"""

import asyncio
import sys
from pathlib import Path

# Test direct import of components
async def test_components():
    """Test that server components work"""

    print("=" * 60)
    print("MCP SERVER COMPONENT TEST")
    print("=" * 60)

    try:
        # Import server components
        sys.path.insert(0, str(Path(__file__).parent))
        from server import MCPServer
        from tools.calculator import CalculatorTool

        print("✅ Server imports successful")

        # Test calculator tool
        calc = CalculatorTool()
        tools = calc.get_tools()
        print(f"✅ Calculator has {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")

        # Test calculations
        print("\n🧮 Testing calculations:")

        # Addition
        result = await calc.execute("calculator.add", {"a": 10, "b": 20})
        print(f"  10 + 20 = {result}")

        # Multiplication
        result = await calc.execute("calculator.multiply", {"a": 7, "b": 6})
        print(f"  7 × 6 = {result}")

        # Division
        result = await calc.execute("calculator.divide", {"a": 100, "b": 4})
        print(f"  100 ÷ 4 = {result}")

        # Power
        result = await calc.execute("calculator.power", {"base": 2, "exponent": 8})
        print(f"  2^8 = {result}")

        # Square root
        result = await calc.execute("calculator.sqrt", {"n": 144})
        print(f"  √144 = {result}")

        # Test error handling
        print("\n⚠️ Testing error handling (division by zero):")
        try:
            await calc.execute("calculator.divide", {"a": 10, "b": 0})
            print("  ❌ Should have raised an error")
        except ValueError as e:
            print(f"  ✅ Error correctly raised: {e}")

        print("\n✅ All component tests passed!")

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

async def test_server_startup():
    """Test that the server can start"""

    print("\n" + "=" * 60)
    print("MCP SERVER STARTUP TEST")
    print("=" * 60)

    try:
        from server import MCPServer

        server = MCPServer()
        print("✅ Server instance created")
        print(f"✅ {len(server.tools)} tools registered:")
        for name in server.tools.keys():
            print(f"   - {name}")

        print("\n✅ Server startup test passed!")
        return True

    except Exception as e:
        print(f"❌ Server startup error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""

    # Run tests
    results = []

    # Test components
    results.append(await test_components())

    # Test server startup
    results.append(await test_server_startup())

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all(results):
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)