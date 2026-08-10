from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.app.api.v1.core.common import CoreActionContext
from apps.api.app.api.v1.core.services.plugins import set_core_plugin_enabled
from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.lifecycle import bootstrap_app_state
from apps.api.app.kernel.plugins.persistent import sync_plugin_registry_state


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client: TestClient) -> dict[str, str]:
    response = login(client)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def enable_compras_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)

        build_ctx = app.state.plugin_runtime.context_builder
        # Enable in dependency order: productos → compras
        for plugin_id in ["productos", "compras"]:
            set_core_plugin_enabled(
                db,
                registry=app.state.plugin_registry,
                plugin_id=plugin_id,
                context_builder=build_ctx,
                is_enabled=True,
                action_context=CoreActionContext(
                    tenant_id=seeded_demo["tenant_id"],
                    branch_id=seeded_demo["branch_id"],
                    actor_user_id=seeded_demo["user_id"],
                    correlation_id=f"test-{plugin_id}-enable",
                    request_id=f"test-{plugin_id}-enable",
                ),
            )
            db.commit()
    bootstrap_app_state(app, app.state.settings)


class FakeStockConnector:
    def __init__(self):
        self.calls: list[dict] = []

    def purchase_in(self, **kwargs):
        self.calls.append(kwargs)
        return {"operation": "purchase_in", "balance": {}, "ledger_entry_id": "fake-ledger"}


# ── Tests ──

def test_compras_supplier_crud(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_compras_plugin(app, seeded)

    with TestClient(app) as client:
        headers = auth_headers(client)

        # Create supplier
        create_resp = client.post(
            "/api/v1/plugins/compras/purchase/suppliers",
            headers=headers,
            json={"name": "Proveedor Test", "email": "test@proveedor.com"},
        )
        assert create_resp.status_code == 201, create_resp.text
        supplier = create_resp.json()
        assert supplier["name"] == "Proveedor Test"
        assert supplier["is_active"] is True

        # List suppliers
        list_resp = client.get("/api/v1/plugins/compras/purchase/suppliers", headers=headers)
        assert list_resp.status_code == 200
        assert any(s["id"] == supplier["id"] for s in list_resp.json())

        # Update supplier
        update_resp = client.patch(
            f"/api/v1/plugins/compras/purchase/suppliers/{supplier['id']}",
            headers=headers,
            json={"name": "Proveedor Actualizado"},
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["name"] == "Proveedor Actualizado"

        # Disable supplier
        disable_resp = client.post(
            f"/api/v1/plugins/compras/purchase/suppliers/{supplier['id']}/disable",
            headers=headers,
        )
        assert disable_resp.status_code == 200
        assert disable_resp.json()["is_active"] is False

        # Search supplier
        search_resp = client.get(
            "/api/v1/plugins/compras/purchase/suppliers?search=Actualizado",
            headers=headers,
        )
        assert search_resp.status_code == 200
        # Disabled, so not in default list
        search_active = client.get(
            "/api/v1/plugins/compras/purchase/suppliers?search=Actualizado",
            headers=headers,
        )
        assert len(search_active.json()) == 0


def test_compras_order_lifecycle(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_compras_plugin(app, seeded)

    with TestClient(app) as client:
        headers = auth_headers(client)

        # Create supplier first
        supplier_resp = client.post(
            "/api/v1/plugins/compras/purchase/suppliers",
            headers=headers,
            json={"name": "Supplier Order Test"},
        )
        supplier_id = supplier_resp.json()["id"]

        # Create order DRAFT
        order_resp = client.post(
            "/api/v1/plugins/compras/purchase/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [
                    {"product_id": "test-prod-1", "quantity": 10, "unit_cost": 25.5},
                    {"product_id": "test-prod-2", "quantity": 5, "unit_cost": 100.0},
                ],
                "notes": "Orden de prueba",
            },
        )
        assert order_resp.status_code == 201, order_resp.text
        order = order_resp.json()
        assert order["status"] == "DRAFT"

        # Get detail
        detail_resp = client.get(
            f"/api/v1/plugins/compras/purchase/orders/{order['id']}",
            headers=headers,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail["items"]) == 2
        assert detail["items"][0]["received_qty"] == 0

        # Confirm order
        confirm_resp = client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order['id']}/confirm",
            headers=headers,
        )
        assert confirm_resp.status_code == 200
        assert confirm_resp.json()["status"] == "ORDERED"

        # Cannot edit after confirm
        edit_resp = client.patch(
            f"/api/v1/plugins/compras/purchase/orders/{order['id']}",
            headers=headers,
            json={"notes": "Cambio no permitido"},
        )
        assert edit_resp.status_code == 400

        # Cancel order
        cancel_resp = client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order['id']}/cancel",
            headers=headers,
        )
        assert cancel_resp.status_code == 200
        assert cancel_resp.json()["status"] == "CANCELLED"


