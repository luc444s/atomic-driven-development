from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, inspect, select
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.auth.models import User
from systutor.kernel.auth.security import hash_password
from systutor.kernel.permissions.models import Permission, Role, RolePermission, UserRole
from systutor.kernel.plugins.persistent import sync_plugin_registry_state
from systutor.kernel.tenants.models import Tenant

from apps.api.app.commands.seed_demo import seed_demo_data

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ORDERS = "/api/v1/plugins/compras/purchase/orders"


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(
    client: TestClient,
    email: str = "admin@example.com",
    password: str = "ChangeMe123!",
) -> dict[str, str]:
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


def _setup(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    return seeded


def _make_order(
    client: TestClient,
    headers: dict[str, str],
    item: dict,
    name: str = "Proveedor Devoluciones",
) -> tuple[str, str]:
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


def _detail_of(client: TestClient, headers: dict[str, str], order_id: str) -> dict:
    detail = client.get(f"{ORDERS}/{order_id}", headers=headers)
    assert detail.status_code == 200, detail.text
    return detail.json()


def _item_of(client: TestClient, headers: dict[str, str], order_id: str) -> str:
    return _detail_of(client, headers, order_id)["items"][0]["id"]


def _seed_cylinder(app, tenant_id: str, serial: str) -> str:
    with app.state.session_factory() as db:
        from plugins.logistics.backend.models.cylinder import LogisticsCylinder

        cylinder = LogisticsCylinder(
            tenant_id=tenant_id,
            serial=serial,
            container_type="CYLINDER",
            current_state="EN_ALMACEN_VACIO",
        )
        db.add(cylinder)
        db.flush()
        cylinder_id = cylinder.id
        db.commit()
    return cylinder_id


def _create_dispatch(
    client: TestClient,
    headers: dict[str, str],
    *,
    supplier_id: str,
    order_id: str,
    cylinder_id: str,
) -> dict:
    created = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "order_id": order_id,
            "cylinders": [{"cylinder_id": cylinder_id}],
        },
    )
    assert created.status_code == 201, created.text
    dispatch = created.json()
    confirmed = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{dispatch['id']}/confirm",
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()


def _receive_order(
    client: TestClient,
    headers: dict[str, str],
    *,
    order_id: str,
    item_id: str,
    qty: float,
    dispatch_id: str | None = None,
    qty_accepted: int | None = None,
    qty_rejected: int | None = None,
) -> dict:
    with patch(
        "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
        return_value=FakeStockConnector(),
    ):
        response = client.post(
            f"{ORDERS}/{order_id}/receive",
            headers=headers,
            json={
                "warehouse_id": "wh-returns",
                "dispatch_id": dispatch_id,
                "items": [
                    {
                        "purchase_item_id": item_id,
                        "quantity": qty,
                        "qty_accepted": qty if qty_accepted is None else qty_accepted,
                        "qty_rejected": 0 if qty_rejected is None else qty_rejected,
                    }
                ],
            },
        )
    assert response.status_code == 200, response.text
    return response.json()


def _make_claim(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
    *,
    reason: str = "DEMORA",
    description: str = "Incidencia en proveedor",
    **extra,
):
    return client.post(
        f"{ORDERS}/{order_id}/claims",
        headers=headers,
        json={"reason": reason, "description": description, **extra},
    )


def _create_return(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
    *,
    receipt_id: str,
    order_item_id: str,
    claim_id: str | None = None,
    cylinder_id: str | None = None,
    qty: float = 1,
    return_date: str = "2026-08-27",
):
    line = {
        "order_item_id": order_item_id,
        "qty": qty,
        "notes": "bulto devuelto al proveedor",
    }
    if cylinder_id is not None:
        line["cylinder_id"] = cylinder_id
    payload = {
        "receipt_id": receipt_id,
        "claim_id": claim_id,
        "return_date": return_date,
        "notes": "devolución por observación",
        "lines": [line],
    }
    return client.post(f"{ORDERS}/{order_id}/returns", headers=headers, json=payload)


