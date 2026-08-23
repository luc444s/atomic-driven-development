"""LOGI-0017 — customer_address_id en eventos de cilindro en cliente.

Verifica:
- migration 056: columna + índice (+ idempotencia)
- record_cylinder_event persiste customer_address_id
- _record_delivery_cylinder_events propaga la dirección al evento CUSTOMER_DELIVERY
- _record_physical_pickup_events resuelve la dirección desde la parada (delivery_point)
"""
from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module

from sqlalchemy import inspect

from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsDeliveryPoint,
    LogisticsLoadSerialAssignment,
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsRouteOperation,
    LogisticsRouteOperationItem,
    LogisticsRouteStop,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.cylinders import (
    get_last_location_event,
    record_cylinder_event,
)
from plugins.logistics.backend.services.route_operation_confirmation import (
    _record_delivery_cylinder_events,
    _record_physical_pickup_events,
)

migration_056 = import_module(
    "plugins.logistics.migrations.056_cylinder_event_customer_address_v1"
)


def _action_context(seeded_demo: dict[str, str]) -> LogisticsActionContext:
    return LogisticsActionContext(
        tenant_id=seeded_demo["tenant_id"],
        branch_id=seeded_demo["branch_id"],
        actor_user_id=seeded_demo["user_id"],
        correlation_id=None,
        request_id=None,
    )


def _make_cylinder(
    db,
    seeded_demo: dict[str, str],
    *,
    serial: str,
    state: str = "LLENADO_OK",
    product_id: str = "prod-1",
) -> LogisticsCylinder:
    cylinder = LogisticsCylinder(
        tenant_id=seeded_demo["tenant_id"],
        branch_id=seeded_demo["branch_id"],
        serial=serial,
        product_id=product_id,
        condition="CILPRO",
        current_state=state,
    )
    db.add(cylinder)
    db.flush()
    return cylinder


def _make_session(db, seeded_demo: dict[str, str]) -> LogisticsVehicleSession:
    session = LogisticsVehicleSession(
        tenant_id=seeded_demo["tenant_id"],
        vehicle_id="veh-1",
        driver_id=seeded_demo["user_id"],
        origin_warehouse_id="wh-1",
        mobile_warehouse_id="wh-1",
        status="OUTBOUND",
        created_by=seeded_demo["user_id"],
        updated_by=seeded_demo["user_id"],
    )
    db.add(session)
    db.flush()
    return session


def _record_location_history(
    db,
    seeded_demo: dict[str, str],
    *,
    cylinder: LogisticsCylinder,
    session: LogisticsVehicleSession,
    customer_id: str,
    include_customer: bool = True,
) -> None:
    from datetime import timedelta

    ctx = _action_context(seeded_demo)
    base = datetime.now(UTC) - timedelta(minutes=1)
    record_cylinder_event(
        db,
        cylinder_id=cylinder.id,
        tenant_id=seeded_demo["tenant_id"],
        event_type="WAREHOUSE_IN",
        location_type="WAREHOUSE",
        location_id="wh-1",
        warehouse_id="wh-1",
        session_id=None,
        customer_id=None,
        source_type="TEST",
        source_id=f"setup-wh-{cylinder.id}",
        occurred_at=base,
        action_context=ctx,
    )
    record_cylinder_event(
        db,
        cylinder_id=cylinder.id,
        tenant_id=seeded_demo["tenant_id"],
        event_type="VEHICLE_LOAD",
        location_type="VEHICLE",
        location_id=session.id,
        warehouse_id=None,
        session_id=session.id,
        customer_id=None,
        source_type="TEST",
        source_id=f"setup-load-{cylinder.id}",
        occurred_at=base + timedelta(seconds=1),
        action_context=ctx,
    )
    if not include_customer:
        return
    record_cylinder_event(
        db,
        cylinder_id=cylinder.id,
        tenant_id=seeded_demo["tenant_id"],
        event_type="CUSTOMER_DELIVERY",
        location_type="CUSTOMER",
        location_id=customer_id,
        warehouse_id=None,
        session_id=session.id,
        customer_id=customer_id,
        source_type="TEST",
        source_id=f"setup-delivery-{cylinder.id}",
        occurred_at=base + timedelta(seconds=2),
        action_context=ctx,
    )


def test_migration_056_adds_customer_address_column_and_index(db_session) -> None:
    migration_056.upgrade(db_session)
    db_session.commit()

    inspector = inspect(db_session.connection())
    columns = {col["name"] for col in inspector.get_columns("lg_cylinder_events")}
    assert "customer_address_id" in columns
    index_names = {idx["name"] for idx in inspector.get_indexes("lg_cylinder_events")}
    assert "ix_lg_cylinder_events_customer_address" in index_names

    # Idempotencia: re-ejecutar no falla.
    migration_056.upgrade(db_session)
    db_session.commit()


