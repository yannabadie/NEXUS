import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_ui_components():
    """Smoke test for UI components."""
    print("Testing UI Components...")
    
    # 1. Test CodeMapper
    try:
        from core.ui.code_mapper import code_mapper
        graph = code_mapper.scan()
        print(f"✅ CodeMapper: Scanned {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")
    except Exception as e:
        print(f"❌ CodeMapper Failed: {e}")
        sys.exit(1)

    # 2. Test Dashboard Server Import
    try:
        from core.ui.dashboard_server import app
        print("✅ Dashboard Server: Import successful.")
    except Exception as e:
        print(f"❌ Dashboard Server Import Failed: {e}")
        sys.exit(1)

    print("UI Smoke Test Passed!")

if __name__ == "__main__":
    test_ui_components()
