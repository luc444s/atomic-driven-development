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
    def __init__(self):
        self.calls: list[dict] = []

    def purchase_in(self, **kwargs):
        self.calls.append(kwargs)
        return {"operation": "purchase_in", "balance": {}, "ledger_entry_id": "fake-ledger"}


def _make_order(client, headers, item):
    supplier_id = client.post(
        "/api/v1/plugins/compras/purchase/suppliers",
        headers=headers,
        json={"name": "Supplier Comercial"},
    ).json()["id"]
    order_id = client.post(
        "/api/v1/plugins/compras/purchase/orders",
        headers=headers,
        json={"supplier_id": supplier_id, "items": [item]},
    ).json()["id"]
    client.post(f"/api/v1/plugins/compras/purchase/orders/{order_id}/confirm", headers=headers)
    return order_id


def test_receive_accept_reject_sums_to_received(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    fake = FakeStockConnector()
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-c1", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=fake):
            resp = client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={"warehouse_id": "wh", "items": [{"purchase_item_id": item_id, "quantity": 10, "qty_accepted": 6, "qty_rejected": 3}]},
            )
        assert resp.status_code == 400, resp.text


def test_receive_defaults_accepted_equals_received(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    fake = FakeStockConnector()
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-c2", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=fake):
            client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={"warehouse_id": "wh", "items": [{"purchase_item_id": item_id, "quantity": 10}]},
            )
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        receipt = detail["receipts"][0]
        assert receipt["qty_accepted"] == 10
        assert receipt["qty_rejected"] == 0


def test_receive_derives_difference_type_faltante_dano(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    fake = FakeStockConnector()
    with TestClient(app) as client:
        headers = auth_headers(client)
        # FALTANTE: recibir menos que ordenado
        order_id = _make_order(client, headers, {"product_id": "prod-c3", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=fake):
            client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={"warehouse_id": "wh", "items": [{"purchase_item_id": item_id, "quantity": 8, "qty_accepted": 8, "qty_rejected": 0}]},
            )
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        assert receipt["difference_type"] == "FALTANTE"

        # DANO: recibir con rechazo
        order_id = _make_order(client, headers, {"product_id": "prod-c4", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=fake):
            client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={"warehouse_id": "wh", "items": [{"purchase_item_id": item_id, "quantity": 10, "qty_accepted": 8, "qty_rejected": 2}]},
            )
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        assert receipt["difference_type"] == "DANO"


def test_commercial_close_idempotent_stamps_user(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    fake = FakeStockConnector()
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-c5", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=fake):
            client.post(
                f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
                headers=headers,
                json={"warehouse_id": "wh", "items": [{"purchase_item_id": item_id, "quantity": 10, "qty_accepted": 10, "qty_rejected": 0}]},
            )
        receipt = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()["receipts"][0]
        first = client.post(
            f"/api/v1/plugins/compras/purchase/receipts/{receipt['id']}/commercial-close",
            headers=headers,
            json={"lines": [{"purchase_item_id": item_id, "qty_accepted": 10, "qty_rejected": 0}], "incidence_notes": "ok"},
        )
        assert first.status_code == 200, first.text
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        receipt_after = next(r for r in detail["receipts"] if r["id"] == receipt["id"])
        assert receipt_after["commercial_closed_at"] is not None
        assert receipt_after["incidence_notes"] == "ok"

        # Idempotente: mismo receipt, no duplica
        second = client.post(
            f"/api/v1/plugins/compras/purchase/receipts/{receipt['id']}/commercial-close",
            headers=headers,
            json={"lines": [{"purchase_item_id": item_id, "qty_accepted": 9, "qty_rejected": 1}]},
        )
        assert second.status_code == 200
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        assert len([r for r in detail["receipts"] if r["id"] == receipt["id"]]) == 1
        assert detail["receipts"][0]["qty_rejected"] == 1
