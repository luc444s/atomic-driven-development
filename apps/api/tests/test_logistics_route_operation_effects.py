from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi.testclient import TestClient

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_customer,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
    enable_stock_plugin,
)
from apps.api.tests.test_stock_plugin import create_active_base_cost


def _create_outbound_session_context(
    client: TestClient, app, seeded_demo: dict[str, str], *, sku: str, name: str
) -> dict[str, Any]:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    customer = create_customer(
        client,
        headers,
        name=f"Cliente {sku}",
        document_number="20100070970",
    )
    warehouse = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": f"Almacen {sku}", "code": f"ALM-{sku}", "address": None, "phone": None},
    ).json()
    vehicle = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": f"TRK-{sku}",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": sku,
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
            "contact_name": "Operador Ruta",
            "address": "Calle Ruta 123",
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
    product = create_product(client, headers, sku=sku, name=name)
    create_active_base_cost(client, headers, product_id=product["id"], amount=5.0)

    stock_seed = client.post(
        "/api/v1/plugins/stock/adjust",
        headers=headers,
        json={
            "product_id": product["id"],
            "warehouse_id": warehouse["id"],
            "quantity": 20,
            "unit_cost": 5.0,
            "reason": f"Stock inicial {sku}",
            "idempotency_key": f"stock-seed-{sku}",
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

    assert (
        client.post(
            f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/start-loading",
            headers=headers,
        ).status_code
        == 200
    )
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
    assert (
        client.post(
            f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/confirm-and-ready",
            headers=headers,
            json={},
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/depart",
            headers=headers,
        ).status_code
        == 200
    )

    return {
        "customer": customer,
        "headers": headers,
        "warehouse": warehouse,
        "route": route,
        "stop": stop,
        "product": product,
        "session": session,
    }


def test_pickup_pure_changes_physical_composition_without_stock_movement(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="PUP-GLP10",
        name="Bombona 10kg Pickup",
    )
    headers = ctx["headers"]
    stop = ctx["stop"]
    product = ctx["product"]
    session = ctx["session"]

    waybill = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Generación inicial en ruta",
            "event": "INITIAL_GENERATION",
            "idempotency_key": "pickup-pure-waybill-v1",
        },
    )
    assert waybill.status_code == 200, waybill.text
    assert waybill.json()["active"]["version"] == 1

    route_operation = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "operation_type": "PICKUP",
            "notes": "Recojo fisico sin devolucion financiera",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "direction": "IN",
                }
            ],
        },
    )
    assert route_operation.status_code == 200, route_operation.text

    confirm = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/{route_operation.json()['id']}/confirm",
        headers=headers,
    )
    assert confirm.status_code == 200, confirm.text
    confirmed = confirm.json()
    assert confirmed["status"] == "CONFIRMED"
    assert confirmed["movement_ids"] == []

    mobile_balance = client.get(
        f"/api/v1/plugins/stock/balance/{product['id']}/{session['mobile_warehouse_id']}",
        headers=headers,
    )
    assert mobile_balance.status_code == 200, mobile_balance.text
    assert mobile_balance.json()["quantity"] == 5.0

    return_in_entries = client.get(
        "/api/v1/plugins/stock/ledger",
        headers=headers,
        params={"operation": "return_in", "limit": 10},
    )
    assert return_in_entries.status_code == 200, return_in_entries.text
    assert return_in_entries.json() == []

    composition = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition.status_code == 200, composition.text
    assert composition.json()["product_lines"][0]["quantity"] == 6.0

    waybill_state = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte",
        headers=headers,
    )
    assert waybill_state.status_code == 200, waybill_state.text
    assert waybill_state.json()["sync_status"] == "OUTDATED"

    regenerated = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Recojo fisico en ruta",
            "event": "PHYSICAL_COMPOSITION_CHANGED",
            "idempotency_key": "pickup-pure-waybill-v2",
        },
    )
    assert regenerated.status_code == 200, regenerated.text
    assert regenerated.json()["sync_status"] == "SYNCED"
    assert regenerated.json()["active"]["version"] == 2
    assert regenerated.json()["active"]["snapshot"]["transported_items"][0]["quantity"] == 6.0


def test_exchange_keeps_real_return_financial_flow(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="RET-GLP10",
        name="Bombona 10kg Return",
    )
    headers = ctx["headers"]
    stop = ctx["stop"]
    product = ctx["product"]
    session = ctx["session"]

    exchange = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/exchange",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "notes": "Intercambio con retorno financiero real",
            "delivered_lines": [{"product_id": product["id"], "quantity": 2}],
            "picked_up_lines": [{"product_id": product["id"], "quantity": 1}],
        },
    )
    assert exchange.status_code == 200, exchange.text

    confirm = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/{exchange.json()['id']}/confirm",
        headers=headers,
    )
    assert confirm.status_code == 200, confirm.text
    confirmed = confirm.json()
    assert confirmed["status"] == "CONFIRMED"
    assert len(confirmed["movement_ids"]) == 2

    return_in_entries = client.get(
        "/api/v1/plugins/stock/ledger",
        headers=headers,
        params={"operation": "return_in", "limit": 10},
    )
    assert return_in_entries.status_code == 200, return_in_entries.text
    entries = return_in_entries.json()
    assert len(entries) == 1
    assert entries[0]["operation"] == "return_in"

    composition = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition.status_code == 200, composition.text
    assert composition.json()["product_lines"][0]["quantity"] == 4.0


