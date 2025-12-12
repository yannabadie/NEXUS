"""
System Monitor for NEXUS V9.0
Collects real system telemetry (CPU, RAM, Disk) for the Dashboard.
"""

import os
import sys
import time
import logging
import threading
import asyncio
from typing import Dict, Any

logger = logging.getLogger("nexus.system_monitor")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SystemMonitor:
    """
    Monitors system resources and broadcasts stats via EventBus.
    """
    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.running = False
        self._last_cpu_check = time.time()
        
    async def start_monitoring(self, interval: float = 2.0):
        """Start the monitoring loop."""
        self.running = True
        logger.info(f"System Monitor started (Interval: {interval}s, Psutil: {PSUTIL_AVAILABLE})")
        
        while self.running:
            stats = self.get_stats()
            if self.event_bus:
                await self.event_bus.publish("SYSTEM_STATS", stats)
            
            await asyncio.sleep(interval)

    def stop(self):
        """Stop monitoring."""
        self.running = False

    def get_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        stats = {
            "timestamp": time.time(),
            "platform": sys.platform,
            "python_version": sys.version.split()[0]
        }

        if PSUTIL_AVAILABLE:
            try:
                # CPU
                stats["cpu_percent"] = psutil.cpu_percent(interval=None)
                
                # Memory
                mem = psutil.virtual_memory()
                stats["memory_total"] = mem.total
                stats["memory_available"] = mem.available
                stats["memory_percent"] = mem.percent
                stats["memory_used_mb"] = (mem.total - mem.available) / (1024 * 1024)
                
                # Disk
                disk = psutil.disk_usage('.')
                stats["disk_percent"] = disk.percent
                
                # Process
                process = psutil.Process(os.getpid())
                stats["process_memory_mb"] = process.memory_info().rss / (1024 * 1024)
                stats["process_cpu_percent"] = process.cpu_percent(interval=None)
                
            except Exception as e:
                logger.error(f"Error getting psutil stats: {e}")
                stats["error"] = str(e)
        else:
            # Fallback for when psutil is not installed
            # We can't get real CPU usage easily without psutil in a cross-platform way
            # so we mark it as unavailable
            stats["cpu_percent"] = 0.0
            stats["memory_percent"] = 0.0
            stats["status"] = "psutil_missing"

        return stats