def test_record_cylinder_event_persists_customer_address_id(db_session, seeded_demo) -> None:
    session = _make_session(db_session, seeded_demo)
    cylinder = _make_cylinder(db_session, seeded_demo, serial="ADDR-EVT-1")

    _record_location_history(
        db_session,
        seeded_demo,
        cylinder=cylinder,
        session=session,
        customer_id="cust-1",
        include_customer=False,
    )
    ctx = _action_context(seeded_demo)
    record_cylinder_event(
        db_session,
        cylinder_id=cylinder.id,
        tenant_id=seeded_demo["tenant_id"],
        event_type="CUSTOMER_DELIVERY",
        location_type="CUSTOMER",
        location_id="cust-1",
        warehouse_id=None,
        session_id=session.id,
        customer_id="cust-1",
        customer_address_id="addr-A",
        source_type="TEST",
        source_id="event-1",
        occurred_at=datetime.now(UTC),
        action_context=ctx,
    )

    event = get_last_location_event(db_session, cylinder_id=cylinder.id)
    assert event is not None
    assert event.customer_address_id == "addr-A"


def test_delivery_cylinder_events_carry_customer_address(db_session, seeded_demo) -> None:
    session = _make_session(db_session, seeded_demo)
    movement = LogisticsMovement(
        tenant_id=seeded_demo["tenant_id"],
        movement_type="SC",
        status="COMPLETADO",
        created_by=seeded_demo["user_id"],
    )
    db_session.add(movement)
    db_session.flush()

    cylinder = _make_cylinder(db_session, seeded_demo, serial="ADDR-DEL-1", state="EN_RUTA")
    db_session.add(
        LogisticsMovementItem(
            movement_id=movement.id,
            cylinder_id=cylinder.id,
            product_id="prod-1",
            product_name="Bombona test",
            quantity=1,
            quantity_out=1,
        )
    )
    db_session.flush()

    _record_location_history(
        db_session,
        seeded_demo,
        cylinder=cylinder,
        session=session,
        customer_id="cust-1",
        include_customer=False,
    )

    _record_delivery_cylinder_events(
        db_session,
        tenant_id=seeded_demo["tenant_id"],
        session=session,
        movement=movement,
        items=[],
        customer_id="cust-1",
        customer_address_id="addr-A",
        action_context=_action_context(seeded_demo),
    )

    event = get_last_location_event(db_session, cylinder_id=cylinder.id)
    assert event is not None
    assert event.event_type == "CUSTOMER_DELIVERY"
    assert event.customer_address_id == "addr-A"


def test_physical_pickup_events_resolve_address_from_stop(db_session, seeded_demo) -> None:
    session = _make_session(db_session, seeded_demo)

    delivery_point = LogisticsDeliveryPoint(
        tenant_id=seeded_demo["tenant_id"],
        customer_id="cust-1",
        customer_name="Cliente Parada",
        address="Calle Parada 100",
        address_id="addr-A",
    )
    db_session.add(delivery_point)
    db_session.flush()

    stop = LogisticsRouteStop(
        route_id="route-1",
        delivery_point_id=delivery_point.id,
        stop_order=1,
    )
    db_session.add(stop)
    db_session.flush()

    operation = LogisticsRouteOperation(
        tenant_id=seeded_demo["tenant_id"],
        session_id=session.id,
        route_stop_id=stop.id,
        operation_type="PICKUP",
        idempotency_key="pickup-address-test",
    )
    db_session.add(operation)
    db_session.flush()

    cylinder = _make_cylinder(
        db_session, seeded_demo, serial="ADDR-PUP-1", state="EN_CLIENTE_VACIO"
    )
    db_session.add(
        LogisticsLoadSerialAssignment(
            tenant_id=seeded_demo["tenant_id"],
            session_id=session.id,
            product_id="prod-1",
            cylinder_id=cylinder.id,
            cylinder_serial=cylinder.serial,
            assignment_status="CONFIRMED",
            selected_by=seeded_demo["user_id"],
        )
    )
    db_session.flush()

    _record_location_history(
        db_session,
        seeded_demo,
        cylinder=cylinder,
        session=session,
        customer_id="cust-1",
    )

    items = [
        LogisticsRouteOperationItem(
            route_operation_id=operation.id,
            product_id="prod-1",
            product_name="Bombona test",
            quantity=1,
            direction="IN",
        )
    ]
    db_session.add_all(items)
    db_session.flush()

    _record_physical_pickup_events(
        db_session,
        tenant_id=seeded_demo["tenant_id"],
        session=session,
        operation=operation,
        items=items,
        customer_id="cust-1",
        action_context=_action_context(seeded_demo),
    )

    event = get_last_location_event(db_session, cylinder_id=cylinder.id)
    assert event is not None
    assert event.event_type == "CUSTOMER_PICKUP"
    assert event.customer_address_id == "addr-A"
