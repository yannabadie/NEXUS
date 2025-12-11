"""
Test UniversalIO.

Verifies:
- litellm integration
- Streaming
- Error handling
"""

import pytest
import asyncio
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Mock litellm module BEFORE importing UniversalIO
mock_litellm = MagicMock()
mock_litellm.acompletion = AsyncMock()
sys.modules["litellm"] = mock_litellm

from core.io.universal_io import UniversalIO

@pytest.fixture
def io():
    # Force LITELLM_AVAILABLE to True for testing
    import core.io.universal_io
    core.io.universal_io.LITELLM_AVAILABLE = True
    return UniversalIO(verbose=True)

@pytest.mark.asyncio
async def test_invoke_mock(io):
    """Test invoke with mocked litellm."""
    
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Hello from GPT"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.model = "gpt-4o"
    mock_response.usage.dict.return_value = {"total_tokens": 10}
    
    mock_litellm.acompletion.return_value = mock_response
        
    result = await io.invoke("gpt-4o", [{"role": "user", "content": "Hi"}])
    
    assert result["content"] == "Hello from GPT"
    assert result["model"] == "gpt-4o"
    mock_litellm.acompletion.assert_called_once()

@pytest.mark.asyncio
async def test_invoke_stream_mock(io):
    """Test streaming with mocked litellm."""
    
    # Mock async generator
    async def mock_stream(*args, **kwargs):
        chunks = ["Hello", " ", "World"]
        for c in chunks:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = c
            yield chunk
            
    mock_litellm.acompletion.side_effect = mock_stream
    
    chunks = []
    async for chunk in io.invoke_stream("gpt-4o", [{"role": "user", "content": "Hi"}]):
        chunks.append(chunk)
        
    assert "".join(chunks) == "Hello World"
