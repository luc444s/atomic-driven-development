from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.audit.models import AuditLog
from systutor.kernel.events.models import EventLog
from systutor.kernel.plugins.persistent import sync_plugin_registry_state

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.tests.test_logistics_plugin import enable_crm_plugin, enable_logistics_plugin
from apps.api.tests.test_productos_plugin import enable_productos_plugin


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(
    client: TestClient,
    email: str = "admin@example.com",
    password: str = "ChangeMe123!",
) -> dict[str, str]:
    response = login(client, email=email, password=password)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def enable_stock_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        set_core_plugin_enabled(
            db,
            registry=app.state.plugin_registry,
            plugin_id="stock",
            context_builder=app.state.plugin_runtime.context_builder,
            is_enabled=True,
            action_context=CoreActionContext(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                actor_user_id=seeded_demo["user_id"],
                correlation_id="test-stock-enable",
                request_id="test-stock-enable",
            ),
        )
        db.commit()
    bootstrap_app_state(app, app.state.settings)


def create_warehouse(
    client: TestClient, headers: dict[str, str], *, code: str, name: str
) -> dict[str, str]:
    return create_warehouse_with_branch(
        client,
        headers,
        code=code,
        name=name,
        branch_id=None,
    )


def create_warehouse_with_branch(
    client: TestClient,
    headers: dict[str, str],
    *,
    code: str,
    name: str,
    branch_id: str | None,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={
            "code": code,
            "name": name,
            "branch_id": branch_id,
            "address": None,
            "phone": None,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_product(client: TestClient, headers: dict[str, str]) -> dict[str, str]:
    category = client.post(
        "/api/v1/plugins/productos/catalog/categories",
        headers=headers,
        json={"code": "ENERGIA", "name": "Energia", "description": "Linea energia"},
    ).json()
    line = client.post(
        "/api/v1/plugins/productos/catalog/lines",
        headers=headers,
        json={
            "code": "GASES",
            "name": "Gases",
            "category_id": category["id"],
            "description": "Productos de gas",
        },
    ).json()
    subline = client.post(
        "/api/v1/plugins/productos/catalog/subline",
        headers=headers,
        json={"code": "GLP", "name": "GLP", "line_id": line["id"]},
    ).json()
    brand = client.post(
        "/api/v1/plugins/productos/catalog/brands",
        headers=headers,
        json={"code": "GENERICA", "name": "Generica", "description": "Marca general"},
    ).json()
    unit = client.post(
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
    ).json()
    subcategory = client.post(
        "/api/v1/plugins/productos/catalog/subcategories",
        headers=headers,
        json={"code": "GAS", "name": "Gas", "description": "Subcategoria gas"},
    ).json()
    response = client.post(
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
    assert response.status_code == 201, response.text
    return response.json()


def create_active_base_cost(
    client: TestClient, headers: dict[str, str], *, product_id: str, amount: float
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/plugins/productos/products/{product_id}/costs",
        headers=headers,
        json={"cost_type": "BASE", "amount": amount, "currency": "PEN"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _setup_stock_env(app):
    """Set up demo seed + all required plugins for stock tests."""
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    return seeded_demo


def test_stock_plugin_inventory_flow(app) -> None:
    seeded_demo = _setup_stock_env(app)

    with TestClient(app) as client:
        headers = auth_headers(client)
        origin_warehouse = create_warehouse(client, headers, code="CENTRAL", name="Central")
        branch_response = client.post(
            "/api/v1/core/branches",
            headers=headers,
            json={"name": "Route Branch", "code": "ROUTE"},
        )
        assert branch_response.status_code == 201, branch_response.text
        destination_branch_id = branch_response.json()["id"]
        destination_warehouse = create_warehouse_with_branch(
            client,
            headers,
            code="RUTA",
            name="Ruta",
            branch_id=destination_branch_id,
        )
        product = create_product(client, headers)

        config_response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": origin_warehouse["id"],
                "min_quantity": 12,
                "max_quantity": 50,
                "is_active": True,
            },
        )
        assert config_response.status_code == 200, config_response.text
        assert config_response.json()["min_quantity"] == 12

        first_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": origin_warehouse["id"],
                "quantity": 10,
                "unit_cost": 5.0,
                "reason": "Carga inicial",
            },
        )
        assert first_adjust_response.status_code == 201, first_adjust_response.text
        assert first_adjust_response.json()["quantity"] == 10

        idempotent_adjust_payload = {
            "product_id": product["id"],
            "warehouse_id": origin_warehouse["id"],
            "quantity": 5,
            "unit_cost": 5.0,
            "reason": "Ajuste lote A",
            "idempotency_key": "adj-1",
        }
        second_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json=idempotent_adjust_payload,
        )
        assert second_adjust_response.status_code == 201, second_adjust_response.text
        assert second_adjust_response.json()["quantity"] == 15

        repeated_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json=idempotent_adjust_payload,
        )
        assert repeated_adjust_response.status_code == 201, repeated_adjust_response.text
        assert repeated_adjust_response.json()["quantity"] == 15

        transfer_payload = {
            "product_id": product["id"],
            "from_warehouse_id": origin_warehouse["id"],
            "to_warehouse_id": destination_warehouse["id"],
            "quantity": 4,
            "unit_cost": 5.0,
            "notes": "Traslado de reparto",
            "idempotency_key": "trx-1",
        }
        transfer_response = client.post(
            "/api/v1/plugins/stock/transfer",
            headers=headers,
            json=transfer_payload,
        )
        assert transfer_response.status_code == 201, transfer_response.text
        transfer_result = transfer_response.json()
        assert transfer_result["from_balance"]["quantity"] == 11
        assert transfer_result["to_balance"]["quantity"] == 4

        repeated_transfer_response = client.post(
            "/api/v1/plugins/stock/transfer",
            headers=headers,
            json=transfer_payload,
        )
        assert repeated_transfer_response.status_code == 201, repeated_transfer_response.text
        assert repeated_transfer_response.json()["from_balance"]["quantity"] == 11
        assert repeated_transfer_response.json()["to_balance"]["quantity"] == 4

        balance_detail_response = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{origin_warehouse['id']}",
            headers=headers,
        )
        assert balance_detail_response.status_code == 200, balance_detail_response.text
        assert balance_detail_response.json()["is_below_min"] is True

        low_stock_response = client.get(
            "/api/v1/plugins/stock/balance?below_min_only=true",
            headers=headers,
        )
        assert low_stock_response.status_code == 200, low_stock_response.text
        assert len(low_stock_response.json()["items"]) == 1
        assert low_stock_response.json()["items"][0]["warehouse_id"] == origin_warehouse["id"]

        ledger_response = client.get(
            f"/api/v1/plugins/stock/ledger/{product['id']}/{origin_warehouse['id']}",
            headers=headers,
        )
        assert ledger_response.status_code == 200, ledger_response.text
        operations = [item["operation"] for item in ledger_response.json()]
        assert operations == ["transfer_out", "adjust", "adjust"]

        invalid_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": "missing-warehouse",
                "quantity": 1,
                "unit_cost": 5.0,
                "reason": "Prueba inválida",
            },
        )
        assert invalid_adjust_response.status_code == 404, invalid_adjust_response.text

        role_response = client.post(
            "/api/v1/core/roles",
            headers=headers,
            json={"name": "stock-reader", "permission_names": ["stock.balance.read"]},
        )
        assert role_response.status_code == 201, role_response.text
        limited_role_id = role_response.json()["id"]

        user_response = client.post(
            "/api/v1/core/users",
            headers=headers,
            json={
                "name": "Stock Reader",
                "email": "stock-reader@example.com",
                "password": "StockReader123!",
                "branch_id": destination_branch_id,
                "role_ids": [limited_role_id],
                "warehouse_ids": [origin_warehouse["id"]],
            },
        )
        assert user_response.status_code == 201, user_response.text
        assert user_response.json()["warehouse_ids"] == [origin_warehouse["id"]]

        limited_headers = auth_headers(
            client,
            email="stock-reader@example.com",
            password="StockReader123!",
        )
        scoped_catalog_response = client.get(
            "/api/v1/plugins/stock/catalog/warehouses",
            headers=limited_headers,
        )
        assert scoped_catalog_response.status_code == 200, scoped_catalog_response.text
        assert [item["id"] for item in scoped_catalog_response.json()] == [origin_warehouse["id"]]

        allowed_balance_response = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{origin_warehouse['id']}",
            headers=limited_headers,
        )
        assert allowed_balance_response.status_code == 200, allowed_balance_response.text

        denied_balance_response = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{destination_warehouse['id']}",
            headers=limited_headers,
        )
        assert denied_balance_response.status_code == 403, denied_balance_response.text

    with app.state.session_factory() as db:
        stock_events = list(
            db.scalars(
                select(EventLog)
                .where(EventLog.module == "stock")
                .order_by(EventLog.occurred_at.asc())
            )
        )
        stock_audits = list(
            db.scalars(
                select(AuditLog)
                .where(AuditLog.module == "stock")
                .order_by(AuditLog.occurred_at.asc())
            )
        )

    event_names = [item.event_name for item in stock_events]
    assert event_names.count("stock.balance.adjusted") == 2
    assert event_names.count("stock.transfer.completed") == 1
    transfer_event = next(
        item for item in stock_events if item.event_name == "stock.transfer.completed"
    )
    assert transfer_event.branch_id == seeded_demo["branch_id"]
    assert transfer_event.payload["from_branch_id"] == seeded_demo["branch_id"]
    assert transfer_event.payload["to_branch_id"] == destination_branch_id

    audit_actions = [item.action for item in stock_audits]
    assert "config.manage" in audit_actions
    assert audit_actions.count("balance.adjust") == 2
    assert audit_actions.count("transfer.create") == 1
    assert audit_actions.count("balance.read") >= 1


