from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
    enable_stock_plugin,
)
from plugins.logistics.backend.models import LogisticsVehicleSession
from plugins.logistics.backend.services.rules import get_next_transition_blocker


def _build_session(
    status: str, *, loaded_weight_kg: float | None = None
) -> LogisticsVehicleSession:
    return LogisticsVehicleSession(
        tenant_id="tenant-test",
        branch_id="branch-test",
        vehicle_id="vehicle-test",
        driver_id="driver-test",
        origin_warehouse_id="warehouse-origin",
        mobile_warehouse_id="warehouse-mobile",
        status=status,
        loaded_weight_kg=loaded_weight_kg,
        created_by="user-test",
        updated_by="user-test",
    )


def test_get_next_transition_blocker_covers_all_statuses() -> None:
    assert get_next_transition_blocker(_build_session("DRAFT")) is None
    assert (
        get_next_transition_blocker(_build_session("LOADING"))
        == "La jornada necesita carga confirmada antes de quedar lista"
    )
    assert get_next_transition_blocker(_build_session("LOADING", loaded_weight_kg=5)) is None
    assert get_next_transition_blocker(_build_session("READY_TO_DEPART")) is None
    assert get_next_transition_blocker(_build_session("OUTBOUND")) is None
    assert get_next_transition_blocker(_build_session("RETURNING")) is None
    assert (
        get_next_transition_blocker(_build_session("AWAITING_RECONCILIATION"))
        == "La jornada no tiene conciliacion registrada"
    )
    assert (
        get_next_transition_blocker(
            _build_session("AWAITING_RECONCILIATION"),
            reconciliation_status="HAS_DIFF",
        )
        == "La jornada solo puede cerrarse cuando la conciliacion esta MATCHED"
    )
    assert (
        get_next_transition_blocker(
            _build_session("AWAITING_RECONCILIATION"),
            reconciliation_status="MATCHED",
            has_open_discrepancies=True,
        )
        == "No se puede cerrar con discrepancias abiertas"
    )
    assert get_next_transition_blocker(
        _build_session("AWAITING_RECONCILIATION"),
        reconciliation_status="MATCHED",
    ) is None
    assert (
        get_next_transition_blocker(_build_session("CLOSED"))
        == "La jornada ya no puede modificarse"
    )
    assert (
        get_next_transition_blocker(_build_session("CANCELLED"))
        == "La jornada ya no puede modificarse"
    )


def test_vehicle_session_load_cycle(client: TestClient, app, seeded_demo: dict[str, str]) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Central V1", "code": "ALM-V1", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-V1",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "V1",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="V1-GLP10", name="Bombona 10kg V1")

    adjust_response = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "reason": "Stock inicial jornada V1",
            "idempotency_key": "test-v1-stock-seed",
        },
    )
    assert adjust_response.status_code == 201, adjust_response.text

    drivers_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    )
    assert drivers_response.status_code == 200, drivers_response.text
    driver_id = drivers_response.json()[0]["id"]

    create_session_response = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    )
    assert create_session_response.status_code == 201, create_session_response.text
    session = create_session_response.json()
    assert session["status"] == "DRAFT"
    assert session["mobile_warehouse_id"]
    assert session["next_transition_allowed"] is True
    assert session["next_transition_blocker"] is None

    start_loading_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    )
    assert start_loading_response.status_code == 200, start_loading_response.text
    loading_session = start_loading_response.json()
    assert loading_session["status"] == "LOADING"
    assert loading_session["next_transition_allowed"] is False
    assert (
        loading_session["next_transition_blocker"]
        == "La jornada necesita carga confirmada antes de quedar lista"
    )

    upsert_plan_response = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-plan",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "planned_quantity": 5,
                    "source_warehouse_id": warehouse["id"],
                }
            ]
        },
    )
    assert upsert_plan_response.status_code == 200, upsert_plan_response.text
    assert len(upsert_plan_response.json()["items"]) == 1

    confirm_load_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-load",
        headers=headers,
        json={},
    )
    assert confirm_load_response.status_code == 200, confirm_load_response.text

    ready_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/ready",
        headers=headers,
    )
    assert ready_response.status_code == 200, ready_response.text
    ready_session = ready_response.json()
    assert ready_session["status"] == "READY_TO_DEPART"
    assert ready_session["loaded_weight_kg"] is not None
    assert ready_session["current_stock"]["total_units"] == 5
    assert ready_session["next_transition_allowed"] is True
    assert ready_session["next_transition_blocker"] is None