def test_return_created_linked_to_receipt(app) -> None:
    seeded = _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c1", "quantity": 5, "unit_cost": 10},
        )
        item_id = _item_of(client, headers, order_id)
        cylinder_id = _seed_cylinder(app, seeded["tenant_id"], "DEV-0001")
        dispatch = _create_dispatch(
            client,
            headers,
            supplier_id=supplier_id,
            order_id=order_id,
            cylinder_id=cylinder_id,
        )
        _receive_order(
            client,
            headers,
            order_id=order_id,
            item_id=item_id,
            qty=5,
            dispatch_id=dispatch["id"],
            qty_accepted=3,
            qty_rejected=2,
        )
        receipt = _detail_of(client, headers, order_id)["receipts"][0]

        claim = _make_claim(
            client,
            headers,
            order_id,
            reason="CILINDRO_DANADO",
            description="Envase golpeado durante revisión",
            receipt_id=receipt["id"],
        )
        assert claim.status_code == 201, claim.text

        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt["id"],
            claim_id=claim.json()["id"],
            order_item_id=item_id,
            cylinder_id=cylinder_id,
            qty=2,
        )
        assert created.status_code == 201, created.text
        body = created.json()
        assert body["status"] == "REGISTRADA"
        assert body["order_id"] == order_id
        assert body["supplier_id"] == supplier_id
        assert body["receipt_id"] == receipt["id"]
        assert body["claim_id"] == claim.json()["id"]

        listed = client.get(f"{ORDERS}/{order_id}/returns", headers=headers)
        assert listed.status_code == 200, listed.text
        assert len(listed.json()) == 1

        detail = client.get(f"{ORDERS}/{order_id}/returns/{body['id']}", headers=headers)
        assert detail.status_code == 200, detail.text
        detail_body = detail.json()
        assert len(detail_body["lines"]) == 1
        assert detail_body["lines"][0]["serial"] == "DEV-0001"
        assert detail_body["lines"][0]["unit_cost"] == 10.0
        assert [event["to_status"] for event in detail_body["events"]] == ["REGISTRADA"]


def test_return_receipt_must_belong_to_order_400(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_a, _supplier_a = _make_order(
            client,
            headers,
            {"product_id": "prod-c2", "quantity": 4, "unit_cost": 9},
            name="Proveedor A",
        )
        order_b, _supplier_b = _make_order(
            client,
            headers,
            {"product_id": "prod-c3", "quantity": 4, "unit_cost": 11},
            name="Proveedor B",
        )
        item_a = _item_of(client, headers, order_a)
        item_b = _item_of(client, headers, order_b)
        _receive_order(client, headers, order_id=order_b, item_id=item_b, qty=4)
        receipt_b = _detail_of(client, headers, order_b)["receipts"][0]["id"]

        response = _create_return(
            client,
            headers,
            order_a,
            receipt_id=receipt_b,
            order_item_id=item_a,
        )
        assert response.status_code == 400, response.text
        assert "recepción no pertenece" in response.json()["detail"].lower()


def test_return_claim_must_belong_to_same_order_400(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_a, _supplier_a = _make_order(
            client,
            headers,
            {"product_id": "prod-c4", "quantity": 5, "unit_cost": 7},
            name="Proveedor A",
        )
        order_b, _supplier_b = _make_order(
            client,
            headers,
            {"product_id": "prod-c5", "quantity": 5, "unit_cost": 8},
            name="Proveedor B",
        )
        item_a = _item_of(client, headers, order_a)
        item_b = _item_of(client, headers, order_b)
        _receive_order(client, headers, order_id=order_a, item_id=item_a, qty=5)
        receipt_a = _detail_of(client, headers, order_a)["receipts"][0]["id"]

        claim_b = _make_claim(client, headers, order_b, reason="DEMORA")
        assert claim_b.status_code == 201, claim_b.text

        response = _create_return(
            client,
            headers,
            order_a,
            receipt_id=receipt_a,
            claim_id=claim_b.json()["id"],
            order_item_id=item_a,
        )
        assert response.status_code == 400, response.text
        assert "reclamación no pertenece" in response.json()["detail"].lower()


def test_return_serial_must_belong_to_order_400(app) -> None:
    seeded = _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_a, supplier_a = _make_order(
            client,
            headers,
            {"product_id": "prod-c6", "quantity": 3, "unit_cost": 9},
            name="Proveedor A",
        )
        order_b, supplier_b = _make_order(
            client,
            headers,
            {"product_id": "prod-c7", "quantity": 3, "unit_cost": 9},
            name="Proveedor B",
        )
        item_a = _item_of(client, headers, order_a)
        item_b = _item_of(client, headers, order_b)
        _receive_order(client, headers, order_id=order_a, item_id=item_a, qty=3)
        receipt_a = _detail_of(client, headers, order_a)["receipts"][0]["id"]

        cylinder_a = _seed_cylinder(app, seeded["tenant_id"], "DEV-0002")
        cylinder_b = _seed_cylinder(app, seeded["tenant_id"], "DEV-0003")
        _create_dispatch(
            client,
            headers,
            supplier_id=supplier_a,
            order_id=order_a,
            cylinder_id=cylinder_a,
        )
        _create_dispatch(
            client,
            headers,
            supplier_id=supplier_b,
            order_id=order_b,
            cylinder_id=cylinder_b,
        )
        _receive_order(client, headers, order_id=order_b, item_id=item_b, qty=3)

        response = _create_return(
            client,
            headers,
            order_a,
            receipt_id=receipt_a,
            order_item_id=item_a,
            cylinder_id=cylinder_b,
        )
        assert response.status_code == 400, response.text
        assert "serial no pertenece" in response.json()["detail"].lower()


def test_return_qty_must_be_positive_422(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, _supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c8", "quantity": 2, "unit_cost": 12},
        )
        item_id = _item_of(client, headers, order_id)
        _receive_order(client, headers, order_id=order_id, item_id=item_id, qty=2)
        receipt_id = _detail_of(client, headers, order_id)["receipts"][0]["id"]

        response = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_id,
            order_item_id=item_id,
            qty=0,
        )
        assert response.status_code == 422, response.text


def test_return_tenant_isolated_404(app) -> None:
    _setup(app)
    return_id = None
    order_id = None
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, _supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c9", "quantity": 2, "unit_cost": 10},
        )
        item_id = _item_of(client, headers, order_id)
        _receive_order(client, headers, order_id=order_id, item_id=item_id, qty=2)
        receipt_id = _detail_of(client, headers, order_id)["receipts"][0]["id"]
        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_id,
            order_item_id=item_id,
        )
        assert created.status_code == 201, created.text
        return_id = created.json()["id"]

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant B", slug="tenant-b")
        db.add(other)
        db.flush()
        role = Role(tenant_id=other.id, name="admin")
        db.add(role)
        db.flush()
        perm_read = db.scalar(select(Permission).where(Permission.name == "compras.order.read"))
        perm_manage = db.scalar(select(Permission).where(Permission.name == "compras.order.manage"))
        db.add(RolePermission(role_id=role.id, permission_id=perm_read.id))
        db.add(RolePermission(role_id=role.id, permission_id=perm_manage.id))
        user = User(
            tenant_id=other.id,
            email="other-returns@example.com",
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
        other_headers = auth_headers(
            client,
            email="other-returns@example.com",
            password="Other123!",
        )
        list_response = client.get(f"{ORDERS}/{order_id}/returns", headers=other_headers)
        assert list_response.status_code == 404, list_response.text
        detail_response = client.get(
            f"{ORDERS}/{order_id}/returns/{return_id}",
            headers=other_headers,
        )
        assert detail_response.status_code == 404, detail_response.text
        complete_response = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=other_headers,
            json={"resolution_notes": "no debería pasar"},
        )
        assert complete_response.status_code == 404, complete_response.text


