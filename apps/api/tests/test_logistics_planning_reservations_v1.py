from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
    enable_stock_plugin,
)


def _setup_vehicle(client: TestClient, headers: dict[str, str]) -> tuple[dict, dict, str]:
    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Planning", "code": "ALM-PLN", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-PLN",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "Planning",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    drivers_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    )
    assert drivers_response.status_code == 200, drivers_response.text
    driver_id = drivers_response.json()[0]["id"]
    return warehouse, vehicle, driver_id


def _reservation_payload(*, warehouse_id: str, vehicle_id: str, driver_id: str, start_at: datetime):
    end_at = start_at + timedelta(hours=2)
    return {
        "vehicle_id": vehicle_id,
        "origin_warehouse_id": warehouse_id,
        "planned_start_at": start_at.isoformat(),
        "planned_end_at": end_at.isoformat(),
        "driver_id": driver_id,
        "expected_load_summary": {
            "total_products": 2,
            "total_units": 10,
            "total_weight_kg": 450,
        },
        "expected_weight_total": 450,
        "notes": "Reserva de prueba",
    }


def test_planning_reservation_marks_overlap_as_conflict(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)
    warehouse, vehicle, driver_id = _setup_vehicle(client, headers)

    start_at = datetime.now(UTC) + timedelta(days=1)
    first_response = client.post(
        "/api/v1/plugins/logistics/planning/reservations",
        headers=headers,
        json=_reservation_payload(
            warehouse_id=warehouse["id"],
            vehicle_id=vehicle["id"],
            driver_id=driver_id,
            start_at=start_at,
        ),
    )
    assert first_response.status_code == 201, first_response.text
    assert first_response.json()["status"] == "READY"

    second_response = client.post(
        "/api/v1/plugins/logistics/planning/reservations",
        headers=headers,
        json=_reservation_payload(
            warehouse_id=warehouse["id"],
            vehicle_id=vehicle["id"],
            driver_id=driver_id,
            start_at=start_at + timedelta(minutes=30),
        ),
    )
    assert second_response.status_code == 201, second_response.text
    second_reservation = second_response.json()
    assert second_reservation["status"] == "CONFLICT"
    assert second_reservation["conflict_reason"] == "TIME_OVERLAP"


def test_activate_planning_reservation_creates_pending_session_when_vehicle_is_busy(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)
    warehouse, vehicle, driver_id = _setup_vehicle(client, headers)

    session_response = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    )
    assert session_response.status_code == 201, session_response.text
    active_session = session_response.json()

    start_loading_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{active_session['id']}/start-loading",
        headers=headers,
    )
    assert start_loading_response.status_code == 200, start_loading_response.text
    assert start_loading_response.json()["status"] == "LOADING"

    reservation_response = client.post(
        "/api/v1/plugins/logistics/planning/reservations",
        headers=headers,
        json=_reservation_payload(
            warehouse_id=warehouse["id"],
            vehicle_id=vehicle["id"],
            driver_id=driver_id,
            start_at=datetime.now(UTC) + timedelta(days=1),
        ),
    )
    assert reservation_response.status_code == 201, reservation_response.text
    reservation = reservation_response.json()

    activate_response = client.post(
        f"/api/v1/plugins/logistics/planning/reservations/{reservation['id']}/activate",
        headers=headers,
    )
    assert activate_response.status_code == 200, activate_response.text
    activated_reservation = activate_response.json()
    assert activated_reservation["linked_session_id"] is not None
    assert activated_reservation["status"] == "READY"

    sessions_response = client.get("/api/v1/plugins/logistics/vehicle-sessions", headers=headers)
    assert sessions_response.status_code == 200, sessions_response.text
    sessions = sessions_response.json()
    assert len([item for item in sessions if item["vehicle_id"] == vehicle["id"]]) == 2
    statuses = {item["status"] for item in sessions if item["vehicle_id"] == vehicle["id"]}
    assert statuses == {"LOADING", "DRAFT"}
