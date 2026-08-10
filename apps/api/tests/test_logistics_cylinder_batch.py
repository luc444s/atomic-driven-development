# ruff: noqa: E501
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


def _setup_batch_env(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)


def _create_warehouse(client: TestClient, headers: dict[str, str]) -> dict[str, str]:
    response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Planta Lote", "code": "PLT", "address": "Zona Lote"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_product(client: TestClient, headers: dict[str, str]) -> dict[str, str]:
    return create_product(
        client,
        headers,
        sku="O2-BATCH-01",
        name="Oxigeno Batch B10",
    )


def test_cylinder_batch_creates_all_in_one_call(app) -> None:
    _setup_batch_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = _create_warehouse(client, headers)
        product = _create_product(client, headers)

        response = client.post(
            "/api/v1/plugins/logistics/cylinders/batch",
            headers=headers,
            json={
                "serials": ["BATCH-0001", "BATCH-0002", "BATCH-0003"],
                "gas_group_id": product["id"],
                "product_id": product["id"],
                "weight_origin": 40,
                "warehouse_id": warehouse["id"],
                "entry_mode": "EMPTY_FROM_WAREHOUSE",
                "next_hydrotest_date": (
                    datetime.now(UTC) + timedelta(days=365)
                ).date().isoformat(),
            },
        )
        assert response.status_code == 201, response.text
        cylinders = response.json()
        assert len(cylinders) == 3

        serials = [item["serial"] for item in cylinders]
        assert serials == ["BATCH-0001", "BATCH-0002", "BATCH-0003"]
        for cylinder in cylinders:
            assert cylinder["warehouse_id"] == warehouse["id"]
            assert cylinder["current_state"] == "EN_ALMACEN_VACIO"


def test_cylinder_batch_rejects_duplicate_serials(app) -> None:
    _setup_batch_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = _create_warehouse(client, headers)
        product = _create_product(client, headers)

        response = client.post(
            "/api/v1/plugins/logistics/cylinders/batch",
            headers=headers,
            json={
                "serials": ["BATCH-D1", "BATCH-D1"],
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "entry_mode": "EMPTY_FROM_WAREHOUSE",
            },
        )
        assert response.status_code in (400, 422), response.text