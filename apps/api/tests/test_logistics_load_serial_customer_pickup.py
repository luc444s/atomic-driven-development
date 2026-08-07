"""Carga operativa: permitir seleccionar seriales que estan en posesion del cliente.

Fix: COMPATIBLE_CYLINDER_STATES no incluia EN_CLIENTE_LLENO / EN_CLIENTE_VACIO, y ademas
se exigia que el cilindro pertenezca al almacen origen. En una jornada de recojo/carga
operativa el camion va al cliente a recoger el envase, asi que ambos bloqueos deben
saltarse para cilindros en cliente.
"""
from __future__ import annotations

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
from plugins.logistics.backend.models import LogisticsCylinder


def _setup_vehicle_and_session(
    client: TestClient, headers: dict[str, str]
) -> tuple[dict, dict, str]:
    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Carga", "code": "ALM-CRG", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-CRG",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "Carga",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    drivers_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog", headers=headers
    )
    assert drivers_response.status_code == 200, drivers_response.text
    driver_id = drivers_response.json()[0]["id"]

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
    return warehouse, vehicle, session_response.json()["id"]


def test_load_plan_accepts_cylinder_at_customer_full(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse, _vehicle, session_id = _setup_vehicle_and_session(client, headers)
    create_customer(
        client, headers, name="Cliente Recojo", document_number="20516509423"
    )
    product = create_product(client, headers, sku="CRG-CYL-GAS", name="Gas Recojo 10kg")

    # Cilindro en posesion del cliente, LLENO (el camion va a recogerlo).
    # Se crea directo en DB porque el endpoint de cilindros fuerza el estado segun entry_mode.
    # location = TANK_WH:<OTRO almacen> para forzar que NO pertenezca al almacen origen y
    # asi verificar que el chequeo de almacen se salta para cilindros en posesion del cliente.
    with app.state.session_factory() as db:
        db.add(
            LogisticsCylinder(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                serial="CRG-2945",
                product_id=product["id"],
                current_state="EN_CLIENTE_LLENO",
                condition="CILPRO",
                is_active=True,
                location=f"TANK_WH:{warehouse['id']}",
            )
        )
        db.commit()

    # El search en contexto LOAD_PLAN debe marcarlo como AVAILABLE (antes: UNAVAILABLE)
    search_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/search",
        headers=headers,
        params={
            "product_id": product["id"],
            "query": "2945",
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
        },
    )
    assert search_response.status_code == 200, search_response.text
    search_results = search_response.json()
    assert len(search_results) == 1, search_results
    assert search_results[0]["availability_status"] == "AVAILABLE"
    assert search_results[0]["serial"] == "CRG-2945"

    # El select en LOAD_PLAN debe permitirlo (antes: "no esta disponible para carga operativa")
    select_response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "CRG-2945",
        },
    )
    assert select_response.status_code == 200, select_response.text
    assignment = select_response.json()
    assert assignment["cylinder_serial"] == "CRG-2945"
    assert assignment["assignment_status"] == "SELECTED"


def test_route_pickup_accepts_cylinder_at_customer_full(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    # Recojo en ruta (RETURNING / OUTBOUND): antes solo aceptaba EN_CLIENTE_VACIO.
    # Ahora tambien EN_CLIENTE_LLENO (recojo programado de llenos).
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse, _vehicle, session_id = _setup_vehicle_and_session(client, headers)
    create_customer(
        client, headers, name="Cliente Recojo Ruta", document_number="20516509423"
    )
    product = create_product(client, headers, sku="RPK-CYL-GAS", name="Gas Recojo Ruta 10kg")

    with app.state.session_factory() as db:
        db.add(
            LogisticsCylinder(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                serial="RPK-2946",
                product_id=product["id"],
                current_state="EN_CLIENTE_LLENO",
                condition="CILPRO",
                is_active=True,
            )
        )
        db.commit()

    search_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_id}/load-serials/search",
        headers=headers,
        params={
            "product_id": product["id"],
            "query": "2946",
            "selection_context": "ROUTE_PICKUP",
        },
    )
    assert search_response.status_code == 200, search_response.text
    results = search_response.json()
    assert len(results) == 1, results
    assert results[0]["availability_status"] == "AVAILABLE"

    select_response = client.put(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session_id}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "selection_context": "ROUTE_PICKUP",
            "serial": "RPK-2946",
        },
    )
    assert select_response.status_code == 200, select_response.text
    assert select_response.json()["assignment_status"] == "SELECTED"


def test_load_plan_still_rejects_cylinder_not_compatible(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse, _vehicle, session_id = _setup_vehicle_and_session(client, headers)
    create_customer(
        client, headers, name="Cliente No Recojo", document_number="20104332189"
    )
    product = create_product(client, headers, sku="CRG-NO-GAS", name="Gas No Recojo 10kg")

    # Estado no compatible con carga operativa (ej. PERDIDO) se mantiene rechazado.
    with app.state.session_factory() as db:
        db.add(
            LogisticsCylinder(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                serial="CRG-NO-001",
                product_id=product["id"],
                current_state="PERDIDO",
                condition="CILPRO",
                is_active=True,
            )
        )
        db.commit()

    select_response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "CRG-NO-001",
        },
    )
    assert select_response.status_code == 400, select_response.text
    assert "no está disponible para carga operativa" in select_response.json()["detail"]
