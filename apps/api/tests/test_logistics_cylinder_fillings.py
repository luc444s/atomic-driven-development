from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_stock_plugin,
)
from apps.api.tests.test_productos_plugin import enable_productos_plugin


def _setup_fillings_env(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)


def test_fill_and_vacate_cylinder_updates_stock_and_trace(app) -> None:
    _setup_fillings_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Planta Norte", "code": "PLN", "address": "Zona Industrial"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()

        product = create_product(
            client,
            headers,
            sku="O2-FILL-01",
            name="Oxigeno Industrial B10",
        )

        stock_config_response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 0,
                "max_quantity": 100,
                "is_active": True,
            },
        )
        assert stock_config_response.status_code == 200, stock_config_response.text

        stock_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 25,
                "unit_cost": 5,
                "reason": "Stock libre para llenado",
            },
        )
        assert stock_adjust_response.status_code == 201, stock_adjust_response.text

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "FILL-0001",
                "product_id": product["id"],
                "weight_origin": 40,
                "next_hydrotest_date": (
                    datetime.now(UTC) + timedelta(days=365)
                ).date().isoformat(),
            },
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()

        fill_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/fill",
            headers=headers,
            json={
                "warehouse_id": warehouse["id"],
                "content_kg": 10.5,
                "notes": "Llenado operativo de prueba",
            },
        )
        assert fill_response.status_code == 200, fill_response.text
        filled_cylinder = fill_response.json()
        assert filled_cylinder["current_state"] == "LLENADO_OK"
        assert filled_cylinder["fill_status"] == "CARGADO"
        assert filled_cylinder["content_kg"] == 10.5
        assert filled_cylinder["weight_current"] == 50.5
        assert filled_cylinder["last_fill_warehouse_id"] == warehouse["id"]
        assert filled_cylinder["last_fill_warehouse_name"] == warehouse["name"]
        assert filled_cylinder["last_fill_at"] is not None

        balance_after_fill = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert balance_after_fill.status_code == 200, balance_after_fill.text
        assert balance_after_fill.json()["quantity"] == 14.5

        trace_after_fill = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/trace",
            headers=headers,
        )
        assert trace_after_fill.status_code == 200, trace_after_fill.text
        fill_trace = next(
            item for item in trace_after_fill.json() if item["reason_code"] == "FILL"
        )
        assert fill_trace["metadata_json"]["warehouse_id"] == warehouse["id"]

        vacate_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/vacate",
            headers=headers,
            json={
                "warehouse_id": warehouse["id"],
                "notes": "Vaciado técnico de prueba",
            },
        )
        assert vacate_response.status_code == 200, vacate_response.text
        emptied_cylinder = vacate_response.json()
        assert emptied_cylinder["current_state"] == "EN_ALMACEN_VACIO"
        assert emptied_cylinder["fill_status"] == "VACIO"
        assert emptied_cylinder["content_kg"] == 0
        assert emptied_cylinder["volume_m3"] == 0
        assert emptied_cylinder["weight_current"] == 40
        assert emptied_cylinder["last_fill_at"] == filled_cylinder["last_fill_at"]

        balance_after_vacate = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert balance_after_vacate.status_code == 200, balance_after_vacate.text
        assert balance_after_vacate.json()["quantity"] == 14.5

        trace_after_vacate = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/trace",
            headers=headers,
        )
        assert trace_after_vacate.status_code == 200, trace_after_vacate.text
        assert any(item["reason_code"] == "VACATE" for item in trace_after_vacate.json())


def test_fill_cylinder_rejects_when_stock_is_insufficient(app) -> None:
    _setup_fillings_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Planta Sur", "code": "PLS", "address": "Zona Sur"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()

        product = create_product(
            client,
            headers,
            sku="O2-FILL-02",
            name="Oxigeno Industrial B50",
        )

        stock_config_response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 0,
                "max_quantity": 100,
                "is_active": True,
            },
        )
        assert stock_config_response.status_code == 200, stock_config_response.text

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "FILL-0002",
                "product_id": product["id"],
                "next_hydrotest_date": (
                    datetime.now(UTC) + timedelta(days=365)
                ).date().isoformat(),
            },
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()

        fill_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/fill",
            headers=headers,
            json={
                "warehouse_id": warehouse["id"],
                "content_kg": 5,
            },
        )
        assert fill_response.status_code == 400, fill_response.text
        assert "Stock insuficiente" in fill_response.json()["detail"]


