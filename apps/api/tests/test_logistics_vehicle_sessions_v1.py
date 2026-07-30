from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_customer,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
    enable_stock_plugin,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsLoadSerialAssignment,
    LogisticsVehicleSession,
)
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
            "unit_cost": 5.0,
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

    ready_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    )
    assert ready_response.status_code == 200, ready_response.text
    ready_session = ready_response.json()
    assert ready_session["status"] == "READY_TO_DEPART"
    assert ready_session["loaded_weight_kg"] is not None
    assert ready_session["current_stock"]["total_units"] == 5
    assert ready_session["next_transition_allowed"] is True
    assert ready_session["next_transition_blocker"] is None


def test_pending_draft_session_cannot_start_before_its_turn(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Cola", "code": "ALM-COLA", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-COLA",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "Queue",
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

    first_session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()
    second_session_response = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    )
    assert second_session_response.status_code == 201, second_session_response.text
    second_session = second_session_response.json()

    second_detail = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{second_session['id']}",
        headers=headers,
    )
    assert second_detail.status_code == 200, second_detail.text
    second_snapshot = second_detail.json()
    assert second_snapshot["status"] == "DRAFT"
    assert second_snapshot["next_transition_allowed"] is False
    assert (
        second_snapshot["next_transition_blocker"]
        == "La jornada está pendiente en cola y no puede iniciar hasta que le toque su turno"
    )

    blocked_start = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{second_session['id']}/start-loading",
        headers=headers,
    )
    assert blocked_start.status_code == 400, blocked_start.text
    assert blocked_start.json()["detail"] == (
        "La jornada está pendiente en cola y no puede iniciar hasta que le toque su turno"
    )

    first_start = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{first_session['id']}/start-loading",
        headers=headers,
    )
    assert first_start.status_code == 200, first_start.text


def test_operational_summary_marks_route_gap_when_departed_without_route(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Summary", "code": "ALM-SUM", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-SUM",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "SUM",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="SUM-GLP10", name="Bombona 10kg SUM")

    adjust_response = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial summary",
            "idempotency_key": "test-summary-stock-seed",
        },
    )
    assert adjust_response.status_code == 201, adjust_response.text

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]

    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200
    assert client.put(
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
    ).status_code == 200
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    ).status_code == 200
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    ).status_code == 200

    summary_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/operational-summary",
        headers=headers,
    )
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["health_status"] == "ATTENTION"
    assert summary["data_completeness"] == "PARTIAL"
    assert summary["blocking_reasons"] == ["NO_ROUTE_ASSIGNED"]
    assert summary["stop_counters"]["total"] == 0
    assert summary["waybill"]["sync_status"] == "MISSING"


def test_load_serials_are_required_and_block_duplicate_selection(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Seriales", "code": "ALM-LS", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-LS",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "LS",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()
    vehicle_two = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-LS2",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "LS2",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()

    product = create_product(client, headers, sku="LS-GLP10", name="Bombona 10kg LS")

    adjust_response = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial seriales",
            "idempotency_key": "test-load-serial-stock-seed",
        },
    )
    assert adjust_response.status_code == 201, adjust_response.text

    with app.state.session_factory() as db:
        cylinder = LogisticsCylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="LS-000001",
            current_state="LLENADO_OK",
            product_id=product["id"],
            location=f"{warehouse['code']} patio norte",
            is_active=True,
        )
        db.add(cylinder)
        db.commit()
        cylinder_id = cylinder.id

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]

    session_one = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_one['id']}/start-loading",
        headers=headers,
    ).status_code == 200
    load_plan = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_one['id']}/load-plan",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "planned_quantity": 1,
                    "source_warehouse_id": warehouse["id"],
                }
            ]
        },
    )
    assert load_plan.status_code == 200, load_plan.text
    assert load_plan.json()["items"][0]["requires_serials"] is True
    assert load_plan.json()["items"][0]["serials_complete"] is False

    confirm_missing_serial = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_one['id']}/confirm-and-ready",
        headers=headers,
        json={},
    )
    assert confirm_missing_serial.status_code == 400, confirm_missing_serial.text

    select_serial = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_one['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "serial": "LS-000001",
        },
    )
    assert select_serial.status_code == 200, select_serial.text
    assignment = select_serial.json()
    assert assignment["assignment_status"] == "SELECTED"
    assert assignment["cylinder_id"] == cylinder_id

    idempotent_select = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_one['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "serial": "LS-000001",
        },
    )
    assert idempotent_select.status_code == 200, idempotent_select.text
    assert idempotent_select.json()["id"] == assignment["id"]

    session_two = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle_two["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_two['id']}/start-loading",
        headers=headers,
    ).status_code == 200
    assert client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_two['id']}/load-plan",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "planned_quantity": 1,
                    "source_warehouse_id": warehouse["id"],
                }
            ]
        },
    ).status_code == 200

    duplicate_select = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_two['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "serial": "LS-000001",
        },
    )
    assert duplicate_select.status_code == 400, duplicate_select.text


