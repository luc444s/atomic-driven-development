from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_customer,
    enable_crm_plugin,
    enable_logistics_plugin,
)
from plugins.logistics.backend.services.route_context import build_route_context
from plugins.logistics.backend.services.session_console import build_session_console_context
from plugins.logistics.backend.services.sessions import list_vehicle_sessions
from plugins.logistics.backend.services.snapshots import build_session_list_items

# Presupuestos de queries (regresion anti N+1). Margen 2x sobre lo medido
# con 3 sesiones en SQLite para absorber datos sinteticos.
LIST_BUDGET_BASE = 10
LIST_BUDGET_PER_SESSION = 4
CONSOLE_BUDGET = 80
ROUTE_CONTEXT_BUDGET = 60


def _first_driver_id(client: TestClient, headers: dict[str, str]) -> str:
    client.post(
        "/api/v1/core/users",
        headers=headers,
        json={
            "name": "Driver Budget",
            "email": "driver.budget@example.com",
            "password": "ChangeMe123!",
            "branch_id": None,
            "category": "driver",
            "role_ids": [],
            "warehouse_ids": [],
        },
    )
    catalog_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    )
    return catalog_response.json()[0]["id"]


def _disable_catalog_bootstrap_hook(monkeypatch) -> None:
    monkeypatch.setattr(
        "plugins.logistics.backend.services.catalog_bootstrap.ensure_logistics_catalogs",
        lambda db: None,
    )


def _create_sessions(
    client: TestClient, app, seeded_demo: dict[str, str], *, count: int
) -> None:
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    create_customer(client, headers, name="Cliente Budget", document_number="20100070970")
    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Budget", "code": "ALM-BUD", "address": None, "phone": None},
    ).json()
    driver_id = _first_driver_id(client, headers)

    for index in range(count):
        vehicle = client.post(
            "/api/v1/plugins/logistics/vehicles",
            headers=headers,
            json={
                "plate": f"TRK-BUD-{index}",
                "vehicle_type": "Camion",
                "brand": "Test",
                "model": f"Budget{index}",
                "capacity_weight": 2000,
                "useful_load": 2000,
                "warehouse_id": warehouse["id"],
            },
        ).json()
        response = client.post(
            "/api/v1/plugins/logistics/vehicle-sessions",
            headers=headers,
            json={
                "vehicle_id": vehicle["id"],
                "driver_id": driver_id,
                "origin_warehouse_id": warehouse["id"],
                "route_id": None,
            },
        )
        assert response.status_code == 201, response.text


def _counter_for(app):
    session_factory = app.state.session_factory
    engine = session_factory.kw["bind"]
    counter = {"count": 0}

    def _on_execute(*args, **kwargs) -> None:
        counter["count"] += 1

    event.listen(engine, "after_cursor_execute", _on_execute)
    return counter


def test_query_budgets_for_jornadas_flows(
    client: TestClient, app, seeded_demo: dict[str, str], monkeypatch
) -> None:
    _disable_catalog_bootstrap_hook(monkeypatch)
    _create_sessions(client, app, seeded_demo, count=3)

    tenant_id = seeded_demo["tenant_id"]
    counter = _counter_for(app)

    def _load_sessions(db: Session):
        sessions, _ = list_vehicle_sessions(
            db, tenant_id=tenant_id, status=None, active_only=False, page=1, per_page=50
        )
        return sessions

    with app.state.session_factory() as db:
        sessions = _load_sessions(db)
        assert len(sessions) == 3
        build_session_list_items(db, sessions=sessions)
        build_session_console_context(db, tenant_id=tenant_id, session_id=sessions[0].id)
        build_route_context(db, tenant_id=tenant_id, session_id=sessions[0].id)
        counter["count"] = 0

        items = build_session_list_items(db, sessions=sessions)
        list_queries = counter["count"]
        assert list_queries <= LIST_BUDGET_BASE + LIST_BUDGET_PER_SESSION * len(items), (
            f"Lista disparo {list_queries} queries (presupuesto "
            f"{LIST_BUDGET_BASE + LIST_BUDGET_PER_SESSION * len(items)})"
        )

        counter["count"] = 0
        console = build_session_console_context(
            db, tenant_id=tenant_id, session_id=sessions[0].id
        )
        console_queries = counter["count"]
        assert console.session.id == sessions[0].id
        assert console_queries <= CONSOLE_BUDGET, (
            f"Console disparo {console_queries} queries (presupuesto {CONSOLE_BUDGET})"
        )

        counter["count"] = 0
        route = build_route_context(db, tenant_id=tenant_id, session_id=sessions[0].id)
        route_queries = counter["count"]
        assert route.session.id == sessions[0].id
        assert route_queries <= ROUTE_CONTEXT_BUDGET, (
            f"Route context disparo {route_queries} queries (presupuesto {ROUTE_CONTEXT_BUDGET})"
        )