# ── edge case & validation tests ────────────────────────────────────────


def test_adjust_zero_quantity_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH1", name="Almacen 1")
        product = create_product(client, headers)
        response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 0,
                "reason": "cero",
            },
        )
        assert response.status_code == 400, response.text
        assert "diferente de cero" in response.text


def test_positive_adjust_without_unit_cost_uses_current_average_cost(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH-AC", name="Almacen Auto Cost")
        product = create_product(client, headers)
        seed = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 2,
                "unit_cost": 7.5,
                "reason": "Ingreso inicial valorizado",
            },
        )
        assert seed.status_code == 201, seed.text

        response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 3,
                "reason": "Ingreso por reconciliacion",
            },
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["quantity"] == 5
        assert payload["unit_cost"] == 7.5
        assert payload["total_cost"] == 37.5


def test_positive_adjust_without_unit_cost_and_zero_balance_uses_zero_legacy_cost(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH-NC", name="Almacen No Cost")
        product = create_product(client, headers)

        response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 3,
                "reason": "Ingreso sin costo explicito",
            },
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload["quantity"] == 3
        assert payload["unit_cost"] == 0
        assert payload["total_cost"] == 0


def test_adjust_insufficient_stock_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH2", name="Almacen 2")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 3,
                "unit_cost": 5.0,
            },
        )
        response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": -9,
                "reason": "reducir de más",
            },
        )
        assert response.status_code == 400, response.text
        assert "insuficiente" in response.text.lower()