def test_return_complete_requires_resolution_notes_422(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, _supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c10", "quantity": 2, "unit_cost": 14},
        )
        item_id = _item_of(client, headers, order_id)
        _receive_order(client, headers, order_id=order_id, item_id=item_id, qty=2)
        receipt_id = _detail_of(client, headers, order_id)["receipts"][0]["id"]
        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_id,
            order_item_id=item_id,
        )
        return_id = created.json()["id"]

        missing = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=headers,
            json={},
        )
        assert missing.status_code == 422, missing.text

        empty = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=headers,
            json={"resolution_notes": ""},
        )
        assert empty.status_code == 422, empty.text


def test_return_terminal_409(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, _supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c11", "quantity": 2, "unit_cost": 15},
        )
        item_id = _item_of(client, headers, order_id)
        _receive_order(client, headers, order_id=order_id, item_id=item_id, qty=2)
        receipt_id = _detail_of(client, headers, order_id)["receipts"][0]["id"]
        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_id,
            order_item_id=item_id,
        )
        return_id = created.json()["id"]

        completed = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=headers,
            json={"resolution_notes": "acreditación NC-123"},
        )
        assert completed.status_code == 200, completed.text
        assert completed.json()["status"] == "CONCRETADA"

        annul = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/annul",
            headers=headers,
            json={"reason": "intento posterior"},
        )
        assert annul.status_code == 409, annul.text


