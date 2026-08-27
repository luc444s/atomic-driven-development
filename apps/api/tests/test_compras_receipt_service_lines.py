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
BASE = "/api/v1/plugins/compras/purchase"
SERVICE_LINES = f"{BASE}/receipts"


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(
    client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"
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


def _seed_and_enable(app) -> dict[str, str]:
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)
    return seeded


def _create_cylinders(app, tenant_id: str, serials: list[str]) -> dict[str, str]:
    with app.state.session_factory() as db:
        from plugins.logistics.backend.models.cylinder import LogisticsCylinder

        ids: dict[str, str] = {}
        for serial in serials:
            cyl = LogisticsCylinder(
                tenant_id=tenant_id,
                serial=serial,
                container_type="CYLINDER",
                current_state="EN_ALMACEN_VACIO",
            )
            db.add(cyl)
            db.flush()
            ids[serial] = cyl.id
        db.commit()
        return ids


def _make_receipt(
    client: TestClient, headers: dict[str, str], product_id: str, quantity: int = 10
) -> tuple[str, str]:
    supplier_id = client.post(
        f"{BASE}/suppliers",
        headers=headers,
        json={"name": "Proveedor Servicios"},
    ).json()["id"]
    order_id = client.post(
        f"{BASE}/orders",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "items": [{"product_id": product_id, "quantity": quantity, "unit_cost": 10.0}],
        },
    ).json()["id"]
    client.post(f"{BASE}/orders/{order_id}/confirm", headers=headers)
    detail = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()
    item_id = detail["items"][0]["id"]
    with patch(
        "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
        return_value=FakeStockConnector(),
    ):
        client.post(
            f"{BASE}/orders/{order_id}/receive",
            headers=headers,
            json={
                "warehouse_id": "wh",
                "items": [{"purchase_item_id": item_id, "quantity": quantity}],
            },
        )
    detail = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()
    return order_id, detail["receipts"][-1]["id"]


def test_service_line_created_linked_to_receipt(app) -> None:
    seeded = _seed_and_enable(app)
    cylinders = _create_cylinders(app, seeded["tenant_id"], ["SERV-0001"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c1")[1]

        resp = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={
                "serial": "SERV-0001",
                "service_type": "RETIMBRADO",
                "cost": 25.5,
                "notes": "retimbrado de origen",
                "test_date": "2026-08-27",
                "result": "APROBADO",
                "next_test_date": "2031-08-27",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["receipt_id"] == receipt_id
        assert body["cylinder_id"] == cylinders["SERV-0001"]
        assert body["serial"] == "SERV-0001"
        assert body["service_type"] == "RETIMBRADO"
        assert body["cost"] == 25.5
        assert body["notes"] == "retimbrado de origen"
        assert body["created_by"]

        listed = client.get(f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=headers)
        assert listed.status_code == 200, listed.text
        assert [ln["id"] for ln in listed.json()] == [body["id"]]


def test_service_line_types_closed_list_422(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0002"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c2")[1]

        resp = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "SERV-0002", "service_type": "PULIDO"},
        )
        assert resp.status_code == 422, resp.text


def test_service_line_rejects_unknown_serial_422(app) -> None:
    _seed_and_enable(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c3")[1]

        resp = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "NO-EXISTE", "service_type": "LLENADO"},
        )
        assert resp.status_code == 422, resp.text
        assert "NO-EXISTE" in resp.json()["detail"]


def test_service_line_tenant_isolated_404(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0003"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c4")[1]
        line_id = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "SERV-0003", "service_type": "LLENADO"},
        ).json()["id"]

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant B", slug="tenant-b")
        db.add(other)
        db.flush()
        role = Role(tenant_id=other.id, name="admin")
        db.add(role)
        db.flush()
        for perm_name in ("compras.order.read", "compras.order.receive"):
            perm = db.scalar(select(Permission).where(Permission.name == perm_name))
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        user = User(
            tenant_id=other.id,
            email="other-serv@example.com",
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
        h_other = auth_headers(client, email="other-serv@example.com", password="Other123!")
        get_resp = client.get(f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=h_other)
        assert get_resp.status_code == 404, get_resp.text
        post_resp = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=h_other,
            json={"serial": "SERV-0003", "service_type": "LLENADO"},
        )
        assert post_resp.status_code == 404, post_resp.text
        del_resp = client.delete(
            f"{SERVICE_LINES}/{receipt_id}/service-lines/{line_id}", headers=h_other
        )
        assert del_resp.status_code == 404, del_resp.text


