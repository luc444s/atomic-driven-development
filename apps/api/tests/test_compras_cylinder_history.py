"""Tests COMPRAS-016: historial técnico del envase (consulta consolidada)."""
from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.auth.models import User
from systutor.kernel.auth.security import hash_password
from systutor.kernel.permissions.models import Permission, Role, RolePermission, UserRole
from systutor.kernel.plugins.persistent import sync_plugin_registry_state
from systutor.kernel.tenants.models import Tenant

from apps.api.app.commands.seed_demo import seed_demo_data

BASE = "/api/v1/plugins/compras/purchase"
HISTORY = f"{BASE}/cylinders"


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


def _get_history(client: TestClient, headers: dict[str, str], serial: str):
    return client.get(f"{HISTORY}/{serial}/history", headers=headers)


def _full_flow(
    client: TestClient,
    headers: dict[str, str],
    cylinder_id: str,
    *,
    qty_receive: int = 6,
    dispatch_date: str | None = None,
) -> dict:
    """Despachar → retornar → recepción parcial vinculada al despacho."""
    supplier_id = client.post(
        f"{BASE}/suppliers", headers=headers, json={"name": "Proveedor Historial"}
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

    payload: dict = {
        "supplier_id": supplier_id,
        "order_id": order_id,
        "cylinders": [{"cylinder_id": cylinder_id, "service_type": "LLENADO"}],
    }
    if dispatch_date is not None:
        payload["dispatch_date"] = dispatch_date
    dispatch = client.post(f"{BASE}/dispatches", headers=headers, json=payload).json()
    client.post(f"{BASE}/dispatches/{dispatch['id']}/confirm", headers=headers)
    client.post(
        f"{BASE}/dispatches/{dispatch['id']}/return",
        headers=headers,
        json={"cylinders": [{"cylinder_id": cylinder_id}]},
    )

    with patch(
        "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
        return_value=FakeStockConnector(),
    ):
        receive = client.post(
            f"{BASE}/orders/{order_id}/receive",
            headers=headers,
            json={
                "warehouse_id": "wh",
                "dispatch_id": dispatch["id"],
                "items": [{"purchase_item_id": item_id, "quantity": qty_receive}],
            },
        )
    assert receive.status_code == 200, receive.text
    detail = client.get(f"{BASE}/orders/{order_id}", headers=headers).json()
    return {
        "supplier_id": supplier_id,
        "order_id": order_id,
        "dispatch_id": dispatch["id"],
        "receipt_id": detail["receipts"][-1]["id"],
    }


def _post_service_line(client: TestClient, headers: dict[str, str], receipt_id: str, payload: dict):
    return client.post(
        f"{BASE}/receipts/{receipt_id}/service-lines", headers=headers, json=payload
    )


def test_history_serial_unknown_404(app) -> None:
    _seed_and_enable(app)
    with TestClient(app) as client:
        headers = auth_headers(client)
        resp = _get_history(client, headers, "NO-EXISTE-999")
        assert resp.status_code == 404, resp.text
        assert "NO-EXISTE-999" in resp.json()["detail"]


def test_history_lists_dispatches_with_status(app) -> None:
    seeded = _seed_and_enable(app)
    ids = _create_cylinders(app, seeded["tenant_id"], ["HIST-0001"])
    cylinder_id = ids["HIST-0001"]
    with TestClient(app) as client:
        headers = auth_headers(client)
        flow = _full_flow(client, headers, cylinder_id)

        # Despacho PREPARADO posterior: se lista igual (no genera custodia).
        preparado = client.post(
            f"{BASE}/dispatches",
            headers=headers,
            json={
                "supplier_id": flow["supplier_id"],
                "cylinders": [{"cylinder_id": cylinder_id, "service_type": "PH"}],
            },
        ).json()
        assert preparado["status"] == "PREPARADO"

        resp = _get_history(client, headers, "HIST-0001")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["cylinder_id"] == cylinder_id
        assert body["serial"] == "HIST-0001"
        assert len(body["dispatches"]) == 2

        by_dispatch = {d["dispatch_id"]: d for d in body["dispatches"]}
        returned = by_dispatch[flow["dispatch_id"]]
        assert returned["status"] == "DEVUELTO"
        assert returned["returned_at"] is not None
        assert returned["order_id"] == flow["order_id"]
        assert returned["supplier_id"] == flow["supplier_id"]
        assert returned["service_type"] == "LLENADO"

        pending = by_dispatch[preparado["id"]]
        assert pending["status"] == "PENDIENTE"
        assert pending["returned_at"] is None


def test_history_lists_receipts_with_difference_type(app) -> None:
    seeded = _seed_and_enable(app)
    ids = _create_cylinders(app, seeded["tenant_id"], ["HIST-0002"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        flow = _full_flow(client, headers, ids["HIST-0002"], qty_receive=6)

        resp = _get_history(client, headers, "HIST-0002")
        assert resp.status_code == 200, resp.text
        receipts = resp.json()["receipts"]
        assert len(receipts) == 1
        receipt = receipts[0]
        assert receipt["receipt_id"] == flow["receipt_id"]
        assert receipt["order_id"] == flow["order_id"]
        assert receipt["qty_accepted"] == 6
        assert receipt["qty_rejected"] == 0
        assert receipt["difference_type"] == "FALTANTE"


def test_history_lists_services_with_ph_legal_data(app) -> None:
    seeded = _seed_and_enable(app)
    ids = _create_cylinders(app, seeded["tenant_id"], ["HIST-0003"])
    with TestClient(app) as client:
        headers = auth_headers(client)
        flow = _full_flow(client, headers, ids["HIST-0003"])
        created = _post_service_line(
            client,
            headers,
            flow["receipt_id"],
            {
                "serial": "HIST-0003",
                "service_type": "PRUEBA_HIDROSTATICA",
                "cost": 12.5,
                "notes": "PH de rutina",
                "test_date": "2026-08-20",
                "next_test_date": "2031-08-20",
                "result": "APROBADO",
                "document_ref": "CERT-PH-0160",
            },
        )
        assert created.status_code == 201, created.text

        resp = _get_history(client, headers, "HIST-0003")
        assert resp.status_code == 200, resp.text
        services = resp.json()["services"]
        assert len(services) == 1
        service = services[0]
        assert service["receipt_id"] == flow["receipt_id"]
        assert service["service_type"] == "PRUEBA_HIDROSTATICA"
        assert service["cost"] == 12.5
        assert service["notes"] == "PH de rutina"
        assert service["test_date"] == "2026-08-20"
        assert service["next_test_date"] == "2031-08-20"
        assert service["result"] == "APROBADO"
        assert service["document_ref"] == "CERT-PH-0160"


def test_history_tenant_isolated_404(app) -> None:
    seeded = _seed_and_enable(app)
    _create_cylinders(app, seeded["tenant_id"], ["HIST-0004"])

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant Historial B", slug="tenant-historial-b")
        db.add(other)
        db.flush()
        role = Role(tenant_id=other.id, name="admin")
        db.add(role)
        db.flush()
        perm = db.scalar(select(Permission).where(Permission.name == "compras.order.read"))
        db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        user = User(
            tenant_id=other.id,
            email="other-historial@example.com",
            full_name="Other Historial Admin",
            password_hash=hash_password("Other123!"),
            is_active=True,
            is_superadmin=False,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    with TestClient(app) as client:
        headers = auth_headers(client)
        ok = _get_history(client, headers, "HIST-0004")
        assert ok.status_code == 200, ok.text

        h_other = auth_headers(client, email="other-historial@example.com", password="Other123!")
        resp = _get_history(client, h_other, "HIST-0004")
        assert resp.status_code == 404, resp.text


def test_history_is_read_only_no_writes(app) -> None:
    seeded = _seed_and_enable(app)
    ids = _create_cylinders(app, seeded["tenant_id"], ["HIST-0005"])

    from plugins.commerce.purchase.backend.models import (
        ComDispatch,
        ComDispatchCylinder,
        ComPurchaseOrder,
        ComPurchaseOrderEvent,
        ComPurchaseReceipt,
        ComReceiptServiceLine,
    )
    from plugins.logistics.backend.models.cylinder import (
        LogisticsCylinder,
        LogisticsCylinderStateLog,
    )

    def _counts() -> dict[str, int]:
        with app.state.session_factory() as db:
            counts: dict[str, int] = {}
            for model in (
                ComDispatch,
                ComDispatchCylinder,
                ComPurchaseOrder,
                ComPurchaseOrderEvent,
                ComPurchaseReceipt,
                ComReceiptServiceLine,
                LogisticsCylinder,
                LogisticsCylinderStateLog,
            ):
                counts[model.__tablename__] = db.scalar(
                    select(func.count()).select_from(model)
                )
            return counts

    with TestClient(app) as client:
        headers = auth_headers(client)
        _full_flow(client, headers, ids["HIST-0005"])
        before = _counts()

        resp = _get_history(client, headers, "HIST-0005")
        assert resp.status_code == 200, resp.text
        assert _counts() == before


def test_history_ordered_chronologically(app) -> None:
    seeded = _seed_and_enable(app)
    ids = _create_cylinders(app, seeded["tenant_id"], ["HIST-0006"])
    cylinder_id = ids["HIST-0006"]
    with TestClient(app) as client:
        headers = auth_headers(client)

        # Despacho con fecha tardía (creado primero).
        late = _full_flow(client, headers, cylinder_id, dispatch_date="2026-08-20")
        # Despacho PREPARADO con fecha temprana (creado después).
        early = client.post(
            f"{BASE}/dispatches",
            headers=headers,
            json={
                "supplier_id": late["supplier_id"],
                "dispatch_date": "2026-08-05",
                "cylinders": [{"cylinder_id": cylinder_id, "service_type": "LLENADO"}],
            },
        ).json()

        # Segunda recepción que completa la orden (misma fecha, creada después).
        order_detail = client.get(f"{BASE}/orders/{late['order_id']}", headers=headers).json()
        item_id = order_detail["items"][0]["id"]
        with patch(
            "plugins.commerce.purchase.backend.routers.receipts._build_stock_connector",
            return_value=FakeStockConnector(),
        ):
            second = client.post(
                f"{BASE}/orders/{late['order_id']}/receive",
                headers=headers,
                json={
                    "warehouse_id": "wh",
                    "dispatch_id": late["dispatch_id"],
                    "items": [{"purchase_item_id": item_id, "quantity": 4}],
                },
            )
        assert second.status_code == 200, second.text
        detail = client.get(f"{BASE}/orders/{late['order_id']}", headers=headers).json()
        receipt_ids = [r["id"] for r in detail["receipts"]]

        # Dos servicios: LLENADO luego PH.
        latest_receipt_id = detail["receipts"][-1]["id"]
        llenado = _post_service_line(
            client,
            headers,
            latest_receipt_id,
            {"serial": "HIST-0006", "service_type": "LLENADO", "cost": 5.0},
        )
        assert llenado.status_code == 201, llenado.text
        ph = _post_service_line(
            client,
            headers,
            latest_receipt_id,
            {
                "serial": "HIST-0006",
                "service_type": "PRUEBA_HIDROSTATICA",
                "test_date": "2026-08-21",
                "next_test_date": "2031-08-21",
                "result": "APROBADO",
            },
        )
        assert ph.status_code == 201, ph.text

        resp = _get_history(client, headers, "HIST-0006")
        assert resp.status_code == 200, resp.text
        body = resp.json()

        dispatch_dates = [d["dispatch_date"] for d in body["dispatches"]]
        assert dispatch_dates == sorted(dispatch_dates)
        assert {d["dispatch_id"] for d in body["dispatches"]} == {late["dispatch_id"], early["id"]}

        receipt_order = [r["receipt_id"] for r in body["receipts"]]
        assert receipt_order == [rid for rid in receipt_ids if rid in receipt_order]
        assert len(receipt_order) == 2

        created_ats = [s["created_at"] for s in body["services"]]
        assert created_ats == sorted(created_ats)
        assert [s["service_type"] for s in body["services"]] == ["LLENADO", "PRUEBA_HIDROSTATICA"]
