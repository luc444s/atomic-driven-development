from __future__ import annotations

from importlib import import_module
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.auth.models import User
from systutor.kernel.auth.security import hash_password
from systutor.kernel.permissions.models import Permission, Role, RolePermission, UserRole
from systutor.kernel.plugins.persistent import sync_plugin_registry_state
from systutor.kernel.tenants.models import Tenant

from apps.api.app.commands.seed_demo import seed_demo_data

migration_013 = import_module("plugins.commerce.migrations.013_claim_derivation_source")

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


def _make_order(client: TestClient, headers: dict[str, str], item: dict, name: str = "Supplier Derive") -> str:
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
    return order_id


def _receive(client: TestClient, headers: dict[str, str], order_id: str, item_id: str, qty: float, *, qty_accepted: float | None = None) -> None:
    accepted = qty_accepted if qty_accepted is not None else qty
    with patch(
        "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
        return_value=FakeStockConnector(),
    ):
        resp = client.post(
            f"{ORDERS}/{order_id}/receive",
            headers=headers,
            json={"warehouse_id": "wh", "items": [
                {
                    "purchase_item_id": item_id,
                    "quantity": qty,
                    "qty_accepted": accepted,
                    "qty_rejected": qty - accepted,
                }
            ]},
        )
    assert resp.status_code == 200, resp.text


def _item_of(client: TestClient, headers: dict[str, str], order_id: str) -> str:
    detail = client.get(f"{ORDERS}/{order_id}", headers=headers).json()
    return detail["items"][0]["id"]


