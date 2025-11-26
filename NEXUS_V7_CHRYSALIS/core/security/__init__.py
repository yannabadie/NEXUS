"""
NEXUS Security Module

Core security components for integrity monitoring and protection.

Modules:
- integrity_monitor: Real-time monitoring of protected files (KERNEL, MISSION, etc.)
"""

from .integrity_monitor import IntegrityMonitor

__all__ = ["IntegrityMonitor"]
