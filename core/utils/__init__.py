"""
NEXUS V7.5 HIVE MIND Utility modules.
"""
from .artifact_verifier import ArtifactVerifier
from .atomic_store import (
    AtomicJsonStore,
    AtomicJsonStoreManager,
    get_store,
)
from .json_extractor import (
    extract_json,
    extract_json_safe,
    extract_code_block,
    wrap_json,
)
from .stream_parser import (
    parse_stream_chunk,
    is_result_message,
    extract_final_result,
    extract_stats,
    is_tool_message,
    extract_tool_info,
)
from .async_utils import (
    run_sync,
    get_or_create_event_loop,
    run_in_thread,
)
from .serialization import (
    NexusJSONEncoder,
    nexus_dumps,
    nexus_loads,
    serialize_for_checkpoint,
)

# V12.4 COGNITIVE BOOST: Output Validation
from .output_validator import (
    OutputValidator,
    Schema,
    Field,
    ValidationResult,
    ValidationError,
)

# V12.4 COGNITIVE BOOST: Event Bus
from .event_bus import EventBus, Event, get_event_bus, reset_event_bus

# V12.4 COGNITIVE BOOST: Feature Flags
from .feature_flags import FeatureFlags, FlagDefinition, get_flags, reset_flags

# V12.4 COGNITIVE BOOST: Config Manager
from .config_manager import ConfigManager, ConfigEntry, get_config_manager, reset_config_manager

# V12.4 COGNITIVE BOOST: Schema Registry
from .schema_registry import (
    SchemaRegistry, SchemaDefinition, SchemaValidationResult,
    get_schema_registry, reset_schema_registry,
)

__all__ = [
    "ArtifactVerifier",
    "AtomicJsonStore",
    "AtomicJsonStoreManager",
    "get_store",
    "extract_json",
    "extract_json_safe",
    "extract_code_block",
    "wrap_json",
    "parse_stream_chunk",
    "is_result_message",
    "extract_final_result",
    "extract_stats",
    "is_tool_message",
    "extract_tool_info",
    "run_sync",
    "get_or_create_event_loop",
    "run_in_thread",
    "NexusJSONEncoder",
    "nexus_dumps",
    "nexus_loads",
    "serialize_for_checkpoint",
    # V12.4 COGNITIVE BOOST: Output Validation
    "OutputValidator",
    "Schema",
    "Field",
    "ValidationResult",
    "ValidationError",
    # V12.4 COGNITIVE BOOST: Event Bus
    "EventBus",
    "Event",
    "get_event_bus",
    "reset_event_bus",
    # V12.4 COGNITIVE BOOST: Feature Flags
    "FeatureFlags",
    "FlagDefinition",
    "get_flags",
    "reset_flags",
    # V12.4 COGNITIVE BOOST: Config Manager
    "ConfigManager",
    "ConfigEntry",
    "get_config_manager",
    "reset_config_manager",
    # V12.4 COGNITIVE BOOST: Schema Registry
    "SchemaRegistry",
    "SchemaDefinition",
    "SchemaValidationResult",
    "get_schema_registry",
    "reset_schema_registry",
]
