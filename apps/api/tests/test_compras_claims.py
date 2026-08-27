from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.auth.models import User
from systutor.kernel.auth.security import hash_password
from systutor.kernel.permissions.models import Permission, Role, RolePermission, UserRole
from systutor.kernel.plugins.persistent import sync_plugin_registry_state
from systutor.kernel.tenants.models import Tenant

from apps.api.app.commands.seed_demo import seed_demo_data

ORDERS = "/api/v1/plugins/compras/purchase/orders"


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!") -> dict[str, str]:
    token = login(client, email=email, password=password).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


def _setup(app) -> None:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)


def _make_order(client: TestClient, headers: dict[str, str], item: dict, name: str = "Supplier Claim") -> tuple[str, str]:
    supplier_id = client.post(
        "/api/v1/plugins/compras/purchase/suppliers",
        headers=headers,
        json={"name": name},
    ).json()["id"]
    order_id = client.post(
        ORDERS,
        headers=headers,
        json={"supplier_id": supplier_id, "items": [item]},
    ).json()["id"]
    confirm = client.post(f"{ORDERS}/{order_id}/confirm", headers=headers)
    assert confirm.status_code == 200, confirm.text
    return order_id, supplier_id


def _receive_full(client: TestClient, headers: dict[str, str], order_id: str, item_id: str, qty: float):
    with patch(
        "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
        return_value=FakeStockConnector(),
    ):
        resp = client.post(
            f"{ORDERS}/{order_id}/receive",
            headers=headers,
            json={"warehouse_id": "wh", "items": [
                {"purchase_item_id": item_id, "quantity": qty, "qty_accepted": qty, "qty_rejected": 0}
            ]},
        )
    assert resp.status_code == 200, resp.text


def _item_of(client: TestClient, headers: dict[str, str], order_id: str) -> str:
    detail = client.get(f"{ORDERS}/{order_id}", headers=headers).json()
    return detail["items"][0]["id"]


def _make_claim(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
    *,
    reason: str = "DEMORA",
    description: str = "Demora en la entrega pactada",
    **extra,
):
    return client.post(
        f"{ORDERS}/{order_id}/claims",
        headers=headers,
        json={"reason": reason, "description": description, **extra},
    )


