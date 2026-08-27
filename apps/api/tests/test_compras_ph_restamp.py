from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import inspect, select
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
        json={"name": "Proveedor PH"},
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
                "items": [{"purchase_item_id": item_id, "quantity": quantity}],
            },
        )
    detail = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()
    return order_id, detail["receipts"][-1]["id"]


def _post_line(client, headers, receipt_id: str, payload: dict):
    return client.post(
        f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=headers, json=payload
    )


def test_ph_line_requires_test_date_and_result_422(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0001"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c1")[1]

        missing_both = _post_line(
            client, headers, receipt_id,
            {"serial": "PH-0001", "service_type": "PRUEBA_HIDROSTATICA"},
        )
        assert missing_both.status_code == 422, missing_both.text

        missing_result = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0001",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-20",
            },
        )
        assert missing_result.status_code == 422, missing_result.text

        missing_date = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0001",
                "service_type": "PRUEBA_HIDROSTATICA",
                "result": "APROBADO",
                "next_test_date": "2031-08-20",
            },
        )
        assert missing_date.status_code == 422, missing_date.text


def test_ph_line_aprobado_requires_next_test_date_422(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0002"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c2")[1]

        resp = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0002",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-20",
                "result": "APROBADO",
            },
        )
        assert resp.status_code == 422, resp.text


def test_ph_line_rechazado_rejects_next_test_date_422(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0003"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c3")[1]

        resp = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0003",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-20",
                "result": "RECHAZADO",
                "next_test_date": "2031-08-20",
            },
        )
        assert resp.status_code == 422, resp.text

        ok = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0003",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-20",
                "result": "RECHAZADO",
            },
        )
        assert ok.status_code == 201, ok.text
        assert ok.json()["next_test_date"] is None


def test_retimbrado_line_accepts_legal_fields(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0004"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c4")[1]

        resp = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0004",
                "service_type": "RETIMBRADO",
                "cost": 35.0,
                "notes": "retimbrado con PH",
                "test_date": "2026-08-21",
                "next_test_date": "2031-08-21",
                "result": "APROBADO",
                "document_ref": "ACTA-2026-0091",
            },
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["service_type"] == "RETIMBRADO"
        assert body["test_date"] == "2026-08-21"
        assert body["next_test_date"] == "2031-08-21"
        assert body["result"] == "APROBADO"
        assert body["document_ref"] == "ACTA-2026-0091"


def test_non_legal_type_rejects_legal_fields_422(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0005"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c5")[1]

        resp = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0005",
                "service_type": "LLENADO",
                "next_test_date": "2031-08-20",
            },
        )
        assert resp.status_code == 422, resp.text

        resp = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0005",
                "service_type": "INSPECCION",
                "test_date": "2026-08-20",
                "result": "APROBADO",
            },
        )
        assert resp.status_code == 422, resp.text


def test_ph_legal_data_visible_in_read(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0006"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c6")[1]

        created = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0006",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-22",
                "next_test_date": "2032-08-22",
                "result": "APROBADO",
                "document_ref": "CERT-PH-0042",
            },
        )
        assert created.status_code == 201, created.text

        listed = client.get(f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=headers)
        assert listed.status_code == 200, listed.text
        rows = listed.json()
        assert len(rows) == 1
        row = rows[0]
        assert row["serial"] == "PH-0006"
        assert row["test_date"] == "2026-08-22"
        assert row["next_test_date"] == "2032-08-22"
        assert row["result"] == "APROBADO"
        assert row["document_ref"] == "CERT-PH-0042"


def test_ph_line_tenant_isolated_404(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0007"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c7")[1]
        created = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0007",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-23",
                "result": "RECHAZADO",
            },
        )
        assert created.status_code == 201, created.text
        line_id = created.json()["id"]

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant PH B", slug="tenant-ph-b")
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
            email="other-ph@example.com",
            full_name="Other PH Admin",
            password_hash=hash_password("Other123!"),
            is_active=True,
            is_superadmin=False,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    with TestClient(app) as client:
        h_other = auth_headers(client, email="other-ph@example.com", password="Other123!")
        get_resp = client.get(f"{SERVICE_LINES}/{receipt_id}/service-lines", headers=h_other)
        assert get_resp.status_code == 404, get_resp.text
        post_resp = client.post(
            f"{SERVICE_LINES}/{receipt_id}/service-lines",
            headers=h_other,
            json={
                "serial": "PH-0007",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-23",
                "result": "RECHAZADO",
            },
        )
        assert post_resp.status_code == 404, post_resp.text
        del_resp = client.delete(
            f"{SERVICE_LINES}/{receipt_id}/service-lines/{line_id}", headers=h_other
        )
        assert del_resp.status_code == 404, del_resp.text


def test_downgrade_0015_drops_legal_columns_table_intact(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["PH-0008"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        receipt_id = _make_receipt(client, headers, "prod-c1")[1]
        created = _post_line(
            client, headers, receipt_id,
            {
                "serial": "PH-0008",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-24",
                "next_test_date": "2031-08-24",
                "result": "APROBADO",
                "document_ref": "CERT-PH-0099",
            },
        )
        assert created.status_code == 201, created.text

    module_path = (
        PROJECT_ROOT / "plugins" / "commerce" / "migrations" / "015_ph_restamp_legal.py"
    )
    spec = importlib.util.spec_from_file_location("compras_migration_0015", module_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    with app.state.session_factory() as db:
        from plugins.commerce.purchase.backend.models import (
            ComPurchaseReceipt,
            ComReceiptServiceLine,
        )

        legal_columns = {"test_date", "next_test_date", "result", "document_ref"}
        legal_index = "ix_com_receipt_service_lines_next_test_date"

        bind = db.connection()
        inspector = inspect(bind)
        assert legal_columns <= {
            c["name"] for c in inspector.get_columns("com_receipt_service_lines")
        }
        assert legal_index in {
            i["name"] for i in inspector.get_indexes("com_receipt_service_lines")
        }

        migration.upgrade(db)
        db.commit()

        migration.downgrade(db)
        db.commit()

        inspector = inspect(db.connection())
        remaining = {c["name"] for c in inspector.get_columns("com_receipt_service_lines")}
        assert legal_columns.isdisjoint(remaining), remaining
        assert legal_index not in {
            i["name"] for i in inspector.get_indexes("com_receipt_service_lines")
        }
        assert inspector.has_table("com_receipt_service_lines")
        assert inspector.has_table("com_purchase_receipts")

        # Columnas legales eliminadas: la fila de 014 sobrevive (serial snapshot).
        rows = db.execute(
            select(ComReceiptServiceLine.id, ComReceiptServiceLine.serial)
        ).all()
        assert len(rows) == 1
        assert rows[0][1] == "PH-0008"
        assert db.scalar(select(ComPurchaseReceipt.id)) is not None
