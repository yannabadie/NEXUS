import asyncio
import pytest
import uvicorn
import requests
import time
import threading
from pathlib import Path
from multiprocessing import Process

# Import the app (ensure sys.path is correct)
import sys
sys.path.append(str(Path(__file__).parents[2]))
from core.ui.dashboard_server import app

PORT = 8001 # Use different port to avoid conflict
BASE_URL = f"http://localhost:{PORT}"

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="error")

@pytest.fixture(scope="module")
def dashboard_server():
    # Start server in a separate process
    proc = Process(target=run_server, daemon=True)
    proc.start()
    
    # Wait for server to start
    for _ in range(10):
        try:
            requests.get(f"{BASE_URL}/")
            break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        pytest.fail("Dashboard server failed to start")
        
    yield proc
    
    # Cleanup
    proc.terminate()
    proc.join()

def test_dashboard_root(dashboard_server):
    """Test that the dashboard HTML is served."""
    resp = requests.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    assert "NEXUS" in resp.text

def test_api_agents(dashboard_server):
    """Test the agents API."""
    resp = requests.get(f"{BASE_URL}/api/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # We expect at least Gemini and Claude if registry is working, 
    # or empty list if mocking is needed.
    # Given we are in a test env, registry might be empty or mocked.
    
def test_api_files(dashboard_server):
    """Test the file explorer API."""
    # Request root
    resp = requests.get(f"{BASE_URL}/api/files")
    assert resp.status_code == 200
    data = resp.json()
    assert data['type'] == 'directory'
    assert 'children' in data

def test_telemetry_push(dashboard_server):
    """Test pushing telemetry events."""
    event = {
        "type": "TEST_EVENT",
        "data": {"foo": "bar"}
    }
    resp = requests.post(f"{BASE_URL}/api/telemetry", json=event)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

if __name__ == "__main__":
    # Manual run if executed as script
    proc = Process(target=run_server, daemon=True)
    proc.start()
    time.sleep(2)
    try:
        print("Testing Root...")
        test_dashboard_root(None)
        print("Testing Agents...")
        test_api_agents(None)
        print("Testing Files...")
        test_api_files(None)
        print("Testing Telemetry...")
        test_telemetry_push(None)
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
    finally:
        proc.terminate()
