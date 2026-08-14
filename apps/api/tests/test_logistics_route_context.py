from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    enable_crm_plugin,
    enable_logistics_plugin,
)


def _first_driver_id(client: TestClient, headers: dict[str, str]) -> str:
    create_response = client.post(
        "/api/v1/core/users",
        headers=headers,
        json={
            "name": "Driver Route Context",
            "email": "driver.route.context@example.com",
            "password": "ChangeMe123!",
            "branch_id": None,
            "category": "driver",
            "role_ids": [],
            "warehouse_ids": [],
        },
    )
    assert create_response.status_code == 201, create_response.text
    catalog_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    )
    assert catalog_response.status_code == 200, catalog_response.text
    return catalog_response.json()[0]["id"]


def _create_session_with_route(
    client: TestClient, app, seeded_demo: dict[str, str], *, suffix: str, with_route: bool
) -> dict:
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": f"Almacen {suffix}", "code": f"ALM-{suffix}", "address": None, "phone": None},
    ).json()
    vehicle = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": f"TRK-{suffix}",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": suffix,
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()
    driver_id = _first_driver_id(client, headers)

    route_id = None
    if with_route:
        route = client.post(
            "/api/v1/plugins/logistics/routes",
            headers=headers,
            json={
                "route_date": "2026-08-14",
                "vehicle_id": vehicle["id"],
                "origin_label": "Base",
                "destination_label": "Zona Norte",
            },
        ).json()
        route_id = route["id"]

    session_response = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
            "route_id": route_id,
        },
    )
    assert session_response.status_code == 201, session_response.text
    return {"session": session_response.json(), "warehouse": warehouse, "vehicle": vehicle}


def _disable_catalog_bootstrap_hook(monkeypatch) -> None:
    # El helper enable_logistics_plugin ya siembra los catalogos en su propia
    # sesion. El lifecycle hook del plugin abriria una segunda conexion SQLite
    # que intenta insertar las mismas filas mientras la primera tiene el lock
    # de escritura -> deadlock "database is locked" en entorno dev.
    monkeypatch.setattr(
        "plugins.logistics.backend.services.catalog_bootstrap.ensure_logistics_catalogs",
        lambda db: None,
    )


def test_route_context_returns_aggregated_data(
    client: TestClient, app, seeded_demo: dict[str, str], monkeypatch
) -> None:
    _disable_catalog_bootstrap_hook(monkeypatch)
    context = _create_session_with_route(
        client, app, seeded_demo, suffix="CTX-AGG", with_route=True
    )
    session = context["session"]
    headers = auth_headers(client)

    response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-context",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["session"]["id"] == session["id"]
    assert payload["session"]["status"] == "DRAFT"
    assert payload["route_detail"] is not None
    assert payload["route_detail"]["id"] == session["route_id"]
    assert payload["stops"] == []
    assert payload["operations"] == []
    assert payload["composition"]["session_id"] == session["id"]
    assert payload["waybill"] is not None
    assert payload["waybill_history"] == []
    assert payload["incidents"] == []
    assert payload["stop_progress"] == []
    assert payload["stop_results"] == []
    assert payload["customers"] == []
    assert any(w["id"] == context["warehouse"]["id"] for w in payload["warehouses"])


def test_route_context_session_without_route(
    client: TestClient, app, seeded_demo: dict[str, str], monkeypatch
) -> None:
    _disable_catalog_bootstrap_hook(monkeypatch)
    context = _create_session_with_route(
        client, app, seeded_demo, suffix="CTX-NOROUTE", with_route=False
    )
    session = context["session"]
    headers = auth_headers(client)

    response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-context",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["session"]["id"] == session["id"]
    assert payload["route_detail"] is None
    assert payload["assigned_route"] is None
    assert payload["stops"] == []


def test_route_context_404_for_missing_session(
    client: TestClient, app, seeded_demo: dict[str, str], monkeypatch
) -> None:
    _disable_catalog_bootstrap_hook(monkeypatch)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/session-inexistente/route-context",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Jornada no encontrada"
