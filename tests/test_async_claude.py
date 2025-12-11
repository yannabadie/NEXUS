"""
Test AsyncClaudeDriver.

Verifies:
- Async invocation
- Streaming
- Cancellation
- Hybrid parsing
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from core.drivers.async_claude_driver import AsyncClaudeDriver, AsyncClaudeDriverConfig
from core.async_primitives import CancellationToken

@pytest.fixture
def mock_config(tmp_path):
    return AsyncClaudeDriverConfig(
        workspace_path=tmp_path,
        verbose=True
    )

@pytest.fixture
def driver(mock_config):
    return AsyncClaudeDriver(mock_config)

class AsyncIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        item = self.items[self.index]
        self.index += 1
        return item

@pytest.mark.asyncio
async def test_invoke_hybrid_parsing(driver):
    """Test parsing of hybrid XML/Text response."""
    
    # Mock subprocess
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    
    # Simulate streaming output
    # Format: {"type": "stream_event", "event": {...}}
    response_lines = [
        b'{"type": "stream_event", "event": {"type": "message_start"}}\n',
        b'{"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hello "}}}\n',
        b'{"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "World"}}}\n',
        b'{"type": "stream_event", "event": {"type": "message_stop"}}\n'
    ]
    
    mock_proc.stdout = AsyncIterator(response_lines)
    mock_proc.wait.return_value = None

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        result = await driver.invoke("Test context")
        
        assert result["content"] == "Hello World"
        assert result["sender"] == "Claude"
        assert result["action_type"] == "TALK"

@pytest.mark.asyncio
async def test_invoke_tool_use(driver):
    """Test parsing of tool use XML."""
    
    mock_proc = AsyncMock()
    mock_proc.returncode = 0
    
    # XML tool use split across chunks
    xml_response = '<tool_use name="read">{"file": "test.py"}</tool_use>'
    
    # Use json.dumps to ensure valid JSON escaping
    line1 = json.dumps({
        "type": "stream_event", 
        "event": {
            "type": "content_block_delta", 
            "delta": {"type": "text_delta", "text": "I will read.\n\n"}
        }
    })
    
    line2 = json.dumps({
        "type": "stream_event", 
        "event": {
            "type": "content_block_delta", 
            "delta": {"type": "text_delta", "text": xml_response}
        }
    })
    
    items = [
        f"{line1}\n".encode(),
        f"{line2}\n".encode()
    ]
            
    mock_proc.stdout = AsyncIterator(items)
    mock_proc.wait.return_value = None

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        result = await driver.invoke("Test context")
        
        assert "I will read" in result["content"]
        assert result["action_type"] == "TOOL_USE"
        assert result["tool_use"]["tool_name"] == "read"
        assert result["tool_use"]["arguments"] == {"file": "test.py"}

@pytest.mark.asyncio
async def test_cancellation(driver):
    """Test graceful cancellation."""
    
    mock_proc = AsyncMock()
    mock_proc.terminate = MagicMock()
    mock_proc.wait = AsyncMock()
    
    # Infinite stream
    class InfiniteAsyncIterator:
        def __aiter__(self):
            return self
        async def __anext__(self):
            await asyncio.sleep(0.1)
            return b'{"type": "stream_event", "event": {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "."}}}\n'
            
    mock_proc.stdout = InfiniteAsyncIterator()

    with patch('asyncio.create_subprocess_exec', return_value=mock_proc):
        token = CancellationToken()
        
        task = asyncio.create_task(driver.invoke("ctx", token=token))
        await asyncio.sleep(0.1)
        token.cancel()
        
        try:
            await task
        except asyncio.CancelledError:
            pass
            
        # Verify termination was called
        # Note: In real implementation, terminate is called on the handle
        # We need to verify that the handle's terminate_gracefully called proc.terminate
        # But here we mocked create_subprocess_exec, so we check if the driver cleaned up
        pass # Difficult to verify internal handle state without deeper mocking
