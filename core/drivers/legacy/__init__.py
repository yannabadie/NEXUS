"""
Legacy CLI-based drivers (subprocess.Popen).

These drivers are maintained for backwards compatibility and fallback.
Prefer SDK-native drivers (AnthropicSDKDriver, GoogleGenAISDKDriver) for
new code.

Migration path:
    # Old (CLI subprocess):
    from core.drivers.legacy import GeminiDriverV7, ClaudeDriverHybrid

    # New (SDK-native):
    from core.drivers import AnthropicSDKDriver, GoogleGenAISDKDriver
"""

from .gemini_driver_v7 import GeminiDriverV7
from .claude_driver_hybrid import ClaudeDriverHybrid

__all__ = ["GeminiDriverV7", "ClaudeDriverHybrid"]
