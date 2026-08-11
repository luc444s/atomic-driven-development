from __future__ import annotations

from datetime import UTC, date, datetime

from apps.api.app.commands.seed_demo import seed_demo_data
from plugins.logistics.backend.models import (
    LogisticsRoute,
    LogisticsRouteCalculation,
    LogisticsRouteStop,
)
from plugins.logistics.backend.services.routing.models import (
    RoutingCalculatedStop,
    RoutingCalculationResponse,
    RoutingCommitOrderRequest,
    RoutingTotals,
)
from plugins.logistics.backend.services.routing.service import RoutingService


def test_routing_commit_order_persists_snapshot_and_reorders_stops(db_session, app) -> None:
    seeded = seed_demo_data(db_session, app.state.settings, app.state.plugin_runtime.list_results())

    route = LogisticsRoute(
        tenant_id=seeded["tenant_id"],
        branch_id=seeded["branch_id"],
        route_date=date(2026, 8, 12),
        driver_id=seeded["user_id"],
        vehicle_id=None,
        status="PLANIFICADO",
        created_by=seeded["user_id"],
    )
    db_session.add(route)
    db_session.flush()

    stop_a = LogisticsRouteStop(route_id=route.id, stop_order=1, status="PENDIENTE")
    stop_b = LogisticsRouteStop(route_id=route.id, stop_order=2, status="PENDIENTE")
    db_session.add(stop_a)
    db_session.add(stop_b)
    db_session.commit()

    payload = RoutingCommitOrderRequest(
        route_id=route.id,
        preview=RoutingCalculationResponse(
            provider_stack="osrm+vroom",
            route_id=route.id,
            ordered_stops=[
                RoutingCalculatedStop(
                    stop_id=stop_b.id,
                    sequence=1,
                    eta_at=datetime(2026, 8, 12, 9, 0, tzinfo=UTC),
                ),
                RoutingCalculatedStop(
                    stop_id=stop_a.id,
                    sequence=2,
                    eta_at=datetime(2026, 8, 12, 9, 30, tzinfo=UTC),
                ),
            ],
            totals=RoutingTotals(
                distance_m=1000,
                travel_seconds=600,
                service_seconds=300,
                total_seconds=900,
            ),
            polyline="poly-123",
        ),
    )

    response = RoutingService(app.state.settings).commit_order(
        db_session,
        tenant_id=seeded["tenant_id"],
        actor_user_id=seeded["user_id"],
        payload=payload,
    )
    db_session.commit()

    ordered = list(
        db_session.query(LogisticsRouteStop)
        .filter(LogisticsRouteStop.route_id == route.id)
        .order_by(LogisticsRouteStop.stop_order.asc())
        .all()
    )
    snapshot = db_session.get(LogisticsRouteCalculation, response.calculation_id)

    assert response.committed is True
    assert response.stop_count == 2
    assert [item.id for item in ordered] == [stop_b.id, stop_a.id]
    assert snapshot is not None
    assert snapshot.route_id == route.id
    assert snapshot.ordered_stop_ids_json == [stop_b.id, stop_a.id]
    assert snapshot.polyline == "poly-123"
