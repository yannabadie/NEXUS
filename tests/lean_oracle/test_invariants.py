from __future__ import annotations

import asyncio
from pathlib import Path

import pytest


def _invariant_names(lines: list[str]) -> set[str]:
    names: set[str] = set()
    for line in lines:
        if not line.startswith("INVARIANT|"):
            continue
        parts = line.split("|", 2)
        if len(parts) >= 2:
            names.add(parts[1])
    return names


@pytest.mark.lean_oracle
def test_invariants_declared(lean_oracle_lines):
    expected = {
        "tenant_isolation",
        "workspace_isolation",
        "cancellation_propagation",
        "event_delivery",
    }
    assert expected.issubset(_invariant_names(lean_oracle_lines))


def test_tenant_isolation_service_factory():
    from core.context import use_context
    from core.factory import ServiceFactory

    ServiceFactory.clear_all_caches()
    try:
        with use_context(tenant_id="tenant_a", workspace_id="ws_a"):
            registry_a = ServiceFactory.get_registry()
        with use_context(tenant_id="tenant_b", workspace_id="ws_a"):
            registry_b = ServiceFactory.get_registry()

        assert registry_a is not registry_b
    finally:
        ServiceFactory.clear_all_caches()


def test_workspace_isolation_paths():
    from core.context import SessionContext
    from core.factory import ServiceFactory

    ServiceFactory.initialize(Path("."))
    ctx_a = SessionContext(tenant_id="tenant_a", workspace_id="ws_a")
    ctx_b = SessionContext(tenant_id="tenant_a", workspace_id="ws_b")

    path_a = ServiceFactory.get_tenant_workspace_path(ctx_a)
    path_b = ServiceFactory.get_tenant_workspace_path(ctx_b)

    assert path_a != path_b
    assert "tenant_a" in str(path_a)
    assert "ws_a" in str(path_a)
    assert "ws_b" in str(path_b)


def test_cancellation_propagation():
    from core.async_primitives.cancellation import CancellationToken

    token = CancellationToken()
    child = token.create_child()
    token.cancel(reason="unit-test")

    assert child.is_cancelled is True
    with pytest.raises(asyncio.CancelledError):
        child.check()


@pytest.mark.asyncio
async def test_event_delivery_in_memory():
    from core.events.redis_bus import get_redis_bus, reset_redis_bus
    from core.events.types import CerebroEvent, CerebroEventType

    reset_redis_bus()
    bus = get_redis_bus()
    bus.set_main_loop(asyncio.get_running_loop())

    subscriber = bus.subscribe("tenant_a", "ws_a")
    task = asyncio.create_task(anext(subscriber))

    await asyncio.sleep(0)
    event = CerebroEvent(
        event_type=CerebroEventType.LOG,
        tenant_id="tenant_a",
        workspace_id="ws_a",
        payload={"message": "invariant"},
    )

    published = await bus.publish(event)
    received = await asyncio.wait_for(task, timeout=2.0)

    assert published is True
    assert received.event_id == event.event_id

    await subscriber.aclose()
    reset_redis_bus()