def test_load_serials_confirm_and_release_on_cancel(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Seriales 2", "code": "ALM-L2", "address": None, "phone": None},
    ).json()
    vehicle = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-L2",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "L2",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()
    vehicle_cancel = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-L3",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "L3",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()
    product = create_product(client, headers, sku="L2-GLP10", name="Bombona 10kg L2")
    assert client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial seriales 2",
            "idempotency_key": "test-load-serial-stock-seed-2",
        },
    ).status_code == 201

    with app.state.session_factory() as db:
        cylinder = LogisticsCylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="L2-000001",
            current_state="LLENADO_OK",
            product_id=product["id"],
            location=f"{warehouse['code']} patio norte",
            is_active=True,
        )
        db.add(cylinder)
        db.commit()
        cylinder_id = cylinder.id

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]
    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200
    assert client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-plan",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "planned_quantity": 1,
                    "source_warehouse_id": warehouse["id"],
                }
            ]
        },
    ).status_code == 200
    assert client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "serial": "L2-000001",
        },
    ).status_code == 200

    ready_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    )
    assert ready_response.status_code == 200, ready_response.text
    assert ready_response.json()["status"] == "READY_TO_DEPART"

    cylinder_after_confirm = client.get(
        f"/api/v1/plugins/logistics/cylinders/{cylinder_id}",
        headers=headers,
    )
    assert cylinder_after_confirm.status_code == 200, cylinder_after_confirm.text
    assert cylinder_after_confirm.json()["current_state"] == "CARGA_EN_VEHICULO"

    selected_after_confirm = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/selected?product_id={product['id']}",
        headers=headers,
    )
    assert selected_after_confirm.status_code == 200, selected_after_confirm.text
    assert selected_after_confirm.json()[0]["assignment_status"] == "CONFIRMED"
    assert selected_after_confirm.json()[0]["confirmed_by_operation_id"]

    depart_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    )
    assert depart_response.status_code == 200, depart_response.text

    cylinder_on_route = client.get(
        f"/api/v1/plugins/logistics/cylinders/{cylinder_id}",
        headers=headers,
    )
    assert cylinder_on_route.status_code == 200, cylinder_on_route.text
    assert cylinder_on_route.json()["current_state"] == "EN_RUTA"

    session_cancel = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle_cancel["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_cancel['id']}/start-loading",
        headers=headers,
    ).status_code == 200
    assert client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_cancel['id']}/load-plan",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "planned_quantity": 1,
                    "source_warehouse_id": warehouse["id"],
                }
            ]
        },
    ).status_code == 200

    with app.state.session_factory() as db:
        cylinder_cancel = LogisticsCylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="L2-000002",
            current_state="LLENADO_OK",
            product_id=product["id"],
            location=f"{warehouse['code']} patio norte",
            is_active=True,
        )
        db.add(cylinder_cancel)
        db.commit()

    assert client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_cancel['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "serial": "L2-000002",
        },
    ).status_code == 200

    cancel_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_cancel['id']}/cancel",
        headers=headers,
        json={"notes": "Anulada antes de salir"},
    )
    assert cancel_response.status_code == 200, cancel_response.text
    assert cancel_response.json()["status"] == "CANCELLED"

    with app.state.session_factory() as db:
        assignment = db.execute(
            select(LogisticsLoadSerialAssignment).where(
                LogisticsLoadSerialAssignment.session_id == session_cancel["id"]
            )
        ).scalar_one()
        assert assignment.assignment_status == "RELEASED"
        assert assignment.release_reason == "OPERATION_CANCELLED"


