"""
Logging module for NEXUS V6

Exports:
- NexusLogger: Main logger class
- LogLevel: Log level enum
- EventType: Event type enum
- init_logger: Initialize global logger
- get_logger: Get global logger instance
- cleanup_old_logs: Cleanup old log files
"""
from .logger_v6 import (
    NexusLogger,
    LogLevel,
    EventType,
    init_logger,
    get_logger,
    cleanup_old_logs
)

__all__ = [
    'NexusLogger',
    'LogLevel',
    'EventType',
    'init_logger',
    'get_logger',
    'cleanup_old_logs'
]