def _invoice(client: TestClient, headers: dict[str, str], order_id: str, item_id: str, qty: float, unit_price: float, number: str = "F-DER") -> str:
    resp = client.post(
        f"{ORDERS}/{order_id}/invoices",
        headers=headers,
        json={"invoice_number": number, "invoice_date": "2026-08-26", "tax": 0, "lines": [
            {"order_item_id": item_id, "qty": qty, "unit_price": unit_price}
        ]},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _derive(client: TestClient, headers: dict[str, str], order_id: str):
    return client.post(f"{ORDERS}/{order_id}/claims/derive", headers=headers)


def _list_claims(client: TestClient, headers: dict[str, str], order_id: str) -> list[dict]:
    return client.get(f"{ORDERS}/{order_id}/claims", headers=headers).json()


def test_derive_creates_faltante_claim_for_qty_mismatch(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d1", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        invoice_id = _invoice(client, h, order_id, item_id, 9, round(80 / 9, 6), "F-D1")

        resp = _derive(client, h, order_id)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["skipped"] == 0
        assert len(body["created"]) == 1
        claim = body["created"][0]
        assert claim["reason"] == "FALTANTE"
        assert claim["status"] == "ABIERTA"
        assert claim["invoice_id"] == invoice_id
        assert claim["receipt_id"] is None
        assert claim["source"] == "DERIVED"
        assert "aceptado" in claim["description"]
        assert len(_list_claims(client, h, order_id)) == 1


def test_derive_creates_precio_incorrecto_claim_for_cost_mismatch(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d2", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        _invoice(client, h, order_id, item_id, 8, 15.0, "F-D2")

        resp = _derive(client, h, order_id)
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert len(body["created"]) == 1
        claim = body["created"][0]
        assert claim["reason"] == "PRECIO_INCORRECTO"
        assert "costo facturado" in claim["description"]


def test_derive_skips_sin_factura_mismatch(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d3", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)

        rec = client.get(f"{ORDERS}/{order_id}/reconciliation", headers=h).json()
        assert rec["by_item"][0]["reason"] == "sin factura"

        resp = _derive(client, h, order_id)
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["created"] == []
        assert body["skipped"] == 1
        assert _list_claims(client, h, order_id) == []


def test_derive_is_idempotent_no_duplicates_on_rerun(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d4", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        _invoice(client, h, order_id, item_id, 9, 12.5, "F-D4")

        first = _derive(client, h, order_id)
        assert first.status_code == 201, first.text
        assert len(first.json()["created"]) == 2

        second = _derive(client, h, order_id)
        assert second.status_code == 200, second.text
        assert second.json()["created"] == []
        assert second.json()["skipped"] == 2

        claims = _list_claims(client, h, order_id)
        assert len(claims) == 2
        assert {c["reason"] for c in claims} == {"FALTANTE", "PRECIO_INCORRECTO"}


def test_derive_no_duplicates_even_after_annul(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d5", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        _invoice(client, h, order_id, item_id, 9, round(80 / 9, 6), "F-D5")

        first = _derive(client, h, order_id)
        assert first.status_code == 201, first.text
        claim_id = first.json()["created"][0]["id"]

        annulled = client.post(
            f"{ORDERS}/{order_id}/claims/{claim_id}/annul",
            headers=h,
            json={"reason": "Reclamación anulada a mano"},
        )
        assert annulled.status_code == 200, annulled.text

        rerun = _derive(client, h, order_id)
        assert rerun.status_code == 200, rerun.text
        assert rerun.json()["created"] == []
        assert rerun.json()["skipped"] == 1

        claims = _list_claims(client, h, order_id)
        assert len(claims) == 1
        assert claims[0]["status"] == "ANULADA"


def test_manual_claim_does_not_block_derivation(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d6", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        _invoice(client, h, order_id, item_id, 9, round(80 / 9, 6), "F-D6")

        manual = client.post(
            f"{ORDERS}/{order_id}/claims",
            headers=h,
            json={"reason": "DEMORA", "description": "Reclamación manual previa"},
        )
        assert manual.status_code == 201, manual.text

        resp = _derive(client, h, order_id)
        assert resp.status_code == 201, resp.text
        assert len(resp.json()["created"]) == 1

        claims = _list_claims(client, h, order_id)
        assert len(claims) == 2
        by_reason = {c["reason"]: c for c in claims}
        assert by_reason["DEMORA"]["source"] == "MANUAL"
        assert by_reason["FALTANTE"]["source"] == "DERIVED"


def test_derived_claim_has_source_derived(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d7", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        invoice_id = _invoice(client, h, order_id, item_id, 9, round(80 / 9, 6), "F-D7")

        resp = _derive(client, h, order_id)
        assert resp.status_code == 201, resp.text
        claim = resp.json()["created"][0]
        assert claim["source"] == "DERIVED"
        assert claim["invoice_id"] == invoice_id
        assert claim["receipt_id"] is None
        assert claim["description"].startswith(f"Derivada de conciliación (ítem {item_id}): ")

        detail = client.get(f"{ORDERS}/{order_id}/claims/{claim['id']}", headers=h).json()
        assert detail["source"] == "DERIVED"
        assert [e["to_status"] for e in detail["events"]] == ["ABIERTA"]


def test_derive_no_mismatch_creates_nothing(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d8", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        _invoice(client, h, order_id, item_id, 8, 10.0, "F-D8")

        rec = client.get(f"{ORDERS}/{order_id}/reconciliation", headers=h).json()
        assert rec["by_item"][0]["status"] == "MATCH"

        resp = _derive(client, h, order_id)
        assert resp.status_code == 200, resp.text
        assert resp.json() == {"created": [], "skipped": 0}
        assert _list_claims(client, h, order_id) == []


def test_derive_tenant_isolated_404(app) -> None:
    _setup(app)
    order_id = None
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-d9", "quantity": 10, "unit_cost": 10.0})

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant B", slug="tenant-b-derive")
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
            email="other-derive@example.com",
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
        h_other = auth_headers(client, email="other-derive@example.com", password="Other123!")
        resp = _derive(client, h_other, order_id)
        assert resp.status_code == 404, resp.text


def test_reconciliation_output_unchanged_after_derive(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        h = auth_headers(client)
        order_id = _make_order(client, h, {"product_id": "prod-da", "quantity": 10, "unit_cost": 10.0})
        item_id = _item_of(client, h, order_id)
        _receive(client, h, order_id, item_id, 10, qty_accepted=8)
        _invoice(client, h, order_id, item_id, 9, 12.5, "F-DA")

        before = client.get(f"{ORDERS}/{order_id}/reconciliation", headers=h).json()

        resp = _derive(client, h, order_id)
        assert resp.status_code == 201, resp.text

        after = client.get(f"{ORDERS}/{order_id}/reconciliation", headers=h).json()
        assert after == before


def test_migration_013_downgrade_drops_source_preserving_rows(db_session) -> None:
    from plugins.commerce.purchase.backend.models import ComSupplierClaim, ComSupplierClaimEvent

    columns_before = {
        c["name"]
        for c in inspect(db_session.connection()).get_columns("com_supplier_claims")
    }
    assert "source" in columns_before

    claim = ComSupplierClaim(
        tenant_id="t-1", order_id="o-1", supplier_id="s-1",
        reason="FALTANTE", description="mismatch", status="ABIERTA",
        source="DERIVED", opened_by="u-1",
    )
    db_session.add(claim)
    db_session.flush()
    db_session.add(ComSupplierClaimEvent(
        tenant_id="t-1", claim_id=claim.id, from_status=None,
        to_status="ABIERTA", reason=None, user_id="u-1",
    ))
    db_session.commit()

    migration_013.downgrade(db_session)
    db_session.commit()

    columns_after = {
        c["name"]
        for c in inspect(db_session.connection()).get_columns("com_supplier_claims")
    }
    assert "source" not in columns_after
    claims_count = db_session.execute(text("SELECT COUNT(*) FROM com_supplier_claims")).scalar_one()
    assert claims_count == 1
    kept_reason = db_session.execute(text("SELECT reason FROM com_supplier_claims")).scalar_one()
    assert kept_reason == "FALTANTE"
    events_count = db_session.execute(text("SELECT COUNT(*) FROM com_supplier_claim_events")).scalar_one()
    assert events_count == 1


def test_migration_013_upgrade_backfills_manual_and_is_idempotent(db_session) -> None:
    from plugins.commerce.purchase.backend.models import ComSupplierClaim

    claim = ComSupplierClaim(
        tenant_id="t-1", order_id="o-1", supplier_id="s-1",
        reason="DEMORA", description="pre-migración", status="ABIERTA",
        opened_by="u-1",
    )
    db_session.add(claim)
    db_session.commit()

    migration_013.downgrade(db_session)
    db_session.commit()
    columns = {
        c["name"]
        for c in inspect(db_session.connection()).get_columns("com_supplier_claims")
    }
    assert "source" not in columns

    migration_013.upgrade(db_session)
    migration_013.upgrade(db_session)
    db_session.commit()

    columns = {
        c["name"]
        for c in inspect(db_session.connection()).get_columns("com_supplier_claims")
    }
    assert "source" in columns
    row = db_session.execute(
        select(ComSupplierClaim).where(ComSupplierClaim.id == claim.id)
    ).scalar_one()
    assert row.source == "MANUAL"