def test_adjust_nonexistent_product_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH3", name="Almacen 3")
        response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": "nonexistent-product-id",
                "warehouse_id": warehouse["id"],
                "quantity": 5,
                "unit_cost": 5.0,
            },
        )
        assert response.status_code == 404, response.text


def test_multiple_sequential_adjustments(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH4", name="Almacen 4")
        product = create_product(client, headers)

        for q, uc in ((10, 5.0), (5, 5.0), (-3, None)):
            payload: dict = {
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": q,
            }
            if uc is not None:
                payload["unit_cost"] = uc
            response = client.post(
                "/api/v1/plugins/stock/adjust",
                headers=headers,
                json=payload,
            )
            assert response.status_code == 201, response.text

        detail = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert detail.status_code == 200, detail.text
        assert detail.json()["quantity"] == 12.0


def test_adjust_without_idempotency_creates_unique_references(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH5", name="Almacen 5")
        product = create_product(client, headers)

        for _ in range(3):
            r = client.post(
                "/api/v1/plugins/stock/adjust",
                headers=headers,
                json={
                    "product_id": product["id"],
                    "warehouse_id": warehouse["id"],
                    "quantity": 1,
                    "unit_cost": 5.0,
                },
            )
            assert r.status_code == 201, r.text

        ledger = client.get(
            f"/api/v1/plugins/stock/ledger/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        refs = [item["reference_id"] for item in ledger.json()]
        assert len(refs) == 3
        assert len(set(refs)) == 3


def test_transfer_same_warehouse_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH6", name="Almacen 6")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 10,
                "unit_cost": 5.0,
            },
        )
        response = client.post(
            "/api/v1/plugins/stock/transfer",
            headers=headers,
            json={
                "product_id": product["id"],
                "from_warehouse_id": warehouse["id"],
                "to_warehouse_id": warehouse["id"],
                "quantity": 2,
                "unit_cost": 5.0,
            },
        )
        assert response.status_code == 400, response.text
        assert "diferentes" in response.text.lower()


def test_transfer_insufficient_stock_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh_a = create_warehouse(client, headers, code="WH7A", name="Almacen 7A")
        wh_b = create_warehouse(client, headers, code="WH7B", name="Almacen 7B")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh_a["id"],
                "quantity": 5,
                "unit_cost": 5.0,
            },
        )
        response = client.post(
            "/api/v1/plugins/stock/transfer",
            headers=headers,
            json={
                "product_id": product["id"],
                "from_warehouse_id": wh_a["id"],
                "to_warehouse_id": wh_b["id"],
                "quantity": 20,
                "unit_cost": 5.0,
            },
        )
        assert response.status_code == 400, response.text
        assert "insuficiente" in response.text.lower()