def test_claim_created_with_closed_reason_defaults_open(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, supplier_id = _make_order(client, h, {"product_id": "prod-c1", "quantity": 5, "unit_cost": 10})
        resp = _make_claim(client, h, order_id, reason="CILINDRO_DANADO")
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["status"] == "ABIERTA"
        assert body["reason"] == "CILINDRO_DANADO"
        assert body["order_id"] == order_id
        assert body["supplier_id"] == supplier_id
        assert body["receipt_id"] is None and body["invoice_id"] is None
        assert body["opened_by"] and body["opened_at"]

        detail = client.get(f"{ORDERS}/{order_id}/claims/{body['id']}", headers=h).json()
        assert len(detail["events"]) == 1
        opening = detail["events"][0]
        assert opening["from_status"] is None
        assert opening["to_status"] == "ABIERTA"
        assert opening["user_id"]


def test_claim_rejects_reason_outside_list_422(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-c2", "quantity": 3, "unit_cost": 8})
        resp = _make_claim(client, h, order_id, reason="NO_EXISTE")
        assert resp.status_code == 422, resp.text


def test_claim_link_must_belong_to_same_order_400(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_a, _sup_a = _make_order(client, h, {"product_id": "prod-c3", "quantity": 4, "unit_cost": 10}, name="Supplier A")
        order_b, _sup_b = _make_order(client, h, {"product_id": "prod-c4", "quantity": 4, "unit_cost": 11}, name="Supplier B")
        item_b = _item_of(client, h, order_b)

        inv = client.post(
            f"{ORDERS}/{order_b}/invoices",
            headers=h,
            json={"invoice_number": "F-C4", "invoice_date": "2026-08-26", "tax": 0, "lines": [{"order_item_id": item_b, "qty": 4, "unit_price": 11}]},
        )
        assert inv.status_code == 201, inv.text
        invoice_b = inv.json()["id"]

        resp_invoice_link = _make_claim(client, h, order_a, invoice_id=invoice_b)
        assert resp_invoice_link.status_code == 400, resp_invoice_link.text
        assert "ajena a la orden" in resp_invoice_link.json()["detail"]

        _receive_full(client, h, order_b, item_b, 4)
        detail_b = client.get(f"{ORDERS}/{order_b}", headers=h).json()
        receipt_b = detail_b["receipts"][0]["id"]

        resp_receipt_link = _make_claim(client, h, order_a, receipt_id=receipt_b)
        assert resp_receipt_link.status_code == 400, resp_receipt_link.text
        assert "ajena a la orden" in resp_receipt_link.json()["detail"]


def test_claim_tenant_isolated_404(app) -> None:
    _setup(app)
    order_id = None
    claim_id = None
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-c5", "quantity": 2, "unit_cost": 9})
        claim_id = _make_claim(client, h, order_id).json()["id"]

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant B", slug="tenant-b")
        db.add(other)
        db.flush()
        role = Role(tenant_id=other.id, name="admin")
        db.add(role)
        db.flush()
        perm = db.scalar(select(Permission).where(Permission.name == "compras.order.read"))
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        perm_manage = db.scalar(select(Permission).where(Permission.name == "compras.order.manage"))
        db.add(RolePermission(role_id=role.id, permission_id=perm_manage.id))
        user = User(
            tenant_id=other.id,
            email="other-b@example.com",
            full_name="Other Admin",
            password_hash=hash_password("Other123!"),
            is_active=True,
            is_superadmin=False,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    with TestClient(app) as client:
        h_other = auth_headers(client, email="other-b@example.com", password="Other123!")
        list_resp = client.get(f"{ORDERS}/{order_id}/claims", headers=h_other)
        assert list_resp.status_code == 404, list_resp.text
        detail_resp = client.get(f"{ORDERS}/{order_id}/claims/{claim_id}", headers=h_other)
        assert detail_resp.status_code == 404, detail_resp.text
        start_resp = client.post(f"{ORDERS}/{order_id}/claims/{claim_id}/start", headers=h_other)
        assert start_resp.status_code == 404, start_resp.text


def test_claim_start_transitions_with_event(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-c6", "quantity": 1, "unit_cost": 10})
        claim_id = _make_claim(client, h, order_id).json()["id"]

        started = client.post(f"{ORDERS}/{order_id}/claims/{claim_id}/start", headers=h)
        assert started.status_code == 200, started.text
        body = started.json()
        assert body["status"] == "EN_GESTION"

        detail = client.get(f"{ORDERS}/{order_id}/claims/{claim_id}", headers=h).json()
        assert len(detail["events"]) == 2
        last = detail["events"][-1]
        assert last["from_status"] == "ABIERTA"
        assert last["to_status"] == "EN_GESTION"
        assert last["user_id"]


def test_claim_resolve_requires_resolution_notes_422(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-c7", "quantity": 1, "unit_cost": 10})
        claim_id = _make_claim(client, h, order_id).json()["id"]

        resp = client.post(f"{ORDERS}/{order_id}/claims/{claim_id}/resolve", headers=h, json={})
        assert resp.status_code == 422, resp.text

        empty_notes = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/resolve",
            headers=h,
            json={"resolution_notes": ""},
        )
        assert empty_notes.status_code == 422, empty_notes.text


def test_claim_resolved_is_terminal_409(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-c8", "quantity": 1, "unit_cost": 10})
        claim_id = _make_claim(client, h, order_id).json()["id"]

        resolved = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/resolve",
            headers=h,
            json={"resolution_notes": "Reposición acordada con el proveedor"},
        )
        assert resolved.status_code == 200, resolved.text
        body = resolved.json()
        assert body["status"] == "RESUELTA"
        assert body["resolved_at"] is not None
        assert body["resolved_by"]
        assert body["resolution_notes"] == "Reposición acordada con el proveedor"

        after_start = client.post(f"{ORDERS}/{order_id}/claims/{claim_id}/start", headers=h)
        assert after_start.status_code == 409, after_start.text
        after_annul = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/annul",
            headers=h,
            json={"reason": "intento post resolucion"},
        )
        assert after_annul.status_code == 409, after_annul.text


def test_repeat_transition_idempotent_no_duplicate_event(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-c9", "quantity": 1, "unit_cost": 10})
        claim_id = _make_claim(client, h, order_id).json()["id"]

        first_start = client.post(f"{ORDERS}/{order_id}/claims/{claim_id}/start", headers=h)
        assert first_start.status_code == 200, first_start.text
        repeat_start = client.post(f"{ORDERS}/{order_id}/claims/{claim_id}/start", headers=h)
        assert repeat_start.status_code == 200, repeat_start.text
        assert repeat_start.json()["status"] == "EN_GESTION"

        resolve = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/resolve",
            headers=h,
            json={"resolution_notes": "notas"},
        )
        assert resolve.status_code == 200, resolve.text
        repeat_resolve = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/resolve",
            headers=h,
            json={"resolution_notes": "otras notas"},
        )
        assert repeat_resolve.status_code == 200, repeat_resolve.text

        detail = client.get(f"{ORDERS}/{order_id}/claims/{claim_id}", headers=h).json()
        statuses = [e["to_status"] for e in detail["events"]]
        assert statuses == ["ABIERTA", "EN_GESTION", "RESUELTA"], statuses
        assert detail["resolution_notes"] == "notas"


def test_claim_annul_records_reason_event(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-ca", "quantity": 1, "unit_cost": 10})
        claim_id = _make_claim(client, h, order_id).json()["id"]

        annulled = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/annul",
            headers=h,
            json={"reason": "Pedido duplicado por error de carga"},
        )
        assert annulled.status_code == 200, annulled.text
        assert annulled.json()["status"] == "ANULADA"

        detail = client.get(f"{ORDERS}/{order_id}/claims/{claim_id}", headers=h).json()
        last = detail["events"][-1]
        assert last["to_status"] == "ANULADA"
        assert last["from_status"] == "ABIERTA"
        assert last["reason"] == "Pedido duplicado por error de carga"

        repeat_annul = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/annul",
            headers=h,
            json={"reason": "repetido"},
        )
        assert repeat_annul.status_code == 200, repeat_annul.text
        detail_after = client.get(f"{ORDERS}/{order_id}/claims/{claim_id}", headers=h).json()
        assert len(detail_after["events"]) == len(detail["events"])

        annul_then_resolve = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/resolve",
            headers=h,
            json={"resolution_notes": "invalido"},
        )
        assert annul_then_resolve.status_code == 409, annul_then_resolve.text


def test_order_close_unaffected_by_open_claims(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-cb", "quantity": 6, "unit_cost": 20})
        item_id = _item_of(client, h, order_id)
        _receive_full(client, h, order_id, item_id, 6)
        detail_received = client.get(f"{ORDERS}/{order_id}", headers=h).json()
        receipt_id = detail_received["receipts"][0]["id"]

        claim = _make_claim(client, h, order_id, reason="FALTANTE", description="Faltó un bulto", receipt_id=receipt_id)
        assert claim.status_code == 201, claim.text
        assert claim.json()["receipt_id"] == receipt_id
        claim_id = claim.json()["id"]

        closed = client.post(f"{ORDERS}/{order_id}/close", headers=h, json={"reason": "Cierre administrativo con reclamo abierto"})
        assert closed.status_code == 200, closed.text
        assert closed.json()["status"] == "CLOSED"

        detail_closed = client.get(f"{ORDERS}/{order_id}", headers=h).json()
        assert detail_closed["status"] == "CLOSED"

        still_open = client.get(f"{ORDERS}/{order_id}/claims/{claim_id}", headers=h).json()
        assert still_open["status"] == "ABIERTA"


def test_claim_e2e_on_receipt_with_difference_three_events(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id, _sup = _make_order(client, h, {"product_id": "prod-cc", "quantity": 10, "unit_cost": 10})
        item_id = _item_of(client, h, order_id)

        with patch(
            "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
            return_value=FakeStockConnector(),
        ):
            received = client.post(
                f"{ORDERS}/{order_id}/receive",
                headers=h,
                json={"warehouse_id": "wh", "items": [
                    {"purchase_item_id": item_id, "quantity": 8, "qty_accepted": 8, "qty_rejected": 0}
                ]},
            )
        assert received.status_code == 200, received.text
        receipt = client.get(f"{ORDERS}/{order_id}", headers=h).json()["receipts"][0]
        assert receipt["difference_type"] == "FALTANTE"

        claim = _make_claim(
            client,
            h,
            order_id,
            reason="FALTANTE",
            description="Se recibieron menos bultos que los ordenados",
            receipt_id=receipt["id"],
        )
        assert claim.status_code == 201, claim.text
        claim_body = claim.json()
        assert claim_body["status"] == "ABIERTA"
        assert claim_body["receipt_id"] == receipt["id"]

        started = client.post(f"{ORDERS}/{order_id}/claims/{claim_body['id']}/start", headers=h)
        assert started.status_code == 200, started.text
        assert started.json()["status"] == "EN_GESTION"

        resolved = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_body['id']}/resolve",
            headers=h,
            json={"resolution_notes": "El proveedor repuso la cantidad faltante"},
        )
        assert resolved.status_code == 200, resolved.text

        detail = client.get(f"{ORDERS}/{order_id}/claims/{claim_body['id']}", headers=h).json()
        assert detail["status"] == "RESUELTA"
        assert detail["resolution_notes"] == "El proveedor repuso la cantidad faltante"
        events = detail["events"]
        assert len(events) == 3
        assert [e["from_status"] for e in events] == [None, "ABIERTA", "EN_GESTION"]
        assert [e["to_status"] for e in events] == ["ABIERTA", "EN_GESTION", "RESUELTA"]
