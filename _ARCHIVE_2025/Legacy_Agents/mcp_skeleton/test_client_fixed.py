#!/usr/bin/env python3
"""
MCP Client Test - FIXED VERSION
Correct imports and implementation for MCP 1.21.2
"""

import asyncio
import sys
from pathlib import Path

# Use the correct imports for MCP 1.21.2
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def test_mcp_server():
    """Test the MCP server using proper client API"""

    # Define server parameters
    server_params = StdioServerParameters(
        command="python",
        args=[str(Path(__file__).parent / "server.py")],
        cwd=str(Path(__file__).parent)
    )

    print("=" * 60)
    print("MCP CLIENT TEST - FIXED VERSION")
    print("=" * 60)

    try:
        # Create client connection using context manager
        async with stdio_client(server_params) as (read_stream, write_stream):
            # Create client session
            async with ClientSession(read_stream, write_stream) as session:
                print("✅ Connected to MCP Server")

                # Initialize the connection
                await session.initialize()
                print("✅ Session initialized")

                # List available tools
                tools_response = await session.list_tools()
                print(f"\n📋 Available Tools: {len(tools_response.tools)}")
                for tool in tools_response.tools:
                    print(f"   - {tool.name}: {tool.description}")

                # Test calculator.add
                print("\n🧮 Testing calculator.add(10, 32)...")
                result = await session.call_tool(
                    "calculator.add",
                    arguments={"a": 10, "b": 32}
                )
                print(f"   Result: {result.content[0].text}")

                # Test calculator.multiply
                print("\n🧮 Testing calculator.multiply(7, 6)...")
                result = await session.call_tool(
                    "calculator.multiply",
                    arguments={"a": 7, "b": 6}
                )
                print(f"   Result: {result.content[0].text}")

                # Test calculator.power
                print("\n🧮 Testing calculator.power(2, 8)...")
                result = await session.call_tool(
                    "calculator.power",
                    arguments={"base": 2, "exponent": 8}
                )
                print(f"   Result: {result.content[0].text}")

                # Test calculator.sqrt
                print("\n🧮 Testing calculator.sqrt(144)...")
                result = await session.call_tool(
                    "calculator.sqrt",
                    arguments={"n": 144}
                )
                print(f"   Result: {result.content[0].text}")

                # Test error handling
                print("\n⚠️ Testing error handling (division by zero)...")
                try:
                    result = await session.call_tool(
                        "calculator.divide",
                        arguments={"a": 10, "b": 0}
                    )
                    if result.isError:
                        print(f"   ✅ Error correctly handled: {result.content[0].text}")
                    else:
                        print(f"   ❌ Should have returned an error")
                except Exception as e:
                    print(f"   ✅ Exception caught: {e}")

                print("\n✅ All tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("TEST SUCCESSFUL")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(test_mcp_server())
    sys.exit(exit_code)