def test_load_serial_search_shows_other_product_as_unavailable(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Search UX", "code": "ALM-SX", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-SX",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "SX",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product_a = create_product(client, headers, sku="SX-A", name="Bombona Search A")
    product_b = create_product(client, headers, sku="SX-B", name="Bombona Search B")

    with app.state.session_factory() as db:
        cylinder = LogisticsCylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="SX-000001",
            current_state="LLENADO_OK",
            product_id=product_a["id"],
            location=f"{warehouse['code']} patio norte",
            is_active=True,
        )
        db.add(cylinder)
        db.commit()

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]
    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()

    search_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/search",
        headers=headers,
        params={
            "product_id": product_b["id"],
            "source_warehouse_id": warehouse["id"],
            "query": "SX-000001",
        },
    )
    assert search_response.status_code == 200, search_response.text
    payload = search_response.json()
    assert len(payload) == 1
    assert payload[0]["serial"] == "SX-000001"
    assert payload[0]["availability_status"] == "UNAVAILABLE"
    assert payload[0]["context_label"] == "Corresponde a otro producto"


def test_load_serial_search_supports_numeric_lookup_inside_prefixed_serial(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Numeric Search", "code": "ALM-NS", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-NS",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "NS",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="NS-GLP10", name="Bombona Numeric Search")

    with app.state.session_factory() as db:
        cylinder = LogisticsCylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="BOMBONA1-LUCAS-000200",
            current_state="LLENADO_OK",
            product_id=product["id"],
            gas_group_id=product["id"],
            location=f"{warehouse['code']} patio norte",
            is_active=True,
        )
        db.add(cylinder)
        db.commit()

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]
    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()

    search_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/search",
        headers=headers,
        params={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "query": "0200",
        },
    )
    assert search_response.status_code == 200, search_response.text
    payload = search_response.json()
    assert len(payload) == 1
    assert payload[0]["serial"] == "BOMBONA1-LUCAS-000200"
    assert payload[0]["availability_status"] == "AVAILABLE"

    select_response = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "serial": "0200",
        },
    )
    assert select_response.status_code == 200, select_response.text
    assert select_response.json()["cylinder_serial"] == "BOMBONA1-LUCAS-000200"


def test_confirm_and_ready_blocks_origin_line_without_positive_quantity(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Cantidad", "code": "ALM-CQ", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-CQ",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "CQ",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="CQ-GLP10", name="Bombona 10kg CQ")
    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]

    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
        },
    ).json()
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200

    load_plan_response = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-plan",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "planned_quantity": 0,
                    "source_warehouse_id": warehouse["id"],
                }
            ]
        },
    )
    assert load_plan_response.status_code == 400, load_plan_response.text
    assert "cantidad debe ser mayor que cero" in load_plan_response.json()["detail"]


def test_vehicle_session_reconciliation_auto_closes(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Recon Auto", "code": "ALM-RA", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-RA",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "RA",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="RA-GLP10", name="Bombona 10kg RA")

    adjust_response = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial jornada auto close",
            "idempotency_key": "test-auto-close-stock-seed",
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

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200

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

    ready_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    )
    assert ready_response.status_code == 200, ready_response.text
    assert ready_response.json()["status"] == "READY_TO_DEPART"

    depart_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    )
    assert depart_response.status_code == 200, depart_response.text

    returning_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/mark-returning",
        headers=headers,
    )
    assert returning_response.status_code == 200, returning_response.text
    assert returning_response.json()["status"] == "AWAITING_RECONCILIATION"

    reconciliation_view_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/reconciliation",
        headers=headers,
    )
    assert reconciliation_view_response.status_code == 200, reconciliation_view_response.text
    reconciliation_view = reconciliation_view_response.json()
    assert len(reconciliation_view["lines"]) == 1
    assert reconciliation_view["lines"][0]["expected_quantity"] == 5.0

    count_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/reconciliation/count",
        headers=headers,
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "counted_quantity": 5,
                }
            ]
        },
    )
    assert count_response.status_code == 200, count_response.text
    reconciliation = count_response.json()
    assert reconciliation["status"] == "CLOSED"

    detail_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}",
        headers=headers,
    )
    assert detail_response.status_code == 200, detail_response.text
    closed_session = detail_response.json()
    assert closed_session["status"] == "CLOSED"
    assert closed_session["closed_at"] is not None


