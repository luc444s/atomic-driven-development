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
            "name": "Driver Console",
            "email": "driver.console@example.com",
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


def _disable_catalog_bootstrap_hook(monkeypatch) -> None:
    # El helper enable_logistics_plugin ya siembra los catalogos en su propia
    # sesion. El lifecycle hook abriria una segunda conexion SQLite con el
    # mismo write lock -> deadlock "database is locked" en entorno dev.
    monkeypatch.setattr(
        "plugins.logistics.backend.services.catalog_bootstrap.ensure_logistics_catalogs",
        lambda db: None,
    )


def _create_session(client: TestClient, app, seeded_demo: dict[str, str]) -> dict:
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Console", "code": "ALM-CON", "address": None, "phone": None},
    ).json()
    vehicle = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-CONSOLE",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "Console",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()
    driver_id = _first_driver_id(client, headers)

    session_response = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
            "route_id": None,
        },
    )
    assert session_response.status_code == 201, session_response.text
    return {"session": session_response.json(), "warehouse": warehouse}


def test_console_context_returns_aggregated_data(
    client: TestClient, app, seeded_demo: dict[str, str], monkeypatch
) -> None:
    _disable_catalog_bootstrap_hook(monkeypatch)
    context = _create_session(client, app, seeded_demo)
    session = context["session"]
    headers = auth_headers(client)

    response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/console-context",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()

    assert payload["session"]["id"] == session["id"]
    assert payload["session"]["status"] == "DRAFT"
    assert payload["load_plan"]["session_id"] == session["id"]
    assert payload["load_plan"]["status"] == "DRAFT"
    assert payload["load_plan"]["items"] == []
    assert payload["reconciliation"]["session_id"] == session["id"]
    assert payload["operational_summary"]["session_id"] == session["id"]
    assert payload["origin_balances"]["total"] >= 0
    assert payload["mobile_balances"]["total"] >= 0
    assert payload["origin_serialized"] == []


def test_console_context_404_for_missing_session(
    client: TestClient, app, seeded_demo: dict[str, str], monkeypatch
) -> None:
    _disable_catalog_bootstrap_hook(monkeypatch)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/session-inexistente/console-context",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Jornada no encontrada"
