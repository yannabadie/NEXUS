"""NEXUS V7 Synapse - Protocol & Memory"""

# V12.4 COGNITIVE BOOST: Inter-Agent Message Protocol
from .message_protocol import (
    Message,
    MessageHeader,
    MessageThread,
    MessageType,
    Priority,
    create_broadcast,
    create_message,
    create_request,
    validate_message,
)

# V12.4 COGNITIVE BOOST: Message Deduplicator
from .message_deduplicator import (
    MessageDeduplicator,
    MessageFingerprint,
    MessageTrace,
    DeduplicationStats,
    compute_fingerprint,
    get_deduplicator,
    reset_deduplicator,
)

# V12.4: Message Router
from .message_router import (
    MessageRouter,
    RoutedMessage,
    DeadLetter,
    RouteResult,
    QueueInfo,
    RouterStats,
    get_message_router,
    reset_message_router,
)

# V12.4 COGNITIVE BOOST: Message Reliability Tracker
from .message_reliability_tracker import (
    MessageReliabilityTracker,
    DeliveryRecord,
    ChannelMetrics,
    ReliabilityStats as MessageReliabilityStats,
    get_message_tracker,
    reset_message_tracker,
)
