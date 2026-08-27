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
        json={"name": "Supplier Invoice"},
    ).json()["id"]
    order_id = client.post(
        "/api/v1/plugins/compras/purchase/orders",
        headers=headers,
        json={"supplier_id": supplier_id, "items": [item]},
    ).json()["id"]
    client.post(f"/api/v1/plugins/compras/purchase/orders/{order_id}/confirm", headers=headers)
    return order_id


def _receive_full(client, headers, order_id, item_id, accepted):
    with patch("plugins.commerce.purchase.backend.routers.receipts._build_stock_connector", return_value=FakeStockConnector()):
        resp = client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/receive",
            headers=headers,
            json={"warehouse_id": "wh", "items": [{"purchase_item_id": item_id, "quantity": accepted, "qty_accepted": accepted, "qty_rejected": 0}]},
        )
    assert resp.status_code == 200, resp.text


def test_invoice_created_links_order(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-i1", "quantity": 10, "unit_cost": 12.5})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive_full(client, headers, order_id, item_id, 10)
        inv = client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/invoices",
            headers=headers,
            json={"invoice_number": "F001", "invoice_date": "2026-08-26", "tax": 0, "lines": [{"order_item_id": item_id, "qty": 10, "unit_price": 12.5}]},
        )
        assert inv.status_code == 201, inv.text
        body = inv.json()
        assert body["order_id"] == order_id
        assert body["status"] == "REGISTRADA"
        assert body["total"] == 125.0

        listed = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}/invoices", headers=headers).json()
        assert len(listed) == 1


def test_reconciliation_match_when_invoiced_equals_accepted_real(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-i2", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive_full(client, headers, order_id, item_id, 8)
        client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/invoices",
            headers=headers,
            json={"invoice_number": "F002", "invoice_date": "2026-08-26", "tax": 0, "lines": [{"order_item_id": item_id, "qty": 8, "unit_price": 12.5}]},
        )
        rec = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}/reconciliation", headers=headers).json()
        assert rec["by_item"][0]["status"] == "MATCH", rec
        assert rec["invoice_status"] == "CONCILIADA", rec


def test_reconciliation_mismatch_when_invoiced_exceeds_accepted(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-i3", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive_full(client, headers, order_id, item_id, 8)
        client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/invoices",
            headers=headers,
            json={"invoice_number": "F003", "invoice_date": "2026-08-26", "tax": 0, "lines": [{"order_item_id": item_id, "qty": 9, "unit_price": 12.5}]},
        )
        rec = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}/reconciliation", headers=headers).json()
        assert rec["by_item"][0]["status"] == "MISMATCH", rec


def test_reconciliation_no_invoice_is_mismatch_not_error(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-i4", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive_full(client, headers, order_id, item_id, 8)
        rec = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}/reconciliation", headers=headers)
        assert rec.status_code == 200, rec.text
        body = rec.json()
        assert body["totals"]["status"] == "MISMATCH"
        assert "sin factura" in body["totals"]["reasons"]


def test_invoice_cancel_excluded_from_reconciliation(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id = _make_order(client, headers, {"product_id": "prod-i5", "quantity": 10, "unit_cost": 10.0})
        detail = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}", headers=headers).json()
        item_id = detail["items"][0]["id"]
        _receive_full(client, headers, order_id, item_id, 8)
        inv = client.post(
            f"/api/v1/plugins/compras/purchase/orders/{order_id}/invoices",
            headers=headers,
            json={"invoice_number": "F005", "invoice_date": "2026-08-26", "tax": 0, "lines": [{"order_item_id": item_id, "qty": 8, "unit_price": 12.5}]},
        ).json()
        cancel = client.post(f"/api/v1/plugins/compras/purchase/invoices/{inv['id']}/cancel", headers=headers)
        assert cancel.status_code == 200
        rec = client.get(f"/api/v1/plugins/compras/purchase/orders/{order_id}/reconciliation", headers=headers).json()
        assert rec["totals"]["status"] == "MISMATCH"
        assert rec["invoice_status"] is None