def test_vehicle_session_waybill_is_available_inside_jornada(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Carta Porte", "code": "ALM-CP", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-CP",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "CP",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="CP-GLP10", name="Bombona 10kg CP")

    adjust_response = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial carta porte",
            "idempotency_key": "test-waybill-stock-seed",
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

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200

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

    ready_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    )
    assert ready_response.status_code == 200, ready_response.text

    depart_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    )
    assert depart_response.status_code == 200, depart_response.text

    state_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte",
        headers=headers,
    )
    assert state_response.status_code == 200, state_response.text
    initial_state = state_response.json()
    assert initial_state["active"] is None
    assert initial_state["can_regenerate"] is True

    regenerate_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Generación inicial en ruta",
            "event": "INITIAL_GENERATION",
            "idempotency_key": "test-session-waybill-v1",
        },
    )
    assert regenerate_response.status_code == 200, regenerate_response.text
    regenerated_state = regenerate_response.json()
    assert regenerated_state["sync_status"] == "SYNCED"
    assert regenerated_state["active"] is not None
    assert regenerated_state["active"]["version"] == 1
    assert regenerated_state["active"]["snapshot"]["vehicle"]["plate"] == "TRK-CP"
    assert regenerated_state["active"]["snapshot"]["transported_items"][0]["quantity"] == 5.0

    retry_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Generación inicial en ruta",
            "event": "INITIAL_GENERATION",
            "idempotency_key": "test-session-waybill-v1",
        },
    )
    assert retry_response.status_code == 200, retry_response.text
    retried_state = retry_response.json()
    assert retried_state["active"]["version"] == 1

    history_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/history",
        headers=headers,
    )
    assert history_response.status_code == 200, history_response.text
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["version"] == 1


def test_route_operation_changes_composition_and_outdates_waybill(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    customer = create_customer(
        client,
        headers,
        name="Cliente Ruta Carta Porte",
        document_number="20100070970",
    )

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Ruta", "code": "ALM-RO", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    zone_response = client.post(
        "/api/v1/plugins/logistics/zones",
        headers=headers,
        json={"name": "Zona Ruta", "code": "ZN-RO"},
    )
    assert zone_response.status_code == 201, zone_response.text
    zone = zone_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-RO",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "RO",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    delivery_point_response = client.post(
        "/api/v1/plugins/logistics/delivery-points",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "contact_name": "Operador Ruta",
            "address": "Calle Ruta 123",
            "zone_id": zone["id"],
            "warehouse_id": warehouse["id"],
            "is_primary": True,
        },
    )
    assert delivery_point_response.status_code == 201, delivery_point_response.text
    delivery_point = delivery_point_response.json()

    route_response = client.post(
        "/api/v1/plugins/logistics/routes",
        headers=headers,
        json={
            "route_date": datetime.now(UTC).date().isoformat(),
            "vehicle_id": vehicle["id"],
        },
    )
    assert route_response.status_code == 201, route_response.text
    route = route_response.json()

    stop_response = client.post(
        f"/api/v1/plugins/logistics/routes/{route['id']}/stops",
        headers=headers,
        json={"delivery_point_id": delivery_point["id"], "stop_order": 1},
    )
    assert stop_response.status_code == 201, stop_response.text
    stop = stop_response.json()

    product = create_product(client, headers, sku="RO-GLP10", name="Bombona 10kg RO")

    adjust_response = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial ruta operation",
            "idempotency_key": "test-route-operation-stock-seed",
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
            "route_id": route["id"],
        },
    )
    assert create_session_response.status_code == 201, create_session_response.text
    session = create_session_response.json()

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200

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

    ready_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    )
    assert ready_response.status_code == 200, ready_response.text

    depart_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    )
    assert depart_response.status_code == 200, depart_response.text

    summary_before_waybill = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/operational-summary",
        headers=headers,
    )
    assert summary_before_waybill.status_code == 200, summary_before_waybill.text
    assert summary_before_waybill.json()["health_status"] == "BLOCKED"
    assert summary_before_waybill.json()["data_completeness"] == "PARTIAL"
    assert summary_before_waybill.json()["blocking_reasons"] == ["WAYBILL_MISSING"]
    assert summary_before_waybill.json()["waybill"]["sync_status"] == "MISSING"

    generate_waybill_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Generación inicial en ruta",
            "event": "INITIAL_GENERATION",
            "idempotency_key": "test-route-op-waybill-v1",
        },
    )
    assert generate_waybill_response.status_code == 200, generate_waybill_response.text
    assert generate_waybill_response.json()["active"]["version"] == 1

    route_operation_create_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "operation_type": "DELIVERY",
            "notes": "Entrega parcial al cliente",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                    "direction": "OUT",
                }
            ],
        },
    )
    assert route_operation_create_response.status_code == 200, route_operation_create_response.text
    route_operation = route_operation_create_response.json()
    assert route_operation["status"] == "DRAFT"

    route_operation_confirm_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/{route_operation['id']}/confirm",
        headers=headers,
    )
    assert (
        route_operation_confirm_response.status_code == 200
    ), route_operation_confirm_response.text
    confirmed_operation = route_operation_confirm_response.json()
    assert confirmed_operation["status"] == "CONFIRMED"
    assert len(confirmed_operation["movement_ids"]) == 1

    operations_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations",
        headers=headers,
    )
    assert operations_response.status_code == 200, operations_response.text
    assert operations_response.json()[0]["status"] == "CONFIRMED"

    composition_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition_response.status_code == 200, composition_response.text
    composition = composition_response.json()
    assert composition["product_lines"][0]["quantity"] == 3.0

    waybill_state_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte",
        headers=headers,
    )
    assert waybill_state_response.status_code == 200, waybill_state_response.text
    assert waybill_state_response.json()["sync_status"] == "OUTDATED"

    summary_outdated_waybill = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/operational-summary",
        headers=headers,
    )
    assert summary_outdated_waybill.status_code == 200, summary_outdated_waybill.text
    outdated_summary = summary_outdated_waybill.json()
    assert outdated_summary["health_status"] == "ATTENTION"
    assert outdated_summary["data_completeness"] == "FULL"
    assert outdated_summary["attention_reasons"] == ["WAYBILL_OUTDATED"]
    assert outdated_summary["waybill"]["sync_status"] == "OUTDATED"
    assert outdated_summary["stop_counters"]["completed"] == 1
    assert outdated_summary["incidents"]["open_total"] == 0

    regenerate_waybill_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Entrega parcial en ruta",
            "event": "MOVEMENT_CHANGED",
            "idempotency_key": "test-route-op-waybill-v2",
        },
    )
    assert regenerate_waybill_response.status_code == 200, regenerate_waybill_response.text
    regenerated_state = regenerate_waybill_response.json()
    assert regenerated_state["sync_status"] == "SYNCED"
    assert regenerated_state["active"]["version"] == 2
    assert regenerated_state["active"]["snapshot"]["transported_items"][0]["quantity"] == 3.0


