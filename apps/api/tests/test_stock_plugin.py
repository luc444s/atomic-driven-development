from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.api.v1.core.common import CoreActionContext
from apps.api.app.api.v1.core.services.plugins import set_core_plugin_enabled
from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.lifecycle import bootstrap_app_state
from apps.api.app.kernel.audit.models import AuditLog
from apps.api.app.kernel.events.models import EventLog
from apps.api.app.kernel.plugins.persistent import sync_plugin_registry_state
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
            "delivery_time": "24h",
            "is_service": False,
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_stock_plugin_inventory_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )

    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)

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
                "reason": "Carga inicial",
            },
        )
        assert first_adjust_response.status_code == 201, first_adjust_response.text
        assert first_adjust_response.json()["quantity"] == 10

        idempotent_adjust_payload = {
            "product_id": product["id"],
            "warehouse_id": origin_warehouse["id"],
            "quantity": 5,
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
