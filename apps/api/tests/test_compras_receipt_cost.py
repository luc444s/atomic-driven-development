from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.plugins.persistent import sync_plugin_registry_state

from apps.api.app.commands.seed_demo import seed_demo_data


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {login(client).json()['access_token']}"}


def enable_compras_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        build_ctx = app.state.plugin_runtime.context_builder
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
    def purchase_in(self, **kwargs):
        return {"operation": "purchase_in", "balance": {}, "ledger_entry_id": "fake-ledger"}


def _make_order(client, headers, item):
    supplier_id = client.post(
        "/api/v1/plugins/compras/purchase/suppliers",
        headers=headers,
        json={"name": "Supplier Cost"},
    ).json()["id"]
    order_id = client.post(
        "/api/v1/plugins/compras/purchase/orders",
        headers=headers,
        json={"supplier_id": supplier_id, "items": [item]},
    ).json()["id"]
    client.post(f"/api/v1/plugins/compras/purchase/orders/{order_id}/confirm", headers=headers)
    return order_id


def _receive(client, headers, order_id, item_id, qty, accepted, rejected, cost_lines=None):
    with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=FakeStockConnector()):
        resp = client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
            headers=headers,
            json={
                "warehouse_id": "wh",
                "items": [{"purchase_item_id": item_id, "quantity": qty, "qty_accepted": accepted, "qty_rejected": rejected}],
                "cost_lines": cost_lines,
            },
        )
    assert resp.status_code == 200, resp.text


def test_receipt_cost_lines_sum_to_extra_total(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-k1", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive(client, headers, order_id, item_id, 8, 8, 0, cost_lines=[
            {"cost_type": "FLETE", "amount": 100},
            {"cost_type": "ARANCEL", "amount": 50},
        ])
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        assert receipt["extra_total"] == 150
        assert len(receipt["cost_lines"]) == 2


def test_receipt_unit_cost_real_prorates_extras(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-k2", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive(client, headers, order_id, item_id, 8, 8, 0, cost_lines=[
            {"cost_type": "FLETE", "amount": 100},
            {"cost_type": "ARANCEL", "amount": 50},
        ])
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        # item_cost = 100 * 0.8 = 80; extra = 150; real = 230; unit_real = 230/8 = 28.75
        assert receipt["real_total"] == 230
        assert receipt["unit_cost_real"] == 28.75


def test_receipt_no_cost_lines_keeps_unit_cost(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-k3", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive(client, headers, order_id, item_id, 10, 10, 0)
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        assert receipt["extra_total"] == 0
        assert receipt["unit_cost_real"] == 10.0


def test_receipt_cost_zero_accepted_returns_null_unit_real(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-k4", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive(client, headers, order_id, item_id, 10, 0, 10, cost_lines=[
            {"cost_type": "ARANCEL", "amount": 40},
        ])
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        assert receipt["qty_accepted"] == 0
        assert receipt["extra_total"] == 40
        assert receipt["unit_cost_real"] is None