def test_transfer_zero_quantity_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh_a = create_warehouse(client, headers, code="WH8A", name="Almacen 8A")
        wh_b = create_warehouse(client, headers, code="WH8B", name="Almacen 8B")
        product = create_product(client, headers)
        response = client.post(
            "/api/v1/plugins/stock/transfer",
            headers=headers,
            json={
                "product_id": product["id"],
                "from_warehouse_id": wh_a["id"],
                "to_warehouse_id": wh_b["id"],
                "quantity": 0,
            },
        )
        assert response.status_code == 422, response.text


def test_transfer_nonexistent_product_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh_a = create_warehouse(client, headers, code="WH9A", name="Almacen 9A")
        wh_b = create_warehouse(client, headers, code="WH9B", name="Almacen 9B")
        response = client.post(
            "/api/v1/plugins/stock/transfer",
            headers=headers,
            json={
                "product_id": "nonexistent",
                "from_warehouse_id": wh_a["id"],
                "to_warehouse_id": wh_b["id"],
                "quantity": 1,
                "unit_cost": 5.0,
            },
        )
        assert response.status_code == 404, response.text


def test_config_negative_min_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH10", name="Almacen 10")
        product = create_product(client, headers)
        response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": -1,
                "max_quantity": 10,
            },
        )
        assert response.status_code == 400, response.text
        assert "negativa" in response.text.lower()


def test_config_max_less_than_min_rejected(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH11", name="Almacen 11")
        product = create_product(client, headers)
        response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 20,
                "max_quantity": 5,
            },
        )
        assert response.status_code == 400, response.text
        assert "máxima no puede ser menor" in response.text.lower()


