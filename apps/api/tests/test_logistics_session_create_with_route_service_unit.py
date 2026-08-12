from __future__ import annotations

from sqlalchemy import select

from apps.api.app.commands.seed_demo import seed_demo_data
from plugins.crm.backend.models import CrmCustomer, CrmCustomerAddress, CrmDocumentType
from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.models import (
    LogisticsRoute,
    LogisticsRouteCalculation,
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.services.routing.models import (
    RoutingCalculatedStop,
    RoutingCalculationResponse,
    RoutingCommitOrderResponse,
    RoutingTotals,
)
from plugins.logistics.backend.services.sessions import create_vehicle_session_with_route


class _Payload:
    def __init__(
        self,
        *,
        vehicle_id: str,
        driver_id: str,
        origin_warehouse_id: str,
        route_id: str | None = None,
        customer_ids: list[str] | None = None,
        address_ids: list[str] | None = None,
        route_date=None,
    ) -> None:
        self.vehicle_id = vehicle_id
        self.driver_id = driver_id
        self.origin_warehouse_id = origin_warehouse_id
        self.route_id = route_id
        self.customer_ids = customer_ids or []
        self.address_ids = address_ids or []
        self.route_date = route_date


def _seed_with_vehicle_and_address(db_session, app):
    seeded = seed_demo_data(db_session, app.state.settings, app.state.plugin_runtime.list_results())
    warehouse = LogisticsWarehouse(
        tenant_id=seeded["tenant_id"],
        branch_id=seeded["branch_id"],
        name="Warehouse Routing",
        code="WH-ROUTING",
        latitude=40.4168,
        longitude=-3.7038,
    )
    db_session.add(warehouse)
    db_session.flush()
    vehicle = LogisticsVehicle(
        tenant_id=seeded["tenant_id"],
        plate="ROUTE-001",
        warehouse_id=warehouse.id,
    )
    db_session.add(vehicle)
    db_session.flush()
    document_type = db_session.scalar(select(CrmDocumentType).limit(1))
    if document_type is None:
        document_type = CrmDocumentType(
            code="DNI",
            name="Documento",
            country_code="PE",
        )
        db_session.add(document_type)
        db_session.flush()
    customer = CrmCustomer(
        tenant_id=seeded["tenant_id"],
        legal_name="Cliente Ruta",
        commercial_name="Cliente Ruta",
        document_type_code=document_type.code,
        document_number="ROUTE-TEST-001",
        created_by=seeded["user_id"],
    )
    db_session.add(customer)
    db_session.flush()
    address = CrmCustomerAddress(
        tenant_id=seeded["tenant_id"],
        customer_id=customer.id,
        line1="Madrid Centro",
        latitude=40.4168,
        longitude=-3.7038,
    )
    db_session.add(address)
    db_session.commit()
    return seeded, warehouse, vehicle, customer, address


def _context(seeded) -> LogisticsActionContext:
    return LogisticsActionContext(
        tenant_id=seeded["tenant_id"],
        branch_id=seeded["branch_id"],
        actor_user_id=seeded["user_id"],
        correlation_id="test-routing",
        request_id="test-routing",
    )


def test_create_with_route_service_builds_route_snapshot_and_session(
    db_session,
    app,
    monkeypatch,
) -> None:
    seeded, warehouse, vehicle, customer, address = _seed_with_vehicle_and_address(db_session, app)

    from plugins.logistics.backend.services import sessions as sessions_service

    def fake_preview(_self, request):
        return RoutingCalculationResponse(
            provider_stack="osrm+vroom",
            route_id=request.route_id,
            ordered_stops=[RoutingCalculatedStop(stop_id=request.stops[0].stop_id, sequence=1)],
            totals=RoutingTotals(
                distance_m=1000,
                travel_seconds=600,
                service_seconds=0,
                total_seconds=600,
            ),
            polyline="poly-xyz",
        )

    def fake_commit(self, db, *, tenant_id, actor_user_id, payload):
        calculation = LogisticsRouteCalculation(
            tenant_id=tenant_id,
            route_id=payload.route_id,
            provider_stack=payload.preview.provider_stack,
            input_hash="hash-1",
            ordered_stop_ids_json=[item.stop_id for item in payload.preview.ordered_stops],
            totals_json=payload.preview.totals.model_dump(),
            violations_json=payload.preview.violations,
            polyline=payload.preview.polyline,
            created_by=actor_user_id,
        )
        db.add(calculation)
        db.flush()
        return RoutingCommitOrderResponse(
            calculation_id=calculation.id,
            route_id=payload.route_id,
            committed=True,
            stop_count=len(payload.preview.ordered_stops),
        )

    monkeypatch.setattr(sessions_service.RoutingService, "calculate_preview", fake_preview)
    monkeypatch.setattr(sessions_service.RoutingService, "commit_order", fake_commit)

    session = create_vehicle_session_with_route(
        db_session,
        tenant_id=seeded["tenant_id"],
        payload=_Payload(
            vehicle_id=vehicle.id,
            driver_id=seeded["user_id"],
            origin_warehouse_id=warehouse.id,
            customer_ids=[customer.id],
            address_ids=[address.id],
        ),
        action_context=_context(seeded),
        settings=app.state.settings,
    )
    db_session.commit()

    route = db_session.scalar(
        select(LogisticsRoute).where(
            LogisticsRoute.id == session.route_id,
        )
    )
    calculation = db_session.scalar(
        select(LogisticsRouteCalculation).where(
            LogisticsRouteCalculation.route_id == session.route_id,
        )
    )

    assert session.route_id is not None
    assert route is not None
    assert calculation is not None


def test_create_with_route_service_rolls_back_when_routing_fails(
    db_session,
    app,
    monkeypatch,
) -> None:
    seeded, warehouse, vehicle, customer, address = _seed_with_vehicle_and_address(db_session, app)

    from plugins.logistics.backend.services import sessions as sessions_service

    def fail_preview(_self, request):
        raise RuntimeError("routing stack unavailable")

    monkeypatch.setattr(sessions_service.RoutingService, "calculate_preview", fail_preview)

    try:
        create_vehicle_session_with_route(
            db_session,
            tenant_id=seeded["tenant_id"],
            payload=_Payload(
                vehicle_id=vehicle.id,
                driver_id=seeded["user_id"],
                origin_warehouse_id=warehouse.id,
                customer_ids=[customer.id],
                address_ids=[address.id],
            ),
            action_context=_context(seeded),
            settings=app.state.settings,
        )
    except RuntimeError as exc:
        assert str(exc) == "routing stack unavailable"
        db_session.rollback()
    else:
        raise AssertionError("Expected routing failure")

    routes = list(
        db_session.scalars(
            select(LogisticsRoute).where(
                LogisticsRoute.tenant_id == seeded["tenant_id"],
                LogisticsRoute.vehicle_id == vehicle.id,
            )
        ).all()
    )
    sessions = list(
        db_session.scalars(
            select(LogisticsVehicleSession).where(
                LogisticsVehicleSession.tenant_id == seeded["tenant_id"],
                LogisticsVehicleSession.vehicle_id == vehicle.id,
            )
        ).all()
    )
    calculations = list(
        db_session.scalars(
            select(LogisticsRouteCalculation).where(
                LogisticsRouteCalculation.tenant_id == seeded["tenant_id"]
            )
        ).all()
    )

    assert routes == []
    assert sessions == []
    assert calculations == []
