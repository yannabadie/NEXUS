"""
NEXUS V5.0 - Resource Monitor
Surveillance CPU/RAM avec psutil (fallback si indisponible).
"""
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from core.config import Config


class ResourceMonitor:
    """Surveillance des ressources système."""

    def __init__(self, config: Config):
        self.cpu_threshold = config.resource_cpu_threshold
        self.ram_threshold = config.resource_ram_threshold
        self.enabled = PSUTIL_AVAILABLE

    def is_overloaded(self) -> bool:
        """Vérifie si les ressources sont surchargées."""
        if not self.enabled:
            return False  # Pas de monitoring si psutil absent

        cpu_percent = psutil.cpu_percent(interval=1)
        ram_percent = psutil.virtual_memory().percent

        if cpu_percent > self.cpu_threshold:
            return True

        if ram_percent > self.ram_threshold:
            return True

        return False

    def get_stats(self) -> dict:
        """Retourne les statistiques actuelles."""
        if not self.enabled:
            return {
                "cpu_percent": 0,
                "ram_percent": 0,
                "ram_available_gb": 0,
                "monitoring_enabled": False
            }

        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
            "ram_available_gb": psutil.virtual_memory().available / (1024 ** 3),
            "monitoring_enabled": True
        }