def test_config_update_existing(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH12", name="Almacen 12")
        product = create_product(client, headers)

        first = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 5,
                "max_quantity": 20,
            },
        )
        assert first.status_code == 200, first.text
        assert first.json()["min_quantity"] == 5.0

        second = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 10,
                "max_quantity": 30,
                "is_active": False,
            },
        )
        assert second.status_code == 200, second.text
        assert second.json()["min_quantity"] == 10.0
        assert second.json()["max_quantity"] == 30.0
        assert second.json()["is_active"] is False


def test_config_max_none(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH13", name="Almacen 13")
        product = create_product(client, headers)
        response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 5,
                "max_quantity": None,
            },
        )
        assert response.status_code == 200, response.text
        assert response.json()["max_quantity"] is None


def test_virtual_zero_balance(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH14", name="Almacen 14")
        product = create_product(client, headers)
        response = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["quantity"] == 0.0
        assert data["is_below_min"] is False


def test_balance_page_search(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH15", name="Almacen 15")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 7,
                "unit_cost": 5.0,
            },
        )
        client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 10,
                "max_quantity": 30,
            },
        )

        matches = client.get(
            "/api/v1/plugins/stock/balance",
            headers=headers,
            params={"q": product["sku"]},
        )
        assert matches.status_code == 200, matches.text
        assert len(matches.json()["items"]) >= 1

        below = client.get(
            "/api/v1/plugins/stock/balance",
            headers=headers,
            params={"below_min_only": "true"},
        )
        assert below.status_code == 200, below.text
        assert any(item["is_below_min"] for item in below.json()["items"])

        by_product = client.get(
            "/api/v1/plugins/stock/balance",
            headers=headers,
            params={"product_id": product["id"]},
        )
        assert by_product.status_code == 200, by_product.text
        assert len(by_product.json()["items"]) == 1

        by_warehouse = client.get(
            "/api/v1/plugins/stock/balance",
            headers=headers,
            params={"warehouse_id": warehouse["id"]},
        )
        assert by_warehouse.status_code == 200, by_warehouse.text
        assert len(by_warehouse.json()["items"]) == 1


def test_config_list(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH16", name="Almacen 16")
        product = create_product(client, headers)
        client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 8,
                "max_quantity": 20,
            },
        )
        all_configs = client.get("/api/v1/plugins/stock/config", headers=headers)
        assert all_configs.status_code == 200, all_configs.text
        assert len(all_configs.json()) >= 1

        by_product = client.get(
            "/api/v1/plugins/stock/config",
            headers=headers,
            params={"product_id": product["id"]},
        )
        assert by_product.status_code == 200, by_product.text
        assert len(by_product.json()) == 1
        assert by_product.json()[0]["min_quantity"] == 8.0


def test_negative_adjustment_works(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH17", name="Almacen 17")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 10,
                "unit_cost": 5.0,
            },
        )
        response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": -4,
                "reason": "devolución a proveedor",
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["quantity"] == 6.0


def test_product_balances_endpoint(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh_a = create_warehouse(client, headers, code="WH18A", name="Almacen 18A")
        wh_b = create_warehouse(client, headers, code="WH18B", name="Almacen 18B")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh_a["id"],
                "quantity": 3,
                "unit_cost": 5.0,
            },
        )
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh_b["id"],
                "quantity": 7,
                "unit_cost": 5.0,
            },
        )
        response = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        balances = response.json()
        assert len(balances) == 2
        quantities = {b["warehouse_id"]: b["quantity"] for b in balances}
        assert quantities[wh_a["id"]] == 3.0
        assert quantities[wh_b["id"]] == 7.0


def test_ledger_filtered_by_operation(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH19", name="Almacen 19")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 5,
                "unit_cost": 5.0,
            },
        )
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": -1,
            },
        )
        response = client.get(
            f"/api/v1/plugins/stock/ledger/{product['id']}",
            headers=headers,
            params={"operation": "adjust"},
        )
        assert response.status_code == 200, response.text
        items = response.json()
        assert len(items) == 2
        assert all(item["operation"] == "adjust" for item in items)