def test_exchange_incident_and_route_stop_progress(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    customer = create_customer(
        client,
        headers,
        name="Cliente Exchange Ruta",
        document_number="20100070970",
    )

    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Exchange", "code": "ALM-EX", "address": None, "phone": None},
    ).json()
    zone = client.post(
        "/api/v1/plugins/logistics/zones",
        headers=headers,
        json={"name": "Zona Exchange", "code": "ZN-EX"},
    ).json()
    vehicle = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-EX",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "EX",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()
    delivery_point = client.post(
        "/api/v1/plugins/logistics/delivery-points",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "contact_name": "Operador Exchange",
            "address": "Calle Exchange 123",
            "zone_id": zone["id"],
            "warehouse_id": warehouse["id"],
            "is_primary": True,
        },
    ).json()
    route = client.post(
        "/api/v1/plugins/logistics/routes",
        headers=headers,
        json={
            "route_date": datetime.now(UTC).date().isoformat(),
            "vehicle_id": vehicle["id"],
        },
    ).json()
    stop = client.post(
        f"/api/v1/plugins/logistics/routes/{route['id']}/stops",
        headers=headers,
        json={"delivery_point_id": delivery_point["id"], "stop_order": 1},
    ).json()

    product = create_product(client, headers, sku="EX-GLP10", name="Bombona 10kg EX")

    stock_seed = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial exchange",
            "idempotency_key": "test-exchange-stock-seed",
        },
    )
    assert stock_seed.status_code == 201, stock_seed.text

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]

    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
            "route_id": route["id"],
        },
    ).json()

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200

    load_plan = client.put(
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
    assert load_plan.status_code == 200, load_plan.text

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    ).status_code == 200
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    ).status_code == 200

    exchange_create = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/exchange",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "notes": "Intercambio guiado",
            "delivered_lines": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                }
            ],
            "picked_up_lines": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                }
            ],
        },
    )
    assert exchange_create.status_code == 200, exchange_create.text
    exchange_operation = exchange_create.json()
    assert exchange_operation["operation_type"] == "EXCHANGE"
    assert exchange_operation["status"] == "DRAFT"
    assert len(exchange_operation["items"]) == 2

    stop_progress_before_confirm = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress_before_confirm.status_code == 200, stop_progress_before_confirm.text
    assert stop_progress_before_confirm.json()[0]["progress_status"] == "IN_PROGRESS"

    exchange_confirm = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/{exchange_operation['id']}/confirm",
        headers=headers,
    )
    assert exchange_confirm.status_code == 200, exchange_confirm.text
    confirmed_exchange = exchange_confirm.json()
    assert confirmed_exchange["status"] == "CONFIRMED"
    assert len(confirmed_exchange["movement_ids"]) == 2

    composition = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition.status_code == 200, composition.text
    assert composition.json()["product_lines"][0]["quantity"] == 4.0

    stop_progress_after_confirm = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress_after_confirm.status_code == 200, stop_progress_after_confirm.text
    assert stop_progress_after_confirm.json()[0]["progress_status"] == "COMPLETED"

    incident_create = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "related_operation_id": exchange_operation["id"],
            "type": "QUANTITY_MISMATCH",
            "notes": "Faltó una unidad por confirmar",
        },
    )
    assert incident_create.status_code == 200, incident_create.text
    incident = incident_create.json()
    assert incident["status"] == "OPEN"

    incidents = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents",
        headers=headers,
    )
    assert incidents.status_code == 200, incidents.text
    assert len(incidents.json()) == 1

    stop_progress_partial = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress_partial.status_code == 200, stop_progress_partial.text
    assert stop_progress_partial.json()[0]["progress_status"] == "PARTIAL"
    assert stop_progress_partial.json()[0]["open_incidents"] == 1

    incident_resolve = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents/{incident['id']}/resolve",
        headers=headers,
        json={"notes": "Validado en calle"},
    )
    assert incident_resolve.status_code == 200, incident_resolve.text
    assert incident_resolve.json()["status"] == "RESOLVED"

    composition_after_resolve = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition_after_resolve.status_code == 200, composition_after_resolve.text
    assert composition_after_resolve.json()["product_lines"][0]["quantity"] == 4.0

    stop_progress_resolved = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress_resolved.status_code == 200, stop_progress_resolved.text
    assert stop_progress_resolved.json()[0]["progress_status"] == "COMPLETED"

    corrective_incident_create = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "related_operation_id": exchange_operation["id"],
            "type": "EXCESS_DELIVERY",
            "notes": "Se entregó una unidad de más",
        },
    )
    assert corrective_incident_create.status_code == 200, corrective_incident_create.text
    corrective_incident = corrective_incident_create.json()
    assert corrective_incident["status"] == "OPEN"

    stop_progress_open_correction = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress_open_correction.status_code == 200, stop_progress_open_correction.text
    assert stop_progress_open_correction.json()[0]["progress_status"] == "PARTIAL"

    corrective_resolution = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents/{corrective_incident['id']}/correct",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "operation_type": "DELIVERY",
            "notes": "Salida correctiva de una unidad",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "direction": "OUT",
                }
            ],
        },
    )
    assert corrective_resolution.status_code == 200, corrective_resolution.text
    corrected_incident = corrective_resolution.json()
    assert corrected_incident["status"] == "CORRECTED"
    assert corrected_incident["corrective_operation_id"]

    incidents_after_correction = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents",
        headers=headers,
    )
    assert incidents_after_correction.status_code == 200, incidents_after_correction.text
    incident_statuses = {item["id"]: item["status"] for item in incidents_after_correction.json()}
    assert incident_statuses[incident["id"]] == "RESOLVED"
    assert incident_statuses[corrective_incident["id"]] == "CORRECTED"

    route_operations = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations",
        headers=headers,
    )
    assert route_operations.status_code == 200, route_operations.text
    corrected_operation = next(
        operation
        for operation in route_operations.json()
        if operation["id"] == corrected_incident["corrective_operation_id"]
    )
    assert corrected_operation["status"] == "CONFIRMED"
    assert corrected_operation["operation_type"] == "DELIVERY"

    composition_after_correction = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition_after_correction.status_code == 200, composition_after_correction.text
    assert composition_after_correction.json()["product_lines"][0]["quantity"] == 3.0

    stop_progress_corrected = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress_corrected.status_code == 200, stop_progress_corrected.text
    assert stop_progress_corrected.json()[0]["progress_status"] == "COMPLETED"
    assert stop_progress_corrected.json()[0]["open_incidents"] == 0


