import pytest
import asyncio
from pathlib import Path
from unittest.mock import MagicMock
from core.drivers.async_factory import create_driver_factory, get_driver_factory
from core.drivers.async_gemini_driver import AsyncGeminiDriver
from core.drivers.async_claude_driver import AsyncClaudeDriver

class MockConfig:
    gemini_cli_path = "gemini"
    claude_cli_path = "claude"
    timeout = 300
    verbose = False
    gemini_default_model = "gemini-mock"
    claude_sonnet_model = "claude-mock"
    gemini_persistent_mode = True

@pytest.fixture
def test_workspace():
    """Create and cleanup test workspace."""
    workspace = Path("workspace_test")
    agents_dir = workspace / "agents"
    
    # Create structure
    if workspace.exists():
        import shutil
        shutil.rmtree(workspace)
    
    workspace.mkdir(parents=True)
    agents_dir.mkdir(parents=True)
    
    yield workspace
    
    # Cleanup
    if workspace.exists():
        import shutil
        shutil.rmtree(workspace)

@pytest.mark.asyncio
async def test_async_factory_creation(test_workspace):
    config = MockConfig()
    workspace_path = test_workspace
    
    factory = create_driver_factory(config, workspace_path)
    
    assert factory is not None
    assert get_driver_factory() == factory
    
    gemini = factory.get_gemini_driver()
    assert isinstance(gemini, AsyncGeminiDriver)
    assert gemini.config.model == "gemini-mock"
    
    claude = factory.get_claude_driver()
    assert isinstance(claude, AsyncClaudeDriver)
    assert claude.config.model == "claude-mock"
    
    # Test singleton behavior
    assert factory.get_gemini_driver() == gemini
    assert factory.get_claude_driver() == claude

@pytest.mark.asyncio
async def test_driver_cancellation(test_workspace):
    config = MockConfig()
    workspace_path = test_workspace
    factory = create_driver_factory(config, workspace_path)
    
    # Mock internal registry
    factory._registry = MagicMock()
    factory._registry.cancel_all = MagicMock(return_value=asyncio.Future())
    factory._registry.cancel_all.return_value.set_result(5)
    
    count = await factory.cancel_all()
    assert count == 5
    factory._registry.cancel_all.assert_called_once()
