from __future__ import annotations

from io import BytesIO

from fastapi.testclient import TestClient
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.plugins.persistent import sync_plugin_registry_state

from apps.api.app.commands.seed_demo import seed_demo_data


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client: TestClient) -> dict[str, str]:
    response = login(client)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def enable_productos_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        set_core_plugin_enabled(
            db,
            registry=app.state.plugin_registry,
            plugin_id="productos",
            context_builder=app.state.plugin_runtime.context_builder,
            is_enabled=True,
            action_context=CoreActionContext(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                actor_user_id=seeded_demo["user_id"],
                correlation_id="test-productos-enable",
                request_id="test-productos-enable",
            ),
        )
        db.commit()
    bootstrap_app_state(app, app.state.settings)


def test_productos_plugin_full_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        conditions_response = client.get(
            "/api/v1/plugins/productos/catalog/conditions",
            headers=headers,
        )
        assert conditions_response.status_code == 200, conditions_response.text
        assert any(item["code"] == "PRODUCTO" for item in conditions_response.json())

        status_response = client.get(
            "/api/v1/plugins/productos/catalog/status",
            headers=headers,
        )
        assert status_response.status_code == 200, status_response.text
        assert any(item["code"] == "ACTIVO" for item in status_response.json())

        category_response = client.post(
            "/api/v1/plugins/productos/catalog/categories",
            headers=headers,
            json={"code": "ENERGIA", "name": "Energia", "description": "Linea de energia"},
        )
        assert category_response.status_code == 201, category_response.text
        category = category_response.json()

        line_response = client.post(
            "/api/v1/plugins/productos/catalog/lines",
            headers=headers,
            json={
                "code": "GASES",
                "name": "Gases",
                "category_id": category["id"],
                "description": "Productos de gas",
            },
        )
        assert line_response.status_code == 201, line_response.text
        line = line_response.json()

        subline_response = client.post(
            "/api/v1/plugins/productos/catalog/subline",
            headers=headers,
            json={"code": "GLP", "name": "GLP", "line_id": line["id"]},
        )
        assert subline_response.status_code == 201, subline_response.text
        subline = subline_response.json()

        brand_response = client.post(
            "/api/v1/plugins/productos/catalog/brands",
            headers=headers,
            json={"code": "GENERICA", "name": "Generica", "description": "Marca general"},
        )
        assert brand_response.status_code == 201, brand_response.text
        brand = brand_response.json()

        unit_response = client.post(
            "/api/v1/plugins/productos/catalog/units",
            headers=headers,
            json={
                "code": "KG",
                "name": "Kilogramo",
                "equivalencia": 1,
                "m3_factor": None,
                "liter_factor": None,
                "kg_factor": 1,
            },
        )
        assert unit_response.status_code == 201, unit_response.text
        unit = unit_response.json()

        subcategory_response = client.post(
            "/api/v1/plugins/productos/catalog/subcategories",
            headers=headers,
            json={"code": "GAS", "name": "Gas", "description": "Subcategoria gas"},
        )
        assert subcategory_response.status_code == 201, subcategory_response.text
        subcategory = subcategory_response.json()

        product_response = client.post(
            "/api/v1/plugins/productos/products",
            headers=headers,
            json={
                "legacy_id": 100,
                "sku": "GLP10",
                "name": "GLP 10kg",
                "description": "Gas licuado 10kg",
                "short_description": "GLP10",
                "line_id": line["id"],
                "subline_id": subline["id"],
                "brand_id": brand["id"],
                "unit_id": unit["id"],
                "box_unit_id": unit["id"],
                "qty_per_box": 1,
                "subcategory_id": subcategory["id"],
                "status_code": "ACTIVO",
                "condition_code": "GAS",
                "weight_kg": 10,
                "content_m3": 0.1,
                "country_code": "PE",
                "is_service": False,
                "is_active": True,
            },
        )
        assert product_response.status_code == 201, product_response.text
        product = product_response.json()

        barcode_response = client.post(
            f"/api/v1/plugins/productos/products/{product['id']}/barcodes",
            headers=headers,
            json={
                "barcode_type": "INTERNAL",
                "barcode": "7750123456789",
                "is_primary": True,
                "is_active": True,
            },
        )
        assert barcode_response.status_code == 201, barcode_response.text

        price_response = client.post(
            f"/api/v1/plugins/productos/products/{product['id']}/prices",
            headers=headers,
            json={
                "price_list": "UNITARIO",
                "amount": 45.5,
                "currency": "USD",
                "valid_from": "2026-01-01",
            },
        )
        assert price_response.status_code == 201, price_response.text

        cost_response = client.post(
            f"/api/v1/plugins/productos/products/{product['id']}/costs",
            headers=headers,
            json={
                "cost_type": "ACTUAL",
                "amount": 32.0,
                "currency": "USD",
                "valid_from": "2026-01-01",
            },
        )
        assert cost_response.status_code == 201, cost_response.text

        tax_response = client.put(
            f"/api/v1/plugins/productos/products/{product['id']}/tax",
            headers=headers,
            json={
                "configs": [
                    {
                        "tax_type": "IGV",
                        "value": None,
                        "is_exempt": True,
                        "valid_from": "2026-01-01",
                    },
                    {
                        "tax_type": "PERCEPCION",
                        "value": 2.5,
                        "is_exempt": False,
                        "valid_from": "2026-01-01",
                    },
                    {
                        "tax_type": "COMISION_EXT",
                        "value": 1.0,
                        "is_exempt": False,
                        "valid_from": "2026-01-01",
                    },
                ]
            },
        )
        assert tax_response.status_code == 200, tax_response.text
        assert len(tax_response.json()) == 3

        adr_response = client.post(
            f"/api/v1/plugins/productos/products/{product['id']}/adr",
            headers=headers,
            json={
                "category": "2",
                "packaging_type": "CILINDRO",
                "net_weight_kg": 10,
                "net_volume_m3": 0.1,
                "un_number": "1075",
                "cargo_description": "Gas licuado de petroleo",
                "label": "2.1",
                "tunnel_restriction": "B/D",
                "subline_id": subline["id"],
                "factor": 1,
                "points": 20,
                "unit_measure": "KG",
                "valid_from": "2026-01-01",
            },
        )
        assert adr_response.status_code == 201, adr_response.text

        promotion_response = client.post(
            f"/api/v1/plugins/productos/products/{product['id']}/promotions",
            headers=headers,
            json={
                "name": "Promo abril",
                "condition": "PORCENTAJE",
                "qty_required": None,
                "discount_percent": 10,
                "unit_price": None,
                "box_price": None,
                "valid_from": "2026-01-01",
                "valid_to": None,
                "is_active": True,
            },
        )
        assert promotion_response.status_code == 201, promotion_response.text

        media_response = client.post(
            f"/api/v1/plugins/productos/products/{product['id']}/media?media_type=PHOTO&is_primary=true",
            headers=headers,
            files={"file": ("producto.txt", BytesIO(b"demo file"), "text/plain")},
        )
        assert media_response.status_code == 201, media_response.text

        detail_response = client.get(
            f"/api/v1/plugins/productos/products/{product['id']}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        detail = detail_response.json()
        assert detail["sku"] == "GLP10"
        assert len(detail["barcodes"]) == 1
        assert len(detail["prices"]) == 1
        assert len(detail["costs"]) == 1
        assert len(detail["taxes"]) == 3
        assert len(detail["adr_configs"]) == 1
        assert len(detail["media_items"]) == 1
        assert len(detail["promotions"]) == 1

        search_response = client.get(
            "/api/v1/plugins/productos/products/search?q=GLP",
            headers=headers,
        )
        assert search_response.status_code == 200, search_response.text
        assert search_response.json()[0]["id"] == product["id"]

        list_response = client.get(
            "/api/v1/plugins/productos/products?limit=10&offset=0",
            headers=headers,
        )
        assert list_response.status_code == 200, list_response.text
        assert list_response.json()["total"] >= 1


def test_productos_list_search_uses_or_between_sku_and_name(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        category = client.post(
            "/api/v1/plugins/productos/catalog/categories",
            headers=headers,
            json={"code": "CAT-SEARCH", "name": "Categoria Search", "description": "Test"},
        ).json()
        line = client.post(
            "/api/v1/plugins/productos/catalog/lines",
            headers=headers,
            json={
                "code": "LIN-SEARCH",
                "name": "Linea Search",
                "category_id": category["id"],
                "description": "Test",
            },
        ).json()
        subline = client.post(
            "/api/v1/plugins/productos/catalog/subline",
            headers=headers,
            json={"code": "SUB-SEARCH", "name": "Sublinea Search", "line_id": line["id"]},
        ).json()
        unit = client.post(
            "/api/v1/plugins/productos/catalog/units",
            headers=headers,
            json={
                "code": "U-SEARCH",
                "name": "Unidad Search",
                "equivalencia": 1,
                "m3_factor": 0,
                "liter_factor": 0,
                "kg_factor": 1,
            },
        ).json()
        product = client.post(
            "/api/v1/plugins/productos/products",
            headers=headers,
            json={
                "sku": "SKU-NUMERICO-1",
                "name": "Gas Especial B10 / 200BAR",
                "description": "Nombre distinto del sku",
                "line_id": line["id"],
                "subline_id": subline["id"],
                "unit_id": unit["id"],
                "status_code": "ACTIVO",
                "condition_code": "GAS",
            },
        )
        assert product.status_code == 201, product.text
        product_data = product.json()

        listed = client.get(
            "/api/v1/plugins/productos/products?limit=20&offset=0"
            "&sku=Gas%20Especial&name=Gas%20Especial",
            headers=headers,
        )
        assert listed.status_code == 200, listed.text
        assert listed.json()["total"] >= 1
        assert any(
            item["id"] == product_data["id"] for item in listed.json()["items"]
        )