def test_catalog_warehouses_all(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        create_warehouse(client, headers, code="WH20A", name="Almacen 20A")
        create_warehouse(client, headers, code="WH20B", name="Almacen 20B")
        response = client.get(
            "/api/v1/plugins/stock/catalog/warehouses",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        codes = [item["code"] for item in response.json()]
        assert "WH20A" in codes
        assert "WH20B" in codes


def test_config_put_requires_warehouse_access(app) -> None:
    seeded_demo = _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh_a = create_warehouse(client, headers, code="WH21A", name="Almacen 21A")
        wh_b = create_warehouse(client, headers, code="WH21B", name="Almacen 21B")
        product = create_product(client, headers)

        role_resp = client.post(
            "/api/v1/core/roles",
            headers=headers,
            json={"name": "config-mgr", "permission_names": ["stock.config.manage"]},
        )
        role_id = role_resp.json()["id"]
        user_resp = client.post(
            "/api/v1/core/users",
            headers=headers,
            json={
                "name": "Config Mgr",
                "email": "config-mgr@example.com",
                "password": "ConfigMgr123!",
                "branch_id": seeded_demo["branch_id"],
                "role_ids": [role_id],
                "warehouse_ids": [wh_a["id"]],
            },
        )
        assert user_resp.status_code == 201, user_resp.text

        limited = auth_headers(client, email="config-mgr@example.com", password="ConfigMgr123!")

        allowed = client.put(
            "/api/v1/plugins/stock/config",
            headers=limited,
            json={
                "product_id": product["id"],
                "warehouse_id": wh_a["id"],
                "min_quantity": 1,
                "max_quantity": 10,
            },
        )
        assert allowed.status_code == 200, allowed.text

        denied = client.put(
            "/api/v1/plugins/stock/config",
            headers=limited,
            json={
                "product_id": product["id"],
                "warehouse_id": wh_b["id"],
                "min_quantity": 1,
                "max_quantity": 10,
            },
        )
        assert denied.status_code == 403, denied.text


def test_global_ledger(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        warehouse = create_warehouse(client, headers, code="WH22", name="Almacen 22")
        product = create_product(client, headers)
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 5,
                "unit_cost": 5.0,
                "reason": "inicial",
            },
        )
        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": -1,
                "reason": "correccion",
            },
        )

        all_entries = client.get(
            "/api/v1/plugins/stock/ledger",
            headers=headers,
            params={"limit": 10},
        )
        assert all_entries.status_code == 200, all_entries.text
        data = all_entries.json()
        assert len(data) == 2
        assert data[0]["created_at"] >= data[1]["created_at"]

        filtered = client.get(
            "/api/v1/plugins/stock/ledger",
            headers=headers,
            params={"operation": "adjust"},
        )
        assert filtered.status_code == 200, filtered.text
        assert len(filtered.json()) == 2


# ==============================================================================
# SPEC 0016.2 — Transactional gaps
# ==============================================================================


