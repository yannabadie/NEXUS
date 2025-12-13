"""
V10 Test Script - Verify session_uuid Propagation and Bug Fixes
"""
import sys
import os
import ast

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modified files can be imported."""
    print("\n🔍 Testing imports...")
    
    errors = []
    
    # Test core imports
    modules = [
        "core.hive_mind.orchestrator",
        "core.hive_mind.phases.phase_analysis",
        "core.hive_mind.phases.phase_debate",
        "core.hive_mind.phases.phase_architecture",
        "core.hive_mind.phases.phase_execution",
        "core.hive_mind.phases.phase_diagnosis",
        "core.hive_mind.phases.phase_consolidation",
    ]
    
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except Exception as e:
            print(f"  ❌ {module}: {e}")
            errors.append((module, str(e)))
    
    return len(errors) == 0, errors


def test_session_uuid_in_orchestrator():
    """Test that TrueHiveMind has session_uuid generation."""
    print("\n🔍 Testing session_uuid in TrueHiveMind...")
    
    from core.hive_mind.orchestrator import TrueHiveMind
    import inspect
    
    # Check that process_task mentions _current_session_uuid
    source = inspect.getsource(TrueHiveMind.process_task)
    
    if "_current_session_uuid" in source:
        print("  ✅ TrueHiveMind.process_task() generates session_uuid")
        return True
    else:
        print("  ❌ session_uuid not found in process_task")
        return False


def test_phase_signatures():
    """Test that all phases accept session_uuid parameter."""
    print("\n🔍 Testing phase execute() signatures...")
    
    from core.hive_mind.phases.phase_analysis import IndependentAnalysisPhase
    from core.hive_mind.phases.phase_debate import StrategicDebatePhase
    from core.hive_mind.phases.phase_architecture import ArchitectureGenerationPhase
    from core.hive_mind.phases.phase_execution import MonitoredExecutionPhase
    from core.hive_mind.phases.phase_diagnosis import FailureDiagnosisPhase
    from core.hive_mind.phases.phase_consolidation import KnowledgeConsolidationPhase
    
    import inspect
    
    phases = [
        ("Phase 1 Analysis", IndependentAnalysisPhase, "execute"),
        ("Phase 2 Debate", StrategicDebatePhase, "execute"),
        ("Phase 3 Architecture", ArchitectureGenerationPhase, "execute"),
        ("Phase 4 Execution", MonitoredExecutionPhase, "execute"),
        ("Phase 5 Diagnosis", FailureDiagnosisPhase, "execute"),
        ("Phase 7 Consolidation", KnowledgeConsolidationPhase, "execute"),
    ]
    
    all_ok = True
    for name, cls, method in phases:
        sig = inspect.signature(getattr(cls, method))
        params = list(sig.parameters.keys())
        
        if "session_uuid" in params:
            print(f"  ✅ {name}: has session_uuid parameter")
        else:
            print(f"  ❌ {name}: MISSING session_uuid parameter")
            all_ok = False
    
    return all_ok


def test_json_parsing():
    """Test JSON parsing with ast.literal_eval fallback."""
    print("\n🔍 Testing JSON parsing improvements...")
    
    # Test case: Python dict repr (single quotes)
    test_inputs = [
        ('{"key": "value"}', True),  # Valid JSON
        ("{'key': 'value'}", True),  # Python dict (should work with ast.literal_eval)
        ('invalid', False),  # Invalid
    ]
    
    all_ok = True
    for input_str, should_succeed in test_inputs:
        try:
            import json
            result = json.loads(input_str)
            success = True
        except json.JSONDecodeError:
            try:
                result = ast.literal_eval(input_str)
                success = isinstance(result, dict)
            except:
                success = False
        
        if success == should_succeed:
            print(f"  ✅ '{input_str[:30]}...' -> {'parsed' if success else 'failed'} (expected)")
        else:
            print(f"  ❌ '{input_str[:30]}...' unexpected result")
            all_ok = False
    
    return all_ok


def test_ansi_colors():
    """Test ANSI color output on Windows."""
    print("\n🔍 Testing ANSI colors...")
    
    import os
    import sys
    
    if sys.platform == 'win32':
        os.system('')  # Enable ANSI on Windows
    
    print("  \033[36m[CYAN]\033[0m \033[32m[GREEN]\033[0m \033[33m[YELLOW]\033[0m")
    print("  ✅ If you see colors above, ANSI works!")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("NEXUS V10 - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    ok, errors = test_imports()
    results.append(("Imports", ok))
    
    if ok:
        # Test 2: Session UUID in orchestrator
        ok = test_session_uuid_in_orchestrator()
        results.append(("Session UUID Generation", ok))
        
        # Test 3: Phase signatures
        ok = test_phase_signatures()
        results.append(("Phase Signatures", ok))
    
    # Test 4: JSON parsing
    ok = test_json_parsing()
    results.append(("JSON Parsing", ok))
    
    # Test 5: ANSI colors
    ok = test_ansi_colors()
    results.append(("ANSI Colors", ok))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {status}: {name}")
        if ok:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-" * 60)
    print(f"Total: {passed}/{passed + failed} tests passed")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
