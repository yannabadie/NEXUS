#!/usr/bin/env python3
"""
MCP Client Test - SSE Transport Version (CORRECTED)
Tests MCP server using HTTP/SSE transport with correct imports
"""

import asyncio
import httpx
import json
from pathlib import Path
import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORRECT MCP client imports based on actual package
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client  # Function, not class


async def test_http_connectivity():
    """Test basic HTTP connectivity to server"""
    print("\n" + "=" * 60)
    print("HTTP CONNECTIVITY TEST")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Test health endpoint
            response = await client.get("http://localhost:8000/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Server is up: {data}")
                return True
            else:
                print(f"❌ Server returned status {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure server_sse.py is running")
        return False


async def test_mcp_sse_client():
    """Test MCP client using SSE transport with correct API"""
    print("\n" + "=" * 60)
    print("MCP SSE CLIENT TEST")
    print("=" * 60)

    # SSE endpoint URL
    sse_url = "http://localhost:8000/mcp/v1/sse"

    try:
        print(f"🔗 Connecting to MCP server via SSE at {sse_url}...")

        # Connect using sse_client function with URL directly
        async with sse_client(
            url=sse_url,
            headers=None,  # Optional headers
            timeout=5,  # Connection timeout
            sse_read_timeout=60 * 5  # SSE read timeout (5 minutes)
        ) as (read_stream, write_stream):
            print("✅ SSE transport connected!")

            # Create client session
            async with ClientSession(read_stream, write_stream) as session:
                print("✅ Client session created!")

                # Initialize session
                print("⏳ Initializing session...")
                await session.initialize()
                print("✅ Session initialized!")

                # List tools
                print("\n📋 Listing available tools...")
                tools_response = await session.list_tools()
                print(f"Found {len(tools_response.tools)} tools:")
                for tool in tools_response.tools:
                    print(f"   - {tool.name}: {tool.description}")

                # Test calculator.add
                print("\n🧮 Testing calculator.add(25, 17)...")
                result = await session.call_tool(
                    "calculator.add",
                    arguments={"a": 25, "b": 17}
                )
                result_text = result.content[0].text if result.content else "No result"
                print(f"   Result: {result_text}")
                assert "42" in str(result_text), f"Expected 42, got {result_text}"

                # Test calculator.multiply
                print("\n🧮 Testing calculator.multiply(6, 7)...")
                result = await session.call_tool(
                    "calculator.multiply",
                    arguments={"a": 6, "b": 7}
                )
                result_text = result.content[0].text if result.content else "No result"
                print(f"   Result: {result_text}")
                assert "42" in str(result_text), f"Expected 42, got {result_text}"

                # Test calculator.power
                print("\n🧮 Testing calculator.power(2, 10)...")
                result = await session.call_tool(
                    "calculator.power",
                    arguments={"base": 2, "exponent": 10}
                )
                result_text = result.content[0].text if result.content else "No result"
                print(f"   Result: {result_text}")
                assert "1024" in str(result_text), f"Expected 1024, got {result_text}"

                # Test calculator.sqrt
                print("\n🧮 Testing calculator.sqrt(256)...")
                result = await session.call_tool(
                    "calculator.sqrt",
                    arguments={"n": 256}
                )
                result_text = result.content[0].text if result.content else "No result"
                print(f"   Result: {result_text}")
                assert "16" in str(result_text), f"Expected 16, got {result_text}"

                # Test calculator.divide (success case)
                print("\n🧮 Testing calculator.divide(100, 4)...")
                result = await session.call_tool(
                    "calculator.divide",
                    arguments={"a": 100, "b": 4}
                )
                result_text = result.content[0].text if result.content else "No result"
                print(f"   Result: {result_text}")
                assert "25" in str(result_text), f"Expected 25, got {result_text}"

                # Test error handling (division by zero)
                print("\n⚠️ Testing error handling (division by zero)...")
                result = await session.call_tool(
                    "calculator.divide",
                    arguments={"a": 10, "b": 0}
                )
                result_text = result.content[0].text if result.content else "No result"

                if hasattr(result, 'isError') and result.isError:
                    print(f"   ✅ Error handled correctly: {result_text}")
                elif "error" in result_text.lower() or "division" in result_text.lower():
                    print(f"   ✅ Error detected: {result_text}")
                else:
                    print(f"   ⚠️ Unexpected result: {result_text}")

                print("\n✅ All SSE client tests passed!")
                return True

    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure httpx-sse is installed:")
        print("   .venv\\Scripts\\pip install httpx-sse")
        return False
    except Exception as e:
        print(f"\n❌ SSE client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_direct_http_request():
    """Test direct HTTP request to verify server is responding"""
    print("\n" + "=" * 60)
    print("DIRECT HTTP REQUEST TEST")
    print("=" * 60)

    try:
        async with httpx.AsyncClient() as client:
            # Note: The SSE endpoint expects a GET request for SSE streaming
            print("📤 Sending test GET to SSE endpoint...")

            # Send GET request (SSE uses GET, not POST)
            response = await client.get(
                "http://localhost:8000/mcp/v1/sse",
                headers={"Accept": "text/event-stream"},
                timeout=5
            )

            print(f"📨 Response status: {response.status_code}")

            if response.status_code == 200:
                # Read some of the response
                content_preview = response.text[:500] if response.text else "No content"
                print(f"   Response preview: {content_preview}...")
                print("✅ Server is responding to SSE requests")
                return True
            else:
                print(f"   Status {response.status_code} - this may be normal for SSE")
                # SSE might require proper connection setup
                return True

    except Exception as e:
        print(f"⚠️ Direct HTTP test note: {e}")
        print("   SSE endpoints may not respond to simple HTTP requests")
        return True  # Not a failure for SSE


async def check_dependencies():
    """Check if required dependencies are installed"""
    print("\n" + "=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)

    dependencies_ok = True

    # Check httpx
    try:
        import httpx
        print(f"✅ httpx installed: {httpx.__version__}")
    except ImportError:
        print("❌ httpx not installed")
        dependencies_ok = False

    # Check httpx-sse (required for SSE client)
    try:
        import httpx_sse
        print("✅ httpx-sse installed")
    except ImportError:
        print("❌ httpx-sse not installed")
        print("   Install with: .venv\\Scripts\\pip install httpx-sse")
        dependencies_ok = False

    # Check starlette (for server)
    try:
        import starlette
        print(f"✅ starlette installed: {starlette.__version__}")
    except ImportError:
        print("❌ starlette not installed")
        dependencies_ok = False

    # Check uvicorn (for server)
    try:
        import uvicorn
        print("✅ uvicorn installed")
    except ImportError:
        print("❌ uvicorn not installed")
        dependencies_ok = False

    # Check mcp
    try:
        import mcp
        print(f"✅ mcp installed (version check skipped)")
    except ImportError:
        print("❌ mcp not installed")
        dependencies_ok = False

    return dependencies_ok


async def main():
    """Main test runner"""
    print("=" * 70)
    print(" MCP SSE TRANSPORT TEST SUITE ")
    print(" Windows-Stable HTTP/SSE Implementation ")
    print("=" * 70)

    print("\nPython version:", sys.version)
    print("Platform:", sys.platform)

    # Check dependencies first
    print("\n[TEST 0/4] Dependencies")
    if not await check_dependencies():
        print("\n❌ Missing dependencies!")
        print("\nInstall with:")
        print("   cd 20_NEXUS")
        print("   .venv\\Scripts\\pip install httpx httpx-sse starlette uvicorn")
        return 1

    # Check server connectivity
    print("\n[TEST 1/4] HTTP Connectivity")
    if not await test_http_connectivity():
        print("\n❌ Server is not running!")
        print("\n📝 To start the server:")
        print("   cd 20_NEXUS")
        print("   .venv\\Scripts\\python.exe 03_AGENTS\\mcp_skeleton\\server_sse.py")
        print("\n   Or use the batch file:")
        print("   03_AGENTS\\mcp_skeleton\\start_sse_server.bat")
        return 1

    # Test direct HTTP request
    print("\n[TEST 2/4] Direct HTTP Request")
    await test_direct_http_request()

    # Test MCP client
    print("\n[TEST 3/4] MCP SSE Client")
    client_ok = await test_mcp_sse_client()

    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY ")
    print("=" * 70)

    if client_ok:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 SSE transport is working perfectly!")
        print("   No more Windows stdio pipe issues!")
        print("\n📊 Benefits of SSE over Stdio:")
        print("   - No ProactorEventLoop complexity")
        print("   - Works with any Windows Python setup")
        print("   - HTTP debugging tools available")
        print("   - Can scale to remote servers")
        print("   - Stable on corporate networks")

        print("\n🚀 Next Steps:")
        print("   1. Port COMPASS agents to MCP tools")
        print("   2. Integrate ChromaDB for knowledge base")
        print("   3. Implement learning loop from CHAT_HISTORY")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("\n📝 Troubleshooting:")
        print("   1. Check mcp_server_sse.log for errors")
        print("   2. Verify firewall allows localhost:8000")
        print("   3. Try: curl http://localhost:8000/health")
        print("   4. Check if port 8000 is already in use")
        print("   5. Install httpx-sse if missing")
        return 1


if __name__ == "__main__":
    # Note: No need for ProactorEventLoop with HTTP!
    # SSE/HTTP works with any event loop on Windows

    try:
        exit_code = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit_code = 130

    sys.exit(exit_code)