def test_allocate_and_consume_via_sale_out(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-ALLOC1", name="Alloc 1")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh["id"],
                "quantity": 100,
                "unit_cost": 10.0,
                "reason": "Stock inicial",
            },
        )

        alloc = client.post(
            "/api/v1/plugins/stock/allocate",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh["id"],
                "quantity": 30,
                "reference_type": "quote",
                "reference_id": "quote-1",
                "allocation_group_id": "group-a",
            },
        )
        assert alloc.status_code == 201, alloc.text
        a = alloc.json()
        assert a["status"] == "active"
        assert a["quantity"] == 30
        assert a["remaining_quantity"] == 30

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["reserved_quantity"] == 30
        assert b["available_quantity"] == 70

        sale = client.post(
            "/api/v1/plugins/stock/sale-out",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh["id"],
                "quantity": 20,
                "source": "allocation",
                "allocation_id": a["id"],
                "reference_type": "waybill",
                "reference_id": "wb-1",
            },
        )
        assert sale.status_code == 201, sale.text

        alloc_detail = client.get(
            f"/api/v1/plugins/stock/allocations/{a['id']}",
            headers=headers,
        )
        ad = alloc_detail.json()
        assert ad["status"] == "partially_consumed"
        assert ad["remaining_quantity"] == 10

        balance2 = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b2 = balance2.json()
        assert b2["quantity"] == 80
        assert b2["reserved_quantity"] == 10
        assert b2["available_quantity"] == 70

        sale2 = client.post(
            "/api/v1/plugins/stock/sale-out",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": wh["id"],
                "quantity": 10,
                "source": "allocation",
                "allocation_id": a["id"],
                "reference_type": "waybill",
                "reference_id": "wb-2",
            },
        )
        assert sale2.status_code == 201, sale2.text

        alloc_detail2 = client.get(
            f"/api/v1/plugins/stock/allocations/{a['id']}",
            headers=headers,
        )
        assert alloc_detail2.json()["status"] == "consumed"
        assert alloc_detail2.json()["remaining_quantity"] == 0


def test_release_allocation(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-REL", name="Release")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 50, "unit_cost": 5.0, "reason": "init",
            },
        )

        alloc = client.post(
            "/api/v1/plugins/stock/allocate",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 15, "reference_type": "quote",
                "reference_id": "q-r1",
            },
        )
        a_id = alloc.json()["id"]

        resp = client.post(
            f"/api/v1/plugins/stock/allocate/{a_id}/release",
            headers=headers,
            json={"reason": "cancelado por cliente"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "released"
        assert resp.json()["release_reason"] == "cancelado por cliente"

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["reserved_quantity"] == 0
        assert b["available_quantity"] == 50


def test_group_allocation_release(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-GRP", name="Group")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 30, "unit_cost": 8.0, "reason": "init",
            },
        )

        client.post(
            "/api/v1/plugins/stock/allocate",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 5, "reference_type": "quote",
                "reference_id": "q-g1", "allocation_group_id": "grp-1",
            },
        )
        client.post(
            "/api/v1/plugins/stock/allocate",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 7, "reference_type": "quote",
                "reference_id": "q-g2", "allocation_group_id": "grp-1",
            },
        )

        group_alloc = client.get(
            "/api/v1/plugins/stock/allocations/group/grp-1",
            headers=headers,
        )
        assert group_alloc.status_code == 200, group_alloc.text
        assert len(group_alloc.json()) == 2

        released = client.post(
            "/api/v1/plugins/stock/allocate/group/grp-1/release",
            headers=headers,
            json={"reason": "cotizacion expirada"},
        )
        assert released.status_code == 200, released.text
        assert len(released.json()) == 2
        assert all(a["status"] == "released" for a in released.json())


def test_sale_out_direct_skip_allocation(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-DIR", name="Direct")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 40, "unit_cost": 6.0, "reason": "init",
            },
        )

        sale = client.post(
            "/api/v1/plugins/stock/sale-out",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 10, "source": "direct",
                "reference_type": "waybill", "reference_id": "wb-d1",
            },
        )
        assert sale.status_code == 201, sale.text

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["quantity"] == 30
        assert b["reserved_quantity"] == 0
        assert b["available_quantity"] == 30


def test_purchase_in_with_cost_tracking(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-COST", name="Cost")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/purchase-in",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 10, "unit_cost": 5.0,
                "reference_type": "purchase_order", "reference_id": "po-1",
            },
        )

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["quantity"] == 10
        assert b["total_cost"] == 50.0
        assert b["unit_cost"] == 5.0

        client.post(
            "/api/v1/plugins/stock/purchase-in",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 10, "unit_cost": 7.0,
                "reference_type": "purchase_order", "reference_id": "po-2",
            },
        )

        balance2 = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b2 = balance2.json()
        assert b2["quantity"] == 20
        assert b2["total_cost"] == 120.0
        assert b2["unit_cost"] == 6.0

        ledger = client.get(
            "/api/v1/plugins/stock/ledger",
            headers=headers,
            params={"operation": "purchase_in", "limit": 10},
        )
        entries = ledger.json()
        assert len(entries) == 2
        assert entries[0]["unit_cost"] is not None
        assert entries[0]["cost_after"] is not None