def test_compras_order_receive(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_compras_plugin(app, seeded)

    fake_stock = FakeStockConnector()

    with TestClient(app) as client:
        headers = auth_headers(client)

        # Create supplier
        supplier_resp = client.post(
            "/api/v1/plugins/compras/purchase/suppliers",
            headers=headers,
            json={"name": "Supplier Receive Test"},
        )
        supplier_id = supplier_resp.json()["id"]

        # Create and confirm order
        order_resp = client.post(
            "/api/v1/plugins/compras/purchase/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [
                    {"product_id": "prod-a", "quantity": 10, "unit_cost": 50.0},
                    {"product_id": "prod-b", "quantity": 5, "unit_cost": 30.0},
                ],
            },
        )
        order_id = order_resp.json()["id"]

        client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/confirm",
            headers=headers,
        )

        # Receive partial
        with patch(
            "plugins.commerce.purchase.backend.router._build_stock_connector",
            return_value=fake_stock,
        ):
            detail_before = client.get(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}",
                headers=headers,
            ).json()

            item_id = detail_before["items"][0]["id"]
            receive_resp = client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh-test",
                    "items": [{"purchase_item_id": item_id, "quantity": 6}],
                },
            )
            assert receive_resp.status_code == 200, receive_resp.text
            assert receive_resp.json()["status"] == "PARTIAL"

            detail_after = client.get(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}",
                headers=headers,
            ).json()
            assert detail_after["items"][0]["received_qty"] == 6
            assert detail_after["items"][1]["received_qty"] == 0
            assert len(detail_after["receipts"]) == 1

        # Verify stock connector was called
        assert len(fake_stock.calls) == 1
        call = fake_stock.calls[0]
        assert call["product_id"] == "prod-a"
        assert call["quantity"] == 6
        assert call["unit_cost"] == 50.0
        assert call["reference_type"] == "purchase_order"
        assert call["reference_id"] == order_id


def test_compras_order_receive_full_marks_received(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_compras_plugin(app, seeded)

    fake_stock = FakeStockConnector()

    with TestClient(app) as client:
        headers = auth_headers(client)

        supplier_resp = client.post(
            "/api/v1/plugins/compras/purchase/suppliers",
            headers=headers,
            json={"name": "Full Receive Test"},
        )
        supplier_id = supplier_resp.json()["id"]

        order_resp = client.post(
            "/api/v1/plugins/compras/purchase/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [{"product_id": "prod-x", "quantity": 3, "unit_cost": 10.0}],
            },
        )
        order_id = order_resp.json()["id"]

        client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/confirm",
            headers=headers,
        )

        detail = client.get(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}",
            headers=headers,
        ).json()
        item_id = detail["items"][0]["id"]

        with patch(
            "plugins.commerce.purchase.backend.router._build_stock_connector",
            return_value=fake_stock,
        ):
            receive_resp = client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh-full",
                    "items": [{"purchase_item_id": item_id, "quantity": 3}],
                },
            )
            assert receive_resp.status_code == 200
            assert receive_resp.json()["status"] == "RECEIVED"


def test_compras_order_receive_excess_quantity_rejected(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_compras_plugin(app, seeded)

    fake_stock = FakeStockConnector()

    with TestClient(app) as client:
        headers = auth_headers(client)

        supplier_resp = client.post(
            "/api/v1/plugins/compras/purchase/suppliers",
            headers=headers,
            json={"name": "Excess Test"},
        )
        supplier_id = supplier_resp.json()["id"]

        order_resp = client.post(
            "/api/v1/plugins/compras/purchase/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [{"product_id": "prod-e", "quantity": 5, "unit_cost": 10.0}],
            },
        )
        order_id = order_resp.json()["id"]

        client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/confirm",
            headers=headers,
        )

        detail = client.get(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}",
            headers=headers,
        ).json()
        item_id = detail["items"][0]["id"]

        with patch(
            "plugins.commerce.purchase.backend.router._build_stock_connector",
            return_value=fake_stock,
        ):
            receive_resp = client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh-excess",
                    "items": [{"purchase_item_id": item_id, "quantity": 10}],
                },
            )
            assert receive_resp.status_code == 400


def test_compras_cannot_receive_draft_order(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_compras_plugin(app, seeded)

    fake_stock = FakeStockConnector()

    with TestClient(app) as client:
        headers = auth_headers(client)

        supplier_resp = client.post(
            "/api/v1/plugins/compras/purchase/suppliers",
            headers=headers,
            json={"name": "Draft Test"},
        )
        supplier_id = supplier_resp.json()["id"]

        order_resp = client.post(
            "/api/v1/plugins/compras/purchase/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [{"product_id": "prod-d", "quantity": 1, "unit_cost": 1.0}],
            },
        )
        order_id = order_resp.json()["id"]
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()

        with patch(
            "plugins.commerce.purchase.backend.router._build_stock_connector",
            return_value=fake_stock,
        ):
            receive_resp = client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh-draft",
                    "items": [{"purchase_item_id": detail["items"][0]["id"], "quantity": 1}],
                },
            )
            assert receive_resp.status_code == 400