def test_service_line_rejected_after_commercial_close_409(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0004"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        order_id, receipt_id = _make_receipt(client, headers, "prod-c5")
        item_id = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()["items"][0]["id"]

        line = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "SERV-0004", "service_type": "CAMBIO_VALVULA", "cost": 12},
        )
        assert line.status_code == 201, line.text

        close = client.post(
            f"{BASE}/receipts/{receipt_id}/commercial-close",
            headers=headers,
            json={"lines": [{"purchase_item_id": item_id, "qty_accepted": 10, "qty_rejected": 0}]},
        )
        assert close.status_code == 200, close.text

        post_resp = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "SERV-0004", "service_type": "PINTURA"},
        )
        assert post_resp.status_code == 409, post_resp.text
        del_resp = client.delete(
            f"{SERVICE_LINES}/{receipt_id}/service-lines/{line.json()['id']}", headers=headers
        )
        assert del_resp.status_code == 409, del_resp.text

        listed = client.get(f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=headers)
        assert [ln["id"] for ln in listed.json()] == [line.json()["id"]]


def test_service_line_delete_before_close_ok(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0005"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c6")[1]

        line_id = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "SERV-0005", "service_type": "INSPECCION"},
        ).json()["id"]

        resp = client.delete(
            f"{SERVICE_LINES}/{receipt_id}/service-lines/{line_id}", headers=headers
        )
        assert resp.status_code == 204, resp.text

        listed = client.get(f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=headers)
        assert listed.status_code == 200, listed.text
        assert listed.json() == []

        missing = client.delete(
            f"{SERVICE_LINES}/{receipt_id}/service-lines/{line_id}", headers=headers
        )
        assert missing.status_code == 404, missing.text


def test_service_lines_do_not_mutate_receipt(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0006", "SERV-0007"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        supplier_id = client.post(
            f"{BASE}/suppliers", headers=headers, json={"name": "Proveedor Snapshot"}
        ).json()["id"]
        order_id = client.post(
            f"{BASE}/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [{"product_id": "prod-c1", "quantity": 10, "unit_cost": 10.0}],
            },
        ).json()["id"]
        client.post(f"{BASE}/orders/{order_id}/confirm", headers=headers)
        item_id = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()["items"][0]["id"]
        with patch(
            "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
            return_value=FakeStockConnector(),
        ):
            client.post(
                f"{BASE}/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh",
                    "items": [
                        {
                            "purchase_item_id": item_id,
                            "quantity": 10,
                            "qty_accepted": 8,
                            "qty_rejected": 2,
                        }
                    ],
                    "cost_lines": [{"cost_type": "FLETE", "amount": 50}],
                },
            )
        detail = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()
        receipt_id = detail["receipts"][-1]["id"]
        before = detail["receipts"][-1]

        for serial, service_type, cost in (
            ("SERV-0006", "REPARACION", 40),
            ("SERV-0007", "MANTENIMIENTO", None),
        ):
            resp = client.post(
                f"{SERVICE_LINES}/{receipt_id}/service-lines",
                headers=headers,
                json={"serial": serial, "service_type": service_type, "cost": cost},
            )
            assert resp.status_code == 201, resp.text

        after = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()["receipts"][-1]
        for field in (
            "id",
            "qty_accepted",
            "qty_rejected",
            "difference_type",
            "incidence_notes",
            "commercial_closed_at",
            "commercial_closed_by",
            "extra_total",
            "real_total",
            "unit_cost_real",
            "cost_lines",
        ):
            assert after[field] == before[field], field


