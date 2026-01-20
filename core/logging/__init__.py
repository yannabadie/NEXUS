"""
Logging module for NEXUS V7

Exports:
- NexusLogger: Main logger class
- LogLevel: Log level enum
- EventType: Event type enum
- init_logger: Initialize global logger
- get_logger: Get global logger instance
- cleanup_old_logs: Cleanup old log files
- get_driver_logger: Get lightweight driver logger (V8.4.5)
- configure_driver_logging: Configure driver log level (V8.4.5)
"""
from .logger_v7 import (
    NexusLogger,
    LogLevel,
    EventType,
    init_logger,
    get_logger,
    cleanup_old_logs
)
from .driver_logger import (
    get_driver_logger,
    configure_driver_logging,
    DriverLogger
)

__all__ = [
    'NexusLogger',
    'LogLevel',
    'EventType',
    'init_logger',
    'get_logger',
    'cleanup_old_logs',
    'get_driver_logger',
    'configure_driver_logging',
    'DriverLogger'
]
