from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.app.core.config import get_settings
from plugins.crm.backend.schemas import CustomerListItemRead
from plugins.crm.backend.services.customers import list_customers
from plugins.logistics.backend.dto.route_context import RouteContextRead
from plugins.logistics.backend.schemas import (
    RouteRead,
    RouteStopRead,
    RoutingAssignedRouteRead,
    WarehouseRead,
)
from plugins.logistics.backend.services.resources import list_warehouses
from plugins.logistics.backend.services.route_operations import (
    build_current_composition,
    list_route_incidents,
    list_route_operations,
)
from plugins.logistics.backend.services.route_stop_results import (
    build_route_stop_progress,
    list_route_stop_results,
)
from plugins.logistics.backend.services.routes import get_route, list_route_stops
from plugins.logistics.backend.services.routing.service import RoutingService
from plugins.logistics.backend.services.session_waybills import (
    get_session_waybill_state,
    list_session_waybill_history,
)
from plugins.logistics.backend.services.sessions import get_vehicle_session
from plugins.logistics.backend.services.snapshots import build_session_snapshot

ROUTE_CONTEXT_CUSTOMER_LIMIT = 200


def _build_customer_read(item) -> CustomerListItemRead:
    return CustomerListItemRead(
        id=item.id,
        legal_name=item.legal_name,
        commercial_name=item.commercial_name,
        external_code=item.external_code,
        document_type_code=item.document_type_code,
        document_number=item.document_number,
        country_code=item.country_code,
        email=item.email,
        phone=item.phone,
        mobile=item.mobile,
        payment_term_code=item.payment_term_code,
        billing_type=item.billing_type,
        is_exempt=item.is_exempt,
        accounting_code=item.accounting_code,
        is_intracommunity=item.is_intracommunity,
        fiscal_operation_key=item.fiscal_operation_key,
        tax_regime_code=item.tax_regime_code,
        equivalence_surcharge_applicable=item.equivalence_surcharge_applicable,
        cash_criterion_applicable=item.cash_criterion_applicable,
        is_active=item.is_active,
        fiscal_address_id=item.fiscal_address_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def build_route_context(
    db: Session,
    *,
    tenant_id: str,
    session_id: str,
) -> RouteContextRead:
    session = get_vehicle_session(db, tenant_id=tenant_id, session_id=session_id)
    if session is None:
        raise LookupError("Jornada no encontrada")

    route_id = session.route_id

    route_detail = None
    assigned_route = None
    stops: list[RouteStopRead] = []
    if route_id:
        route = get_route(db, tenant_id=tenant_id, route_id=route_id)
        if route is not None:
            route_detail = RouteRead.model_validate(route)
        snapshot = RoutingService(get_settings()).get_latest_assigned_route(
            db,
            tenant_id=tenant_id,
            route_id=route_id,
        )
        if snapshot is not None:
            assigned_route = RoutingAssignedRouteRead.model_validate(snapshot.model_dump())
        stops = [
            RouteStopRead.model_validate(item)
            for item in list_route_stops(db, route_id=route_id)
        ]

    operations = list_route_operations(db, session_id=session.id)
    composition = build_current_composition(db, session=session)
    waybill = get_session_waybill_state(db, session=session)
    waybill_history = list_session_waybill_history(db, session=session)
    incidents = list_route_incidents(db, session_id=session.id)
    stop_progress = build_route_stop_progress(db, session=session)
    stop_results = list_route_stop_results(db, session_id=session.id)

    customers, _ = list_customers(
        db,
        tenant_id=tenant_id,
        limit=ROUTE_CONTEXT_CUSTOMER_LIMIT,
        offset=0,
    )
    warehouses = list_warehouses(db, tenant_id=tenant_id)

    return RouteContextRead(
        session=build_session_snapshot(db, session=session),
        route_detail=route_detail,
        assigned_route=assigned_route,
        stops=stops,
        operations=operations,
        composition=composition,
        waybill=waybill,
        waybill_history=waybill_history,
        incidents=incidents,
        stop_progress=stop_progress,
        stop_results=stop_results,
        customers=[_build_customer_read(item) for item in customers],
        warehouses=[WarehouseRead.model_validate(item) for item in warehouses],
    )
