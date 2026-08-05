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


def _setup_tank_env(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)


def _add_cryogenic_recipe(client: TestClient, headers: dict[str, str], result_product_id: str, source_product_id: str) -> None:
    recipe = client.post(
        f"/api/v1/plugins/productos/products/{result_product_id}/adr",
        headers=headers,
        json={
            "source_product_id": source_product_id,
            "source_quantity_liters": 2.516,
            "category": "2F",
            "packaging_type": "CIL",
            "net_weight_kg": 2.52,
            "net_volume_m3": 2.12,
            "un_number": "1073",
            "cargo_description": "Oxigeno comprimido",
            "label": "2.2",
            "tunnel_restriction": "E",
            "factor": 1,
            "points": 3,
            "unit_measure": "L",
        },
    )
    assert recipe.status_code == 201, recipe.text


def test_create_cryogenic_tank_persists_container_type(app) -> None:
    _setup_tank_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        lox = create_product(client, headers, sku="LOX-TK-01", name="Oxigeno Liquido Criogenico")
        result = create_product(client, headers, sku="O2-TK-RES", name="Oxigeno Industrial B10")
        _add_cryogenic_recipe(client, headers, result["id"], lox["id"])

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "TK-LOX-001",
                "container_type": "CRYOGENIC_TANK",
                "product_id": lox["id"],
                "volume_m3": 5.0,
                "description": "Tanque LOX planta norte",
            },
        )
        assert create_response.status_code == 201, create_response.text
        tank = create_response.json()
        assert tank["container_type"] == "CRYOGENIC_TANK"
        assert tank["product_id"] == lox["id"]
        assert tank["serial"] == "TK-LOX-001"

        detail_response = client.get(
            f"/api/v1/plugins/logistics/cylinders/{tank['id']}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        assert detail_response.json()["container_type"] == "CRYOGENIC_TANK"


def test_create_cryogenic_tank_requires_gas_product(app) -> None:
    _setup_tank_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "TK-NOPROD",
                "container_type": "CRYOGENIC_TANK",
            },
        )
        assert create_response.status_code == 400, create_response.text
        assert "product_id" in create_response.json()["detail"]


def test_create_cryogenic_tank_requires_gas_that_is_cryogenic_source(app) -> None:
    _setup_tank_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        regular_gas = create_product(client, headers, sku="GAS-NO-SRC", name="Gas sin receta criogenica")

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "TK-NOSRC",
                "container_type": "CRYOGENIC_TANK",
                "product_id": regular_gas["id"],
            },
        )
        assert create_response.status_code == 400, create_response.text
        assert "receta criogenica" in create_response.json()["detail"]


def test_create_standard_cylinder_defaults_to_cylinder_type(app) -> None:
    _setup_tank_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        product = create_product(client, headers, sku="CIL-STD-01", name="Oxigeno Industrial B50")

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "STD-0001",
                "product_id": product["id"],
                "next_hydrotest_date": (datetime.now(UTC) + timedelta(days=365)).date().isoformat(),
            },
        )
        assert create_response.status_code == 201, create_response.text
        assert create_response.json()["container_type"] == "CYLINDER"


def test_update_to_cryogenic_tank_validates_product(app) -> None:
    _setup_tank_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        lox = create_product(client, headers, sku="LOX-TK-02", name="Oxigeno Liquido Criogenico")
        result = create_product(client, headers, sku="O2-TK-RES2", name="Oxigeno Industrial B10")
        _add_cryogenic_recipe(client, headers, result["id"], lox["id"])
        product = create_product(client, headers, sku="CIL-STD-02", name="Oxigeno Industrial B10")

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={"serial": "UPG-0001", "product_id": product["id"]},
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()
        assert cylinder["container_type"] == "CYLINDER"

        update_response = client.patch(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
            json={"container_type": "CRYOGENIC_TANK"},
        )
        assert update_response.status_code == 400, update_response.text

        update_response = client.patch(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
            json={"container_type": "CRYOGENIC_TANK", "product_id": lox["id"]},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["container_type"] == "CRYOGENIC_TANK"


def test_list_cylinders_filters_by_container_type(app) -> None:
    _setup_tank_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        lox = create_product(client, headers, sku="LOX-TK-03", name="Oxigeno Liquido Criogenico")
        result = create_product(client, headers, sku="O2-TK-RES3", name="Oxigeno Industrial B10")
        _add_cryogenic_recipe(client, headers, result["id"], lox["id"])
        product = create_product(client, headers, sku="CIL-STD-03", name="Oxigeno Industrial B10")

        tank_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "TK-FILTER-01",
                "container_type": "CRYOGENIC_TANK",
                "product_id": lox["id"],
            },
        )
        assert tank_response.status_code == 201, tank_response.text

        cylinder_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={"serial": "FILTER-STD-01", "product_id": product["id"]},
        )
        assert cylinder_response.status_code == 201, cylinder_response.text

        tank_list = client.get(
            "/api/v1/plugins/logistics/cylinders?container_type=CRYOGENIC_TANK",
            headers=headers,
        )
        assert tank_list.status_code == 200, tank_list.text
        tank_serials = [item["serial"] for item in tank_list.json()]
        assert "TK-FILTER-01" in tank_serials
        assert "FILTER-STD-01" not in tank_serials