def test_pickup_serialized_route_scan_uses_customer_empty_cylinders(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="SER-GLP10",
        name="Bombona 10kg Serializada",
    )
    headers = ctx["headers"]
    customer = ctx["customer"]
    warehouse = ctx["warehouse"]
    stop = ctx["stop"]
    product = ctx["product"]
    session = ctx["session"]

    pickup_cylinder = client.post(
        "/api/v1/plugins/logistics/cylinders",
        headers=headers,
        json={
            "serial": "SER-PICKUP-001",
            "warehouse_id": warehouse["id"],
            "condition": "CILPRO",
            "product_id": product["id"],
            "entry_mode": "FULL_FROM_SUPPLIER",
            "minimal_route_create": True,
        },
    )
    assert pickup_cylinder.status_code == 201, pickup_cylinder.text
    pickup_cylinder_id = pickup_cylinder.json()["id"]

    move_to_customer = client.post(
        f"/api/v1/plugins/logistics/cylinders/{pickup_cylinder_id}/transition",
        headers=headers,
        json={
            "to_state": "EN_CLIENTE_LLENO",
            "customer_id": customer["id"],
            "origin": "TEST_ROUTE_PICKUP",
        },
    )
    assert move_to_customer.status_code == 200, move_to_customer.text
    move_to_empty = client.post(
        f"/api/v1/plugins/logistics/cylinders/{pickup_cylinder_id}/transition",
        headers=headers,
        json={
            "to_state": "EN_CLIENTE_VACIO",
            "customer_id": customer["id"],
            "origin": "TEST_ROUTE_PICKUP",
        },
    )
    assert move_to_empty.status_code == 200, move_to_empty.text

    select_pickup = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "selection_context": "ROUTE_PICKUP",
            "serial": "SER-PICKUP-001",
        },
    )
    assert select_pickup.status_code == 200, select_pickup.text

    selected_pickup = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/load-serials/selected",
        headers=headers,
        params={"product_id": product["id"], "selection_context": "ROUTE_PICKUP"},
    )
    assert selected_pickup.status_code == 200, selected_pickup.text
    assert len(selected_pickup.json()) == 1
    assert selected_pickup.json()[0]["cylinder_serial"] == "SER-PICKUP-001"

    route_operation = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "operation_type": "PICKUP",
            "notes": "Recojo serializado en ruta",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "direction": "IN",
                }
            ],
        },
    )
    assert route_operation.status_code == 200, route_operation.text

    confirm = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations/{route_operation.json()['id']}/confirm",
        headers=headers,
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["movement_ids"] == []

    ownership = client.get(
        f"/api/v1/plugins/logistics/cylinders/{pickup_cylinder_id}/ownership",
        headers=headers,
    )
    assert ownership.status_code == 200, ownership.text
    assert ownership.json()[0]["customer_id"] is None

    composition = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/composition/current",
        headers=headers,
    )
    assert composition.status_code == 200, composition.text
    assert composition.json()["product_lines"][0]["quantity"] == 1.0


def test_confirm_route_event_customer_emergency_is_idempotent_and_creates_incident(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="EVT-GLP10",
        name="Bombona 10kg Evento",
    )
    headers = ctx["headers"]
    customer = ctx["customer"]
    product = ctx["product"]
    session = ctx["session"]

    payload = {
        "context_type": "CUSTOMER_EMERGENCY",
        "customer_id": customer["id"],
        "operation_type": "DELIVERY",
        "notes": "Entrega de emergencia sin parada",
        "idempotency_key": "route-event-customer-emergency-v1",
        "items": [
            {
                "product_id": product["id"],
                "quantity": 1,
                "direction": "OUT",
            }
        ],
        "incident_mode": "CREATE",
        "type": "QUANTITY_MISMATCH",
        "incident_notes": "Se documenta desvío en la misma captura",
    }

    first = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-events/confirm",
        headers=headers,
        json=payload,
    )
    assert first.status_code == 200, first.text
    first_payload = first.json()
    assert first_payload["status"] == "CONFIRMED"
    assert first_payload["route_stop_id"] is None
    assert first_payload["context_type"] == "CUSTOMER_EMERGENCY"
    assert first_payload["customer_id"] == customer["id"]

    second = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-events/confirm",
        headers=headers,
        json=payload,
    )
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first_payload["id"]

    route_operations = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-operations",
        headers=headers,
    )
    assert route_operations.status_code == 200, route_operations.text
    assert len([item for item in route_operations.json() if item["id"] == first_payload["id"]]) == 1

    incidents = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-incidents",
        headers=headers,
    )
    assert incidents.status_code == 200, incidents.text
    assert len(incidents.json()) == 1
    assert incidents.json()[0]["related_operation_id"] == first_payload["id"]
    assert incidents.json()[0]["status"] == "OPEN"


def test_confirm_route_event_rejects_invalid_context_and_missing_correction_target(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="VAL-GLP10",
        name="Bombona 10kg Validación",
    )
    headers = ctx["headers"]
    customer = ctx["customer"]
    product = ctx["product"]
    session = ctx["session"]
    stop = ctx["stop"]

    invalid_stop_context = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-events/confirm",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "context_type": "STOP",
            "customer_id": customer["id"],
            "operation_type": "DELIVERY",
            "notes": "No debería aceptar customer_id libre con STOP",
            "idempotency_key": "route-event-invalid-stop-context",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "direction": "OUT",
                }
            ],
            "incident_mode": "NONE",
        },
    )
    assert invalid_stop_context.status_code == 400, invalid_stop_context.text
    assert "STOP" in invalid_stop_context.text

    missing_target = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-events/confirm",
        headers=headers,
        json={
            "context_type": "CUSTOMER_EMERGENCY",
            "customer_id": customer["id"],
            "operation_type": "DELIVERY",
            "notes": "Corrección inválida sin target",
            "idempotency_key": "route-event-missing-target",
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "direction": "OUT",
                }
            ],
            "incident_mode": "CORRECT_EXISTING",
        },
    )
    assert missing_target.status_code == 400, missing_target.text
    assert "target_incident_id" in missing_target.text
