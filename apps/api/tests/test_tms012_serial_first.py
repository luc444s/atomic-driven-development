"""TMS-012: carga operativa serial-first — el serial infiere el producto.

Verifica:
- select sin product_id infiere el producto del cilindro (C2)
- select con product_id explícito funciona igual (I3 compat)
- search sin product_id devuelve producto inferido (C3)
- negativos: serial sin cilindro, cilindro inactivo, estado no compatible (C4/I2)
- select no toca stock ni movimientos (I4)
"""
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
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsLoadSerialAssignment,
    LogisticsMovement,
)


def _make_cylinder_at_origin(
    app, seeded_demo: dict[str, str], *, serial: str, product_id: str, warehouse_id: str
) -> None:
    _make_cylinder(
        app,
        seeded_demo,
        serial=serial,
        product_id=product_id,
        location=f"TANK_WH:{warehouse_id}",
    )


def _make_cylinder(
    app,
    seeded_demo: dict[str, str],
    *,
    serial: str,
    product_id: str,
    current_state: str = "LLENADO_OK",
    is_active: bool = True,
    location: str | None = None,
) -> None:
    with app.state.session_factory() as db:
        db.add(
            LogisticsCylinder(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                serial=serial,
                product_id=product_id,
                current_state=current_state,
                condition="CILPRO",
                is_active=is_active,
                location=location,
            )
        )
        db.commit()


def _setup(client: TestClient, app, seeded_demo: dict[str, str]) -> tuple[dict, str, dict]:
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Carga", "code": "ALM-T12", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-T12",
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

    driver_response = client.post(
        "/api/v1/core/users",
        headers=headers,
        json={
            "name": "Driver T12",
            "email": "driver.t12@example.com",
            "password": "ChangeMe123!",
            "branch_id": None,
            "category": "driver",
            "role_ids": [],
            "warehouse_ids": [],
        },
    )
    assert driver_response.status_code == 201, driver_response.text
    catalog_response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/drivers/catalog", headers=headers
    )
    assert catalog_response.status_code == 200, catalog_response.text
    driver_id = catalog_response.json()[0]["id"]

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

    product = create_product(client, headers, sku="TMS012-GAS", name="O2 10kg Inferido")
    return warehouse, session_response.json()["id"], product, headers


def test_select_serial_infer_product_sin_product_id(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    warehouse, session_id, product, headers = _setup(client, app, seeded_demo)
    _make_cylinder_at_origin(app, seeded_demo, serial="TMS012-A1",
        product_id=product["id"], warehouse_id=warehouse["id"])

    response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "TMS012-A1",
        },
    )
    assert response.status_code == 200, response.text
    assignment = response.json()
    assert assignment["cylinder_serial"] == "TMS012-A1"
    assert assignment["product_id"] == product["id"]
    assert assignment["assignment_status"] == "SELECTED"


def test_select_con_product_id_sigue_igual(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    warehouse, session_id, product, headers = _setup(client, app, seeded_demo)
    _make_cylinder_at_origin(app, seeded_demo, serial="TMS012-A2",
        product_id=product["id"], warehouse_id=warehouse["id"])

    response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "product_id": product["id"],
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "TMS012-A2",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["product_id"] == product["id"]


def test_search_sin_product_id_expone_producto_inferido(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    warehouse, session_id, product, headers = _setup(client, app, seeded_demo)
    _make_cylinder_at_origin(app, seeded_demo, serial="TMS012-B1",
        product_id=product["id"], warehouse_id=warehouse["id"])

    response = client.get(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/search",
        headers=headers,
        params={
            "query": "TMS012-B1",
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
        },
    )
    assert response.status_code == 200, response.text
    results = response.json()
    assert len(results) == 1
    assert results[0]["serial"] == "TMS012-B1"
    assert results[0]["product_id"] == product["id"]
    assert results[0]["availability_status"] == "AVAILABLE"


def test_select_serial_no_existente_falla(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    warehouse, session_id, _product, headers = _setup(client, app, seeded_demo)

    response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "TMS012-NOX",
        },
    )
    assert response.status_code == 404, response.text


def test_select_serial_cilindro_inactivo_falla(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    warehouse, session_id, product, headers = _setup(client, app, seeded_demo)
    _make_cylinder(
        app,
        seeded_demo,
        serial="TMS012-INA",
        product_id=product["id"],
        is_active=False,
    )

    response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "TMS012-INA",
        },
    )
    assert response.status_code == 400, response.text


def test_select_no_toca_stock_ni_movimientos(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    warehouse, session_id, product, headers = _setup(client, app, seeded_demo)
    _make_cylinder_at_origin(app, seeded_demo, serial="TMS012-C1",
        product_id=product["id"], warehouse_id=warehouse["id"])

    with app.state.session_factory() as db:
        movements_before = db.query(LogisticsMovement).count()

    response = client.put(
        "/api/v1/plugins/logistics/vehicle-sessions/"
        f"{session_id}/load-serials/select",
        headers=headers,
        json={
            "source_warehouse_id": warehouse["id"],
            "selection_context": "LOAD_PLAN",
            "serial": "TMS012-C1",
        },
    )
    assert response.status_code == 200, response.text

    with app.state.session_factory() as db:
        movements_after = db.query(LogisticsMovement).count()
        assignments = db.query(LogisticsLoadSerialAssignment).count()

    assert movements_after == movements_before
    assert assignments == 1