def test_fill_cylinder_uses_cryogenic_recipe_source_product(app) -> None:
    _setup_fillings_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Planta Cryo", "code": "PCR", "address": "Zona Criogenica"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()

        source_product = create_product(
            client,
            headers,
            sku="LOX-SRC-01",
            name="Oxigeno Liquido Criogenico",
        )
        result_product = create_product(
            client,
            headers,
            sku="O2-B10-200",
            name="Oxigeno Industrial B10 200 BAR",
        )

        recipe_response = client.post(
            f"/api/v1/plugins/productos/products/{result_product['id']}/adr",
            headers=headers,
            json={
                "source_product_id": source_product["id"],
                "source_quantity_liters": 3.798,
                "category": "2F",
                "packaging_type": "CIL",
                "net_weight_kg": 3.8,
                "net_volume_m3": 3.2,
                "un_number": "1073",
                "cargo_description": "Oxigeno comprimido",
                "label": "2.2",
                "tunnel_restriction": "E",
                "factor": 1,
                "points": 3,
                "unit_measure": "L",
            },
        )
        assert recipe_response.status_code == 201, recipe_response.text

        stock_config_response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": source_product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 0,
                "max_quantity": 100,
                "is_active": True,
            },
        )
        assert stock_config_response.status_code == 200, stock_config_response.text

        stock_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": source_product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 20,
                "unit_cost": 5,
                "reason": "Stock criogenico libre para llenado",
            },
        )
        assert stock_adjust_response.status_code == 201, stock_adjust_response.text

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "CRYO-0001",
                "product_id": result_product["id"],
                "weight_origin": 40,
                "next_hydrotest_date": (
                    datetime.now(UTC) + timedelta(days=365)
                ).date().isoformat(),
            },
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()

        fill_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/fill",
            headers=headers,
            json={
                "warehouse_id": warehouse["id"],
                "source_product_id": source_product["id"],
                "fill_operation_id": "fill-op-cryo-001",
                "notes": "Llenado criogenico de prueba",
            },
        )
        assert fill_response.status_code == 200, fill_response.text
        filled_cylinder = fill_response.json()
        assert filled_cylinder["current_state"] == "LLENADO_OK"
        assert filled_cylinder["fill_status"] == "CARGADO"
        assert filled_cylinder["content_kg"] == 3.8
        assert filled_cylinder["volume_m3"] == 3.2
        assert filled_cylinder["weight_current"] == 43.8
        assert filled_cylinder["last_fill_mode"] == "CRYOGENIC"
        assert filled_cylinder["last_fill_operation_id"] == "fill-op-cryo-001"
        assert filled_cylinder["last_fill_source_product_id"] == source_product["id"]
        assert filled_cylinder["last_fill_source_product_name"] == source_product["name"]
        assert filled_cylinder["last_fill_source_quantity_liters"] == 3.798

        source_balance_response = client.get(
            f"/api/v1/plugins/stock/balance/{source_product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert source_balance_response.status_code == 200, source_balance_response.text
        assert source_balance_response.json()["quantity"] == 16.202

        trace_response = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/trace",
            headers=headers,
        )
        assert trace_response.status_code == 200, trace_response.text
        fill_trace = next(
            item for item in trace_response.json() if item["reason_code"] == "FILL_CRYO"
        )
        assert fill_trace["metadata_json"]["fill_mode"] == "CRYOGENIC"
        assert fill_trace["metadata_json"]["fill_operation_id"] == "fill-op-cryo-001"
        assert fill_trace["metadata_json"]["source_product_id"] == source_product["id"]
        assert fill_trace["metadata_json"]["result_product_id"] == result_product["id"]
        assert fill_trace["metadata_json"]["source_quantity_liters"] == 3.798


def test_fill_cylinder_rejects_explicit_cryogenic_source_without_recipe(app) -> None:
    _setup_fillings_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Planta Sin Receta", "code": "PSR", "address": "Zona Norte"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()

        source_product = create_product(
            client,
            headers,
            sku="LOX-SRC-02",
            name="Oxigeno Liquido Sin Receta",
        )
        result_product = create_product(
            client,
            headers,
            sku="O2-B50-200",
            name="Oxigeno Industrial B50 200 BAR",
        )

        stock_config_response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": source_product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 0,
                "max_quantity": 100,
                "is_active": True,
            },
        )
        assert stock_config_response.status_code == 200, stock_config_response.text

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "CRYO-0002",
                "product_id": result_product["id"],
                "next_hydrotest_date": (
                    datetime.now(UTC) + timedelta(days=365)
                ).date().isoformat(),
            },
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()

        fill_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/fill",
            headers=headers,
            json={
                "warehouse_id": warehouse["id"],
                "source_product_id": source_product["id"],
            },
        )
        assert fill_response.status_code == 400, fill_response.text
        assert "receta criogenica activa" in fill_response.json()["detail"]