def test_repeat_transition_idempotent_no_duplicate_event(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, _supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c12", "quantity": 2, "unit_cost": 16},
        )
        item_id = _item_of(client, headers, order_id)
        _receive_order(client, headers, order_id=order_id, item_id=item_id, qty=2)
        receipt_id = _detail_of(client, headers, order_id)["receipts"][0]["id"]
        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_id,
            order_item_id=item_id,
        )
        return_id = created.json()["id"]

        first = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=headers,
            json={"resolution_notes": "acreditación inicial"},
        )
        assert first.status_code == 200, first.text

        repeated = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=headers,
            json={"resolution_notes": "otra nota"},
        )
        assert repeated.status_code == 200, repeated.text
        assert repeated.json()["status"] == "CONCRETADA"

        detail = client.get(f"{ORDERS}/{order_id}/returns/{return_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        detail_body = detail.json()
        assert [event["to_status"] for event in detail_body["events"]] == [
            "REGISTRADA",
            "CONCRETADA",
        ]
        assert detail_body["resolution_notes"] == "acreditación inicial"


def test_return_does_not_mutate_receipt(app) -> None:
    seeded = _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c13", "quantity": 5, "unit_cost": 10},
        )
        item_id = _item_of(client, headers, order_id)
        cylinder_id = _seed_cylinder(app, seeded["tenant_id"], "DEV-0004")
        dispatch = _create_dispatch(
            client,
            headers,
            supplier_id=supplier_id,
            order_id=order_id,
            cylinder_id=cylinder_id,
        )
        _receive_order(
            client,
            headers,
            order_id=order_id,
            item_id=item_id,
            qty=5,
            dispatch_id=dispatch["id"],
            qty_accepted=4,
            qty_rejected=1,
        )
        before = _detail_of(client, headers, order_id)
        receipt_before = before["receipts"][0]
        order_status_before = before["status"]
        events_before = list(before["events"])

        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_before["id"],
            order_item_id=item_id,
            cylinder_id=cylinder_id,
        )
        assert created.status_code == 201, created.text
        return_id = created.json()["id"]
        completed = client.post(
            f"{ORDERS}/{order_id}/returns/{return_id}/complete",
            headers=headers,
            json={"resolution_notes": "acuerdo documentado"},
        )
        assert completed.status_code == 200, completed.text

        after = _detail_of(client, headers, order_id)
        assert after["receipts"][0] == receipt_before
        assert after["status"] == order_status_before
        assert after["events"] == events_before


def test_return_migration_downgrade_removes_tables_only(app) -> None:
    _setup(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, _supplier_id = _make_order(
            client,
            headers,
            {"product_id": "prod-c14", "quantity": 2, "unit_cost": 19},
        )
        item_id = _item_of(client, headers, order_id)
        _receive_order(client, headers, order_id=order_id, item_id=item_id, qty=2)
        receipt_id = _detail_of(client, headers, order_id)["receipts"][0]["id"]
        claim = _make_claim(client, headers, order_id, reason="DEMORA")
        assert claim.status_code == 201, claim.text
        created = _create_return(
            client,
            headers,
            order_id,
            receipt_id=receipt_id,
            claim_id=claim.json()["id"],
            order_item_id=item_id,
        )
        assert created.status_code == 201, created.text

    module_path = (
        PROJECT_ROOT / "plugins" / "commerce" / "migrations" / "018_merchandise_returns.py"
    )
    spec = importlib.util.spec_from_file_location("compras_migration_0018", module_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0018"

    with app.state.session_factory() as db:
        from plugins.commerce.purchase.backend.models import (
            ComMerchandiseReturn,
            ComPurchaseReceipt,
            ComSupplierClaim,
        )

        assert db.scalar(select(func.count()).select_from(ComMerchandiseReturn)) == 1
        assert db.scalar(select(func.count()).select_from(ComPurchaseReceipt)) == 1
        assert db.scalar(select(func.count()).select_from(ComSupplierClaim)) == 1

        migration.downgrade(db)
        db.commit()

        inspector = inspect(db.connection())
        assert not inspector.has_table("com_merchandise_returns")
        assert not inspector.has_table("com_merchandise_return_lines")
        assert not inspector.has_table("com_merchandise_return_events")
        assert inspector.has_table("com_purchase_receipts")
        assert inspector.has_table("com_supplier_claims")
        assert inspector.has_table("com_purchase_orders")
        assert db.scalar(select(func.count()).select_from(ComPurchaseReceipt)) == 1
        assert db.scalar(select(func.count()).select_from(ComSupplierClaim)) == 1

        migration.upgrade(db)
        db.commit()

        inspector = inspect(db.connection())
        assert inspector.has_table("com_merchandise_returns")
        assert inspector.has_table("com_merchandise_return_lines")
        assert inspector.has_table("com_merchandise_return_events")
