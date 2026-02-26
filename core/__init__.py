"""NEXUS Core Module - COGNITIVE BOOST"""

# Version: single source of truth is pyproject.toml via importlib.metadata
try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("nexus-swarm-os")
except Exception:
    __version__ = "12.4.0"

__codename__ = "COGNITIVE BOOST"