def test_return_in_uses_historical_cost(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-RET", name="Return")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/purchase-in",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 100, "unit_cost": 10.0,
                "reference_type": "purchase_order", "reference_id": "po-ret",
            },
        )

        sale = client.post(
            "/api/v1/plugins/stock/sale-out",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 10, "source": "direct",
                "reference_type": "waybill", "reference_id": "wb-ret",
            },
        )
        assert sale.status_code == 201, sale.text
        original_sale_ledger_id = sale.json()["ledger_entry_id"]

        resp = client.post(
            "/api/v1/plugins/stock/return-in",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 5, "original_sale_ledger_id": original_sale_ledger_id,
                "reference_type": "return_note", "reference_id": "rn-1",
            },
        )
        assert resp.status_code == 201, resp.text

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["quantity"] == 95
        assert b["unit_cost"] == pytest.approx(10.0, abs=0.01)

        r_ledger = client.get(
            "/api/v1/plugins/stock/ledger",
            headers=headers,
            params={"operation": "return_in", "limit": 1},
        )
        re = r_ledger.json()
        assert len(re) == 1
        assert re[0]["unit_cost"] == 10.0


def test_damage_out_and_negative_stock_warning(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-DMG", name="Damage")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 20, "unit_cost": 5.0, "reason": "init",
            },
        )

        resp = client.post(
            "/api/v1/plugins/stock/damage-out",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 3, "reason": "rotura en traslado",
                "reference_type": "damage_report", "reference_id": "dr-1",
            },
        )
        assert resp.status_code == 201, resp.text

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["quantity"] == 17

        l_resp = client.get(
            "/api/v1/plugins/stock/ledger",
            headers=headers,
            params={"operation": "damage_out", "limit": 1},
        )
        assert l_resp.json()[0]["quantity"] == -3

        overkill = client.post(
            "/api/v1/plugins/stock/damage-out",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 100, "reason": "test",
                "reference_type": "damage_report", "reference_id": "dr-2",
            },
        )
        assert overkill.status_code == 400


def test_adjust_positive_requires_active_product_cost(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-REQ", name="Required")
        product = create_product(client, headers)

        resp = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 5,
            },
        )
        assert resp.status_code == 400, resp.text
        assert "costo unitario activo" in resp.text

        create_active_base_cost(client, headers, product_id=product["id"], amount=10.0)
        ok = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 5,
            },
        )
        assert ok.status_code == 201, ok.text


def test_available_quantity_in_balance_read(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-AVAIL", name="Avail")
        product = create_product(client, headers)

        client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 100, "unit_cost": 5.0, "reason": "init",
            },
        )

        client.post(
            "/api/v1/plugins/stock/allocate",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 25, "reference_type": "quote",
                "reference_id": "q-av1",
            },
        )

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        b = balance.json()
        assert b["quantity"] == 100
        assert b["reserved_quantity"] == 25
        assert b["available_quantity"] == 75


def test_config_allow_negative_stock(app) -> None:
    _setup_stock_env(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        wh = create_warehouse(client, headers, code="WH-NEG", name="NegStock")
        product = create_product(client, headers)

        client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "min_quantity": 0, "allow_negative_stock": True, "is_active": True,
            },
        )

        resp = client.post(
            "/api/v1/plugins/stock/sale-out",
            headers=headers,
            json={
                "product_id": product["id"], "warehouse_id": wh["id"],
                "quantity": 5, "source": "direct",
                "reference_type": "waybill", "reference_id": "wb-neg",
            },
        )
        assert resp.status_code == 201, resp.text

        balance = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{wh['id']}",
            headers=headers,
        )
        assert balance.json()["quantity"] == -5
