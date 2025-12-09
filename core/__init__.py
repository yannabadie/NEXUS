"""NEXUS Core Module - TRUE HIVE MIND"""
import os
from dotenv import load_dotenv

# Load .env to get version
load_dotenv()

# Version from .env (single source of truth)
__version__ = os.getenv("NEXUS_VERSION", "8.3.1")
__codename__ = os.getenv("NEXUS_CODENAME", "TRUE HIVE MIND")
