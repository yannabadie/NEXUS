"""
Test Semantic Memory (Universal Embeddings).

Verifies:
- DenseBackend uses UniversalIO when sentence-transformers is missing.
- ProjectMemory selects DenseBackend correctly.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch, AsyncMock

# Mock lancedb
mock_lancedb = MagicMock()
sys.modules["lancedb"] = mock_lancedb

# Mock sentence_transformers (ensure it's NOT available)
sys.modules["sentence_transformers"] = None

from core.memory.backends.dense import DenseBackend
from core.memory.project_memory import ProjectMemory
from core.io.universal_io import UniversalIO

@pytest.fixture
def mock_universal_io():
    with patch("core.io.universal_io.UniversalIO") as MockUI:
        instance = MockUI.return_value
        instance.embed = AsyncMock(return_value=[0.1] * 384)
        instance.embed_sync = MagicMock(return_value=[[0.1] * 384]) # Batch return
        MockUI.is_available.return_value = True
        yield instance

def test_dense_backend_uses_universal_io(mock_universal_io):
    """Test that DenseBackend uses UniversalIO when ST is missing."""
    
    # Force ST unavailable
    with patch("core.memory.backends.dense.SENTENCE_TRANSFORMERS_AVAILABLE", False):
        backend = DenseBackend("test_path")
        
        # Ensure model loads UniversalIO
        assert backend._ensure_model() is True
        assert backend._model == mock_universal_io
        assert backend._device == "api"

def test_project_memory_selects_dense(mock_universal_io, tmp_path):
    """Test that ProjectMemory selects DenseBackend if UniversalIO is available."""
    
    with patch("core.memory.backends.dense.SENTENCE_TRANSFORMERS_AVAILABLE", False), \
         patch("core.memory.backends.dense.LANCEDB_AVAILABLE", True), \
         patch("core.io.universal_io.UniversalIO.is_available", return_value=True):
        
        memory = ProjectMemory(tmp_path)
        assert isinstance(memory._backend, DenseBackend)

def test_dense_backend_build_index_universal(mock_universal_io):
    """Test build_index using UniversalIO (Sync)."""
    
    with patch("core.memory.backends.dense.SENTENCE_TRANSFORMERS_AVAILABLE", False):
        backend = DenseBackend("test_path")
        backend._ensure_model()
        backend._ensure_db()
        
        # Mock DB table
        mock_table = MagicMock()
        backend._db.create_table.return_value = mock_table
        
        # Create fake chunks
        chunk = MagicMock()
        chunk.content = "test content"
        chunk.to_dict.return_value = {"content": "test"}
        
        # Run build_index
        backend.build_index([chunk])
        
        # Verify embed_sync was called
        mock_universal_io.embed_sync.assert_called()
        backend._db.create_table.assert_called()
