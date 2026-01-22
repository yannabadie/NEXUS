import warnings
import sys
from pathlib import Path

# Enable all warnings
warnings.simplefilter("always")

# Add the current directory to sys.path so we can import core
sys.path.append(str(Path.cwd()))

try:
    from core.fsm.panic_system import PanicSystem

    print("Import successful")

    # Instantiate
    ps = PanicSystem(Path("./workspace"))
    ps.check_stalemate()
    ps.record_error("TEST", "Test error")
    ps.trigger_panic_explicit("TEST", "Test panic")
    ps.get_panic_info()
    ps.clear_panic()

    print("Execution successful")
except Exception as e:
    print(f"Error: {e}")