def test_service_lines_listed_by_receipt(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0008", "SERV-0009", "SERV-0010"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        supplier_id = client.post(
            f"{BASE}/suppliers", headers=headers, json={"name": "Proveedor Listado"}
        ).json()["id"]
        order_id = client.post(
            f"{BASE}/orders",
            headers=headers,
            json={
                "supplier_id": supplier_id,
                "items": [{"product_id": "prod-c2", "quantity": 10, "unit_cost": 10.0}],
            },
        ).json()["id"]
        client.post(f"{BASE}/orders/{order_id}/confirm", headers=headers)
        item_id = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()["items"][0]["id"]
        with patch(
            "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
            return_value=FakeStockConnector(),
        ):
            client.post(
                f"{BASE}/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh",
                    "items": [{"purchase_item_id": item_id, "quantity": 5}],
                },
            )
            client.post(
                f"{BASE}/orders/{order_id}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh",
                    "items": [{"purchase_item_id": item_id, "quantity": 5}],
                },
            )
        detail = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()
        receipt_a, receipt_b = detail["receipts"][0]["id"], detail["receipts"][1]["id"]

        first = client.post(
            f"{SERVICE_LINES}/{receipt_a}/service-lines",
            headers=headers,
            json={"serial": "SERV-0008", "service_type": "RETIMBRADO",
                  "test_date": "2026-08-27", "result": "APROBADO",
                  "next_test_date": "2031-08-27"},
        ).json()["id"]
        second = client.post(
            f"{SERVICE_LINES}/{receipt_a}/service-lines",
            headers=headers,
            json={"serial": "SERV-0009", "service_type": "CAMBIO_VALVULA", "cost": 30},
        ).json()["id"]
        other = client.post(
            f"{SERVICE_LINES}/{receipt_b}/service-lines",
            headers=headers,
            json={"serial": "SERV-0010", "service_type": "LLENADO"},
        ).json()["id"]

        lines_a = client.get(f"{SERVICE_LINES}/{receipt_a}/service-lines", headers=headers).json()
        assert [ln["id"] for ln in lines_a] == [first, second]
        assert {ln["serial"] for ln in lines_a} == {"SERV-0008", "SERV-0009"}
        assert all(ln["receipt_id"] == receipt_a for ln in lines_a)

        lines_b = client.get(f"{SERVICE_LINES}/{receipt_b}/service-lines", headers=headers).json()
        assert [ln["id"] for ln in lines_b] == [other]
        assert all(ln["receipt_id"] == receipt_b for ln in lines_b)


def test_downgrade_0014_drops_table_receipts_intact(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["SERV-0011"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c3")[1]
        created = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=headers,
            json={"serial": "SERV-0011", "service_type": "PRUEBA_HIDROSTATICA", "cost": 80,
                  "test_date": "2026-08-27", "result": "APROBADO",
                  "next_test_date": "2029-08-27"},
        )
        assert created.status_code == 201, created.text

    module_path = (
        PROJECT_ROOT / "plugins" / "commerce" / "migrations" / "014_receipt_service_lines.py"
    )
    spec = importlib.util.spec_from_file_location("compras_migration_0014", module_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with app.state.session_factory() as db:
        from plugins.commerce.purchase.backend.models import (
            ComPurchaseReceipt,
            ComReceiptServiceLine,
        )

        receipt_count = db.scalar(select(func.count()).select_from(ComPurchaseReceipt))
        assert receipt_count == 1
        assert db.scalar(select(func.count()).select_from(ComReceiptServiceLine)) == 1

        migration.upgrade(db)

        db.commit()
        migration.downgrade(db)
        db.commit()

        bind = db.connection()
        inspector = inspect(bind)
        assert not inspector.has_table("com_receipt_service_lines")
        assert inspector.has_table("com_purchase_receipts")
        assert inspector.has_table("com_supplier_claims")
        assert inspector.has_table("com_supplier_invoices")
        assert db.scalar(select(func.count()).select_from(ComPurchaseReceipt)) == 1
