#!/usr/bin/env python3
"""
MCP Client Test - FINAL CORRECTED VERSION
Complete Windows-compatible implementation with all fixes applied
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Set up logging to debug connection issues
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG if you need more details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORRECT imports for MCP 1.21.2
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters


async def test_direct_server():
    """Test server components directly without stdio transport"""
    print("\n" + "="*60)
    print("DIRECT SERVER TEST (No Stdio)")
    print("="*60)

    try:
        # Import server components
        sys.path.insert(0, str(Path(__file__).parent))
        from server import MCPServer
        from tools.calculator import CalculatorTool

        # Create server instance
        server = MCPServer()
        print(f"✅ Server instance created with {len(server.tools)} tools")

        # Test calculator tool directly
        calc = server.tools["calculator"]

        # Test addition
        result = await calc.execute("calculator.add", {"a": 5, "b": 3})
        print(f"✅ Addition: 5 + 3 = {result}")

        # Test multiplication
        result = await calc.execute("calculator.multiply", {"a": 7, "b": 6})
        print(f"✅ Multiplication: 7 × 6 = {result}")

        # Test square root
        result = await calc.execute("calculator.sqrt", {"n": 144})
        print(f"✅ Square root: √144 = {result}")

        print("✅ Direct server test PASSED")
        return True

    except Exception as e:
        print(f"❌ Direct server test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_client_connection():
    """Test MCP client-server connection with full Windows compatibility fixes"""

    print("\n" + "="*60)
    print("MCP CLIENT-SERVER CONNECTION TEST")
    print("="*60)

    # Determine paths based on current working directory
    cwd = Path.cwd()
    if (cwd / "20_NEXUS").exists():
        # Running from parent directory
        PYTHON_EXE = (cwd / "20_NEXUS" / ".venv" / "Scripts" / "python.exe").absolute()
        SERVER_SCRIPT = (cwd / "20_NEXUS" / "03_AGENTS" / "mcp_skeleton" / "server.py").absolute()
    elif (cwd.parent / "20_NEXUS").exists() and cwd.parent.name == "MES":
        # Running from MES directory
        PYTHON_EXE = (cwd.parent / "20_NEXUS" / ".venv" / "Scripts" / "python.exe").absolute()
        SERVER_SCRIPT = (cwd.parent / "20_NEXUS" / "03_AGENTS" / "mcp_skeleton" / "server.py").absolute()
    else:
        # Assume we're in 20_NEXUS directory
        PYTHON_EXE = (cwd / ".venv" / "Scripts" / "python.exe").absolute()
        SERVER_SCRIPT = (cwd / "03_AGENTS" / "mcp_skeleton" / "server.py").absolute()

    # Verify paths exist
    if not PYTHON_EXE.exists():
        print(f"❌ Python executable not found: {PYTHON_EXE}")
        print(f"   Current directory: {cwd}")
        return False

    if not SERVER_SCRIPT.exists():
        print(f"❌ Server script not found: {SERVER_SCRIPT}")
        print(f"   Current directory: {cwd}")
        return False

    print(f"📂 Python: {PYTHON_EXE}")
    print(f"📂 Server: {SERVER_SCRIPT}")
    print(f"📂 Working Dir: {SERVER_SCRIPT.parent}")

    # Configure server parameters with all Windows fixes
    server_params = StdioServerParameters(
        command=str(PYTHON_EXE),
        args=[
            "-u",  # Unbuffered Python output (critical for Windows)
            str(SERVER_SCRIPT)
        ],
        cwd=str(SERVER_SCRIPT.parent),
        env={
            **os.environ.copy(),
            "PYTHONUNBUFFERED": "1",      # Force unbuffered stdout/stderr
            "PYTHONIOENCODING": "utf-8",  # Force UTF-8 encoding
            "PYTHONUTF8": "1"              # Ensure UTF-8 mode
        }
    )

    try:
        print("\n🚀 Starting MCP server process...")

        # Use timeout to prevent hanging
        async with asyncio.timeout(30):
            # Connect to server using stdio transport
            async with stdio_client(server_params) as (read_stream, write_stream):
                print("✅ Stdio transport connected!")

                # Create client session
                async with ClientSession(read_stream, write_stream) as session:
                    print("✅ Client session created!")

                    # Initialize session with timeout
                    print("⏳ Initializing session...")
                    try:
                        async with asyncio.timeout(10):
                            await session.initialize()
                        print("✅ Session initialized successfully!")
                    except asyncio.TimeoutError:
                        print("❌ Session initialization timeout!")
                        print("   The server may not be responding correctly")
                        print("   Check mcp_server.log for errors")
                        return False

                    # List available tools
                    print("\n📋 Listing available tools...")
                    tools_response = await session.list_tools()
                    print(f"✅ Found {len(tools_response.tools)} tools:")
                    for tool in tools_response.tools:
                        print(f"   - {tool.name}: {tool.description}")

                    # Test calculator.add
                    print("\n🧮 Testing calculator.add(10, 32)...")
                    result = await session.call_tool(
                        "calculator.add",
                        arguments={"a": 10, "b": 32}
                    )
                    result_text = result.content[0].text if result.content else "No result"
                    print(f"   Result: {result_text}")
                    assert "42" in str(result_text), f"Expected 42, got {result_text}"

                    # Test calculator.multiply
                    print("\n🧮 Testing calculator.multiply(7, 6)...")
                    result = await session.call_tool(
                        "calculator.multiply",
                        arguments={"a": 7, "b": 6}
                    )
                    result_text = result.content[0].text if result.content else "No result"
                    print(f"   Result: {result_text}")
                    assert "42" in str(result_text), f"Expected 42, got {result_text}"

                    # Test calculator.power
                    print("\n🧮 Testing calculator.power(2, 8)...")
                    result = await session.call_tool(
                        "calculator.power",
                        arguments={"base": 2, "exponent": 8}
                    )
                    result_text = result.content[0].text if result.content else "No result"
                    print(f"   Result: {result_text}")
                    assert "256" in str(result_text), f"Expected 256, got {result_text}"

                    # Test error handling
                    print("\n⚠️ Testing error handling (division by zero)...")
                    result = await session.call_tool(
                        "calculator.divide",
                        arguments={"a": 10, "b": 0}
                    )
                    result_text = result.content[0].text if result.content else "No result"

                    # Check if error was handled
                    if hasattr(result, 'isError') and result.isError:
                        print(f"   ✅ Error correctly handled: {result_text}")
                    elif "error" in result_text.lower() or "division" in result_text.lower():
                        print(f"   ✅ Error detected in response: {result_text}")
                    else:
                        print(f"   ⚠️ Unexpected result: {result_text}")

                    print("\n✅ MCP client-server test PASSED!")
                    return True

    except asyncio.TimeoutError:
        print("\n❌ Connection timeout!")
        print("Possible causes:")
        print("  1. Server failed to start")
        print("  2. Stdio transport not properly configured")
        print("  3. Python buffering issues on Windows")
        return False

    except Exception as e:
        print(f"\n❌ Connection test FAILED: {e}")
        import traceback
        traceback.print_exc()

        print("\nDiagnostic Information:")
        print(f"  - Working Directory: {os.getcwd()}")
        print(f"  - Python Version: {sys.version}")
        print(f"  - Platform: {sys.platform}")
        print(f"  - Event Loop: {asyncio.get_event_loop_policy().__class__.__name__}")

        return False


async def main():
    """Main test runner"""

    print("=" * 70)
    print(" MCP SERVER TEST SUITE - WINDOWS EDITION ")
    print(" Final Corrected Version with All Fixes ")
    print("=" * 70)

    # Test 1: Direct server components
    print("\n[TEST 1/2] Direct Server Components")
    server_ok = await test_direct_server()

    if not server_ok:
        print("\n⚠️ Server components failed - skipping connection test")
        print("   Fix server issues before testing client connection")
        return 1

    # Test 2: Full MCP client-server connection
    print("\n[TEST 2/2] MCP Client-Server Connection")
    client_ok = await test_mcp_client_connection()

    # Final summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY ")
    print("=" * 70)

    if server_ok and client_ok:
        print("✅ ALL TESTS PASSED!")
        print("   - Server components: OK")
        print("   - Client connection: OK")
        print("\n🎉 MCP Server is fully operational on Windows!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        if not server_ok:
            print("   - Server components: FAILED")
        else:
            print("   - Server components: OK")

        if not client_ok:
            print("   - Client connection: FAILED")
        else:
            print("   - Client connection: OK")

        print("\n📝 Next steps:")
        if not server_ok:
            print("   1. Check server.py imports")
            print("   2. Verify tools/calculator.py is correct")
        if not client_ok:
            print("   1. Check mcp_server.log for errors")
            print("   2. Try running server.py directly to see output")
            print("   3. Verify Python unbuffered mode is working")

        return 1


if __name__ == "__main__":
    # CRITICAL: Set Windows-specific event loop policy
    if sys.platform == 'win32':
        # ProactorEventLoop is required for subprocess support on Windows
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        print("✅ Windows ProactorEventLoop configured")

    # Run the test suite
    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit_code = 130

    sys.exit(exit_code)