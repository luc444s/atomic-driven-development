# ruff: noqa: E501
from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.tests.test_logistics_plugin import auth_headers, create_product
from apps.api.tests.test_productos_plugin import enable_productos_plugin


def _setup_env(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_productos_plugin(app, seeded_demo)


def _set_liquid_density(client: TestClient, headers: dict[str, str], product_id: str, kg_per_m3: float) -> None:
    response = client.put(
        f"/api/v1/plugins/productos/products/{product_id}",
        headers=headers,
        json={"default_weight_kg": kg_per_m3},
    )
    assert response.status_code == 200, response.text


def _post_recipe(
    client: TestClient,
    headers: dict[str, str],
    *,
    product_id: str,
    source_product_id: str,
    source_quantity_liters: float,
    net_weight_kg: float,
):
    return client.post(
        f"/api/v1/plugins/productos/products/{product_id}/adr",
        headers=headers,
        json={
            "source_product_id": source_product_id,
            "source_quantity_liters": source_quantity_liters,
            "category": "2F",
            "packaging_type": "CIL",
            "net_weight_kg": net_weight_kg,
            "net_volume_m3": 1.6,
            "un_number": "1072",
            "cargo_description": "Oxigeno comprimido",
            "label": "2.2",
            "tunnel_restriction": "E",
            "factor": 1,
            "points": 3,
            "unit_measure": "L",
            "valid_from": "2026-01-01",
        },
    )


def test_adr_recipe_accepts_real_liquid_liters(app) -> None:
    _setup_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        source = create_product(client, headers, sku="LOX-SRC-01", name="Oxigeno Liquido - LOX")
        _set_liquid_density(client, headers, source["id"], 1141.0)
        result = create_product(client, headers, sku="O2-B10-01", name="Oxigeno Industrial B10 / 150BAR")

        response = _post_recipe(
            client,
            headers,
            product_id=result["id"],
            source_product_id=source["id"],
            source_quantity_liters=1.665,
            net_weight_kg=1.90,
        )
        assert response.status_code == 201, response.text


def test_adr_recipe_rejects_water_capacity_as_liquid_liters(app) -> None:
    _setup_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        source = create_product(client, headers, sku="LOX-SRC-02", name="Oxigeno Liquido - LOX")
        _set_liquid_density(client, headers, source["id"], 1141.0)
        result = create_product(client, headers, sku="O2-B10-02", name="Oxigeno Industrial B10 / 150BAR")

        response = _post_recipe(
            client,
            headers,
            product_id=result["id"],
            source_product_id=source["id"],
            source_quantity_liters=10.0,
            net_weight_kg=1.90,
        )
        assert response.status_code == 400, response.text
        assert "litros de liquido" in response.json()["detail"]


def test_adr_recipe_skips_liquid_check_without_source_density(app) -> None:
    _setup_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        source = create_product(client, headers, sku="LOX-SRC-03", name="Oxigeno Liquido - LOX")
        result = create_product(client, headers, sku="O2-B10-03", name="Oxigeno Industrial B10 / 150BAR")

        response = _post_recipe(
            client,
            headers,
            product_id=result["id"],
            source_product_id=source["id"],
            source_quantity_liters=10.0,
            net_weight_kg=1.90,
        )
        assert response.status_code == 201, response.text