def test_route_stop_result_minimal_updates_progress_and_summary(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    customer = create_customer(
        client,
        headers,
        name="Cliente Stop Result",
        document_number="20100070970",
    )

    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen StopResult", "code": "ALM-SR", "address": None, "phone": None},
    ).json()
    zone = client.post(
        "/api/v1/plugins/logistics/zones",
        headers=headers,
        json={"name": "Zona StopResult", "code": "ZN-SR"},
    ).json()
    vehicle = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-SR",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "SR",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    ).json()
    delivery_point = client.post(
        "/api/v1/plugins/logistics/delivery-points",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "contact_name": "Operador StopResult",
            "address": "Calle StopResult 123",
            "zone_id": zone["id"],
            "warehouse_id": warehouse["id"],
            "is_primary": True,
        },
    ).json()
    route = client.post(
        "/api/v1/plugins/logistics/routes",
        headers=headers,
        json={
            "route_date": datetime.now(UTC).date().isoformat(),
            "vehicle_id": vehicle["id"],
        },
    ).json()
    stop = client.post(
        f"/api/v1/plugins/logistics/routes/{route['id']}/stops",
        headers=headers,
        json={"delivery_point_id": delivery_point["id"], "stop_order": 1},
    ).json()

    product = create_product(client, headers, sku="SR-GLP10", name="Bombona 10kg SR")
    stock_seed = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": "Stock inicial stop result",
            "idempotency_key": "test-stop-result-stock-seed",
        },
    )
    assert stock_seed.status_code == 201, stock_seed.text

    driver_id = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog",
        headers=headers,
    ).json()[0]["id"]
    session = client.post(
        "/api/v1/plugins/logistics/vehicle-sessions",
        headers=headers,
        json={
            "vehicle_id": vehicle["id"],
            "driver_id": driver_id,
            "origin_warehouse_id": warehouse["id"],
            "route_id": route["id"],
        },
    ).json()

    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
        headers=headers,
    ).status_code == 200
    assert client.put(
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
    ).status_code == 200
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
        headers=headers,
        json={},
    ).status_code == 200
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
        headers=headers,
    ).status_code == 200
    assert client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Generación inicial stop result",
            "event": "INITIAL_GENERATION",
            "idempotency_key": "test-stop-result-waybill-v1",
        },
    ).status_code == 200

    invalid_result = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-results/{stop['id']}",
        headers=headers,
        json={
            "status": "PARTIAL",
            "completion_percent": 100,
            "outcome_type": "PARTIAL_ATTENDED",
            "driver_note": "Dato inválido para parcial",
        },
    )
    assert invalid_result.status_code == 400, invalid_result.text

    upsert_result = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-results/{stop['id']}",
        headers=headers,
        json={
            "status": "PARTIAL",
            "completion_percent": 60,
            "outcome_type": "PARTIAL_ATTENDED",
            "driver_note": "Llegaron muchos clientes y solo se pudo cubrir parte del stop.",
        },
    )
    assert upsert_result.status_code == 200, upsert_result.text
    result_payload = upsert_result.json()
    assert result_payload["status"] == "PARTIAL"
    assert result_payload["completion_percent"] == 60.0

    stop_results = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-results",
        headers=headers,
    )
    assert stop_results.status_code == 200, stop_results.text
    assert stop_results.json()[0]["outcome_type"] == "PARTIAL_ATTENDED"

    stop_progress = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-stop-progress",
        headers=headers,
    )
    assert stop_progress.status_code == 200, stop_progress.text
    progress_payload = stop_progress.json()[0]
    assert progress_payload["progress_status"] == "PARTIAL"
    assert progress_payload["completion_percent"] == 60.0
    assert progress_payload["outcome_type"] == "PARTIAL_ATTENDED"
    assert "solo se pudo cubrir parte" in progress_payload["driver_note"]

    summary_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/operational-summary",
        headers=headers,
    )
    assert summary_response.status_code == 200, summary_response.text
    summary = summary_response.json()
    assert summary["health_status"] == "ATTENTION"
    assert summary["data_completeness"] == "FULL"
    assert summary["attention_reasons"] == ["PARTIAL_STOP"]
    assert summary["problematic_stops"][0]["completion_percent"] == 60.0
    assert summary["problematic_stops"][0]["outcome_type"] == "PARTIAL_ATTENDED"
