"""Tests COMPRAS-017: conciliación física del inventario en custodia.

La custodia (005/007/008) es verdad ajena: los conteos SOLO la leen.
El snapshot de seriales se PERSISTE al crear y es la base inmutable del
diff al cerrar; las discrepancias se resuelven con evento auditable y
ninguna fila de custodia cambia jamás (§45).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

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
COUNTS = f"{BASE}/dispatches/physical-counts"


def auth_headers(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    token = client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    ).json()["access_token"]
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


def _setup(app, serials: list[str]) -> tuple[TestClient, dict[str, str], str, dict[str, str], str]:
    """Devuelve client, headers, supplier_id, {serial: cylinder_id} y despacho confirmado.

    El despacho queda DESPACHADO → todos los seriales EN_CUSTODIA (fuente 005).
    """
    seeded = _seed_and_enable(app)
    client = TestClient(app)
    headers = auth_headers(client)

    supplier_id = client.post(
        f"{BASE}/suppliers", headers=headers, json={"name": "Proveedor Conteo"}
    ).json()["id"]

    cylinder_ids = _create_cylinders(app, seeded["tenant_id"], serials)

    dispatch = client.post(
        f"{BASE}/dispatches",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "cylinders": [{"cylinder_id": cid} for cid in cylinder_ids.values()],
        },
    ).json()
    confirmed = client.post(
        f"{BASE}/dispatches/{dispatch['id']}/confirm", headers=headers
    ).json()
    assert confirmed["status"] == "DESPACHADO", confirmed
    assert all(c["status"] == "EN_CUSTODIA" for c in confirmed["cylinders"])

    return client, headers, supplier_id, cylinder_ids, dispatch["id"]


def _create_count(client, headers, supplier_id: str) -> dict:
    resp = client.post(COUNTS, headers=headers, json={"supplier_id": supplier_id})
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_count_snapshot_captures_custody_serials(app) -> None:
    serials = ["FIS-0001", "FIS-0002", "FIS-0003"]
    client, headers, supplier_id, cylinder_ids, _dispatch = _setup(app, serials)

    count = _create_count(client, headers, supplier_id)
    assert count["status"] == "EN_CURSO"
    assert count["expected_total"] == 3
    assert count["found_total"] == 0
    assert count["match_count"] == 0
    assert count["supplier_id"] == supplier_id
    assert count["counted_by"]
    assert count["closed_at"] is None

    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    snapshot = sorted(detail["expected_serials"], key=lambda s: s["serial"])
    assert [s["serial"] for s in snapshot] == sorted(serials)
    assert all(s["cylinder_id"] == cylinder_ids[s["serial"]] for s in snapshot)
    assert all(s["captured_at"] for s in snapshot)

    # El despacho ajeno a este proveedor no entra en el snapshot (filtro por supplier)
    other_supplier = client.post(
        f"{BASE}/suppliers", headers=headers, json={"name": "Proveedor Conteo B"}
    ).json()["id"]
    other_cyls = _create_cylinders(app, _seeded_tenant(app), ["FIS-OTRO"])
    other_dispatch = client.post(
        f"{BASE}/dispatches",
        headers=headers,
        json={"supplier_id": other_supplier, "cylinders": [{"cylinder_id": other_cyls["FIS-OTRO"]}]},
    ).json()
    confirmed = client.post(
        f"{BASE}/dispatches/{other_dispatch['id']}/confirm", headers=headers
    ).json()
    assert confirmed["status"] == "DESPACHADO"

    detail_b = client.get(f"{COUNTS}/{_create_count(client, headers, other_supplier)['id']}", headers=headers).json()
    assert [s["serial"] for s in detail_b["expected_serials"]] == ["FIS-OTRO"]
    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    assert len(detail["expected_serials"]) == 3


def test_count_snapshot_persisted_visible_after_restart(app) -> None:
    serials = ["FIS-1001", "FIS-1002"]
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, serials)

    count = _create_count(client, headers, supplier_id)
    before = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()["expected_serials"]

    # Cierre con faltante: el snapshot NO cambia
    closed = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-1001"}]},
    )
    assert closed.status_code == 200, closed.text

    # "Reinicio": nueva sesión de BD y nuevo cliente sobre el mismo estado persistido
    with app.state.session_factory() as db:
        from plugins.commerce.purchase.backend.models import ComPhysicalCountExpectedSerial

        rows = db.scalars(
            select(ComPhysicalCountExpectedSerial)
            .where(ComPhysicalCountExpectedSerial.count_id == count["id"])
            .order_by(ComPhysicalCountExpectedSerial.serial)
        ).all()
        persisted = sorted((r.serial, r.cylinder_id, r.captured_at.isoformat()) for r in rows)
    before_sorted = sorted((s["serial"], s["cylinder_id"], s["captured_at"]) for s in before)
    assert persisted == before_sorted

    with TestClient(app) as client2:
        after = client2.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    assert sorted(after["expected_serials"], key=lambda s: s["id"]) == sorted(before, key=lambda s: s["id"])
    assert after["status"] == "CERRADA"
    assert [i["discrepancy_type"] for i in after["items"]] == ["FALTANTE"]


def test_close_undeclared_serial_with_note_is_no_declarado(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-2001"])
    # Serial registrado en el sistema pero NUNCA despachado a este proveedor
    _create_cylinders(app, _seeded_tenant(app), ["AJENO-77"])

    count = _create_count(client, headers, supplier_id)
    closed = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "AJENO-77", "condition_note": "apareció en el local"}]},
    )
    assert closed.status_code == 200, closed.text

    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    by_type = {i["discrepancy_type"]: i for i in detail["items"]}
    assert set(by_type) == {"FALTANTE", "NO_DECLARADO"}
    undeclared = by_type["NO_DECLARADO"]
    assert undeclared["serial"] == "AJENO-77"
    assert undeclared["expected"] is False
    assert undeclared["found"] is True
    # La condition_note del NO_DECLARADO se conserva en notes del ítem
    assert undeclared["notes"] == "apareció en el local"
    assert by_type["FALTANTE"]["serial"] == "FIS-2001"
    assert detail["expected_total"] == 1
    assert detail["found_total"] == 1
    assert detail["match_count"] == 0


def _seeded_tenant(app) -> str:
    with app.state.session_factory() as db:
        from systutor.kernel.tenants.models import Tenant as T

        return db.scalar(select(T.id).where(T.slug == "demo"))


def test_close_computes_faltante_and_no_declarado(app) -> None:
    serials = ["FIS-3001", "FIS-3002", "FIS-3003"]
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, serials)
    _create_cylinders(app, _seeded_tenant(app), ["AJENO-88"])

    count = _create_count(client, headers, supplier_id)
    closed = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-3001"}, {"serial": "AJENO-88"}]},
    )
    assert closed.status_code == 200, closed.text
    body = closed.json()
    assert body["expected_total"] == 3
    assert body["found_total"] == 2
    assert body["match_count"] == 1
    assert body["status"] == "CERRADA"
    assert body["closed_at"] is not None

    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    faltantes = sorted(i["serial"] for i in detail["items"] if i["discrepancy_type"] == "FALTANTE")
    assert faltantes == ["FIS-3002", "FIS-3003"]
    assert all(i["expected"] is True and i["found"] is False for i in detail["items"] if i["discrepancy_type"] == "FALTANTE")
    no_declarado = [i for i in detail["items"] if i["discrepancy_type"] == "NO_DECLARADO"]
    assert len(no_declarado) == 1
    assert no_declarado[0]["serial"] == "AJENO-88"
    assert len(detail["events"]) == 2
    assert detail["events"][-1]["from_status"] == "EN_CURSO"
    assert detail["events"][-1]["to_status"] == "CERRADA"


def test_close_condition_note_creates_condicion_item(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-4001", "FIS-4002"])

    count = _create_count(client, headers, supplier_id)
    closed = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={
            "found": [
                {"serial": "FIS-4001", "condition_note": "válvula gastada"},
                {"serial": "FIS-4002"},
            ],
            "notes": "cierre con observación",
        },
    )
    assert closed.status_code == 200, closed.text

    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    condicion = [i for i in detail["items"] if i["discrepancy_type"] == "CONDICION"]
    assert len(condicion) == 1
    assert condicion[0]["serial"] == "FIS-4001"
    assert condicion[0]["expected"] is True
    assert condicion[0]["found"] is True
    assert condicion[0]["notes"] == "válvula gastada"
    # FIS-4002 cotejó limpio: no genera ítem
    assert [i["serial"] for i in detail["items"]] == ["FIS-4001"]
    assert detail["expected_total"] == 2
    assert detail["found_total"] == 2
    assert detail["match_count"] == 2
    assert detail["notes"].endswith("cierre con observación")


def test_close_already_closed_409(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-5001"])
    count = _create_count(client, headers, supplier_id)

    first = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-5001"}]},
    )
    assert first.status_code == 200
    again = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-5001"}]},
    )
    assert again.status_code == 409, again.text
    assert "CERRADA" in again.json()["detail"]


def test_close_tenant_isolated_404(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-6001"])
    count = _create_count(client, headers, supplier_id)

    with app.state.session_factory() as db:
        other = Tenant(name="Tenant Conteo B", slug="tenant-conteo-b")
        db.add(other)
        db.flush()
        role = Role(tenant_id=other.id, name="admin")
        db.add(role)
        db.flush()
        for perm_name in ("compras.dispatch.read", "compras.dispatch.manage"):
            perm = db.scalar(select(Permission).where(Permission.name == perm_name))
            db.add(RolePermission(role_id=role.id, permission_id=perm.id))
        user = User(
            tenant_id=other.id,
            email="other-conteo@example.com",
            full_name="Other Admin",
            password_hash=hash_password("Other123!"),
            is_active=True,
            is_superadmin=False,
        )
        db.add(user)
        db.flush()
        db.add(UserRole(user_id=user.id, role_id=role.id))
        db.commit()

    with TestClient(app) as client2:
        h_other = auth_headers(client2, email="other-conteo@example.com", password="Other123!")
        list_resp = client2.get(COUNTS, headers=h_other)
        assert list_resp.status_code == 200
        assert list_resp.json() == []
        detail = client2.get(f"{COUNTS}/{count['id']}", headers=h_other)
        assert detail.status_code == 404, detail.text
        close = client2.post(
            f"{COUNTS}/{count['id']}/close",
            headers=h_other,
            json={"found": [{"serial": "FIS-6001"}]},
        )
        assert close.status_code == 404, close.text


def test_list_physical_counts_not_shadowed(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-7001"])
    count_a = _create_count(client, headers, supplier_id)
    count_b = _create_count(client, headers, supplier_id)

    # GET /dispatches/physical-counts NO debe ser capturado por /{dispatch_id}
    listed = client.get(COUNTS, headers=headers)
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert isinstance(body, list)
    assert sorted(c["id"] for c in body) == sorted([count_a["id"], count_b["id"]])
    assert "detail" not in body[0] or body[0].get("status")

    detail = client.get(f"{COUNTS}/{count_a['id']}", headers=headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["id"] == count_a["id"]

    # El router de despachos sigue operativo (no lo pisamos)
    dispatches = client.get(f"{BASE}/dispatches", headers=headers)
    assert dispatches.status_code == 200


def test_resolution_stamps_event(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-8001", "FIS-8002"])

    count = _create_count(client, headers, supplier_id)
    client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-8001"}]},
    )
    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    faltante = next(i for i in detail["items"] if i["discrepancy_type"] == "FALTANTE")
    events_before = len(detail["events"])

    resolved = client.post(
        f"{COUNTS}/{count['id']}/items/{faltante['id']}/resolve",
        headers=headers,
        json={"resolution": "RECLAMADA", "reason": "reclamo al proveedor por pérdida"},
    )
    assert resolved.status_code == 200, resolved.text

    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    item = next(i for i in detail["items"] if i["id"] == faltante["id"])
    assert item["resolution"] == "RECLAMADA"
    assert item["resolved_at"] is not None
    assert item["resolved_by"]
    # Exactamente UN evento por resolución
    assert len(detail["events"]) == events_before + 1
    event = detail["events"][-1]
    assert event["from_status"] == "FALTANTE"
    assert event["to_status"] == "RECLAMADA"
    assert "FIS-8002" in event["reason"]
    assert "reclamo al proveedor por pérdida" in event["reason"]
    assert event["user_id"]


def test_resolution_twice_409(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-9001"])
    count = _create_count(client, headers, supplier_id)
    client.post(
        f"{COUNTS}/{count['id']}/close", headers=headers, json={"found": []}
    )
    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    item = detail["items"][0]

    first = client.post(
        f"{COUNTS}/{count['id']}/items/{item['id']}/resolve",
        headers=headers,
        json={"resolution": "ACEPTADA", "reason": "se acepta la diferencia"},
    )
    assert first.status_code == 200
    again = client.post(
        f"{COUNTS}/{count['id']}/items/{item['id']}/resolve",
        headers=headers,
        json={"resolution": "OBSERVADA", "reason": "intento repetido"},
    )
    assert again.status_code == 409, again.text
    assert "ya fue resuelta" in again.json()["detail"]


def test_resolution_does_not_mutate_custody(app) -> None:
    serials = ["FIS-1101", "FIS-1102"]
    client, headers, supplier_id, cylinder_ids, dispatch_id = _setup(app, serials)
    tenant_id = _seeded_tenant(app)
    _create_cylinders(app, tenant_id, ["AJENO-99"])

    count = _create_count(client, headers, supplier_id)
    close_resp = client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-1101"}, {"serial": "AJENO-99"}]},
    )
    assert close_resp.status_code == 200, close_resp.text

    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    faltante = next(i for i in detail["items"] if i["discrepancy_type"] == "FALTANTE")
    client.post(
        f"{COUNTS}/{count['id']}/items/{faltante['id']}/resolve",
        headers=headers,
        json={"resolution": "RECLAMADA", "reason": "se reclama al proveedor"},
    )

    # Custodia intacta: mismos seriales EN_CUSTODIA, despacho DESPACHADO
    custody = client.get(
        f"{BASE}/dispatches/suppliers/{supplier_id}/custody", headers=headers
    ).json()
    assert sorted(e["serial"] for e in custody) == sorted(serials)
    assert all(e["status"] if "status" in e else True for e in custody)
    dispatch = client.get(f"{BASE}/dispatches/{dispatch_id}", headers=headers).json()
    assert dispatch["status"] == "DESPACHADO"
    assert all(c["status"] == "EN_CUSTODIA" for c in dispatch["cylinders"])

    # Cero escrituras lg_*: estados de cilindro sin cambios
    with app.state.session_factory() as db:
        from plugins.logistics.backend.models.cylinder import LogisticsCylinder

        states = dict(db.execute(
            select(LogisticsCylinder.serial, LogisticsCylinder.current_state).where(
                LogisticsCylinder.serial.in_(serials),
                LogisticsCylinder.tenant_id == tenant_id,
            )
        ).all())
        assert states == {s: "EN_ALMACEN_VACIO" for s in serials}


def test_counts_never_delete_history(app) -> None:
    client, headers, supplier_id, _cylinder_ids, _dispatch = _setup(app, ["FIS-1201", "FIS-1202"])
    count = _create_count(client, headers, supplier_id)
    client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-1201"}]},
    )
    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    item = detail["items"][0]
    client.post(
        f"{COUNTS}/{count['id']}/items/{item['id']}/resolve",
        headers=headers,
        json={"resolution": "OBSERVADA", "reason": "bajo observación"},
    )

    tenant_id = _seeded_tenant(app)
    with app.state.session_factory() as db:
        from plugins.commerce.purchase.backend.models import (
            ComPhysicalCount,
            ComPhysicalCountEvent,
            ComPhysicalCountExpectedSerial,
            ComPhysicalCountItem,
        )

        cid = count["id"]
        assert db.scalar(
            select(func.count()).select_from(ComPhysicalCountEvent).where(
                ComPhysicalCountEvent.count_id == cid
            )
        ) == 3  # create + close + resolve
        assert db.scalar(
            select(func.count()).select_from(ComPhysicalCountExpectedSerial).where(
                ComPhysicalCountExpectedSerial.count_id == cid
            )
        ) == 2  # snapshot intacto tras cierre y resolución
        assert db.scalar(
            select(func.count()).select_from(ComPhysicalCountItem).where(
                ComPhysicalCountItem.count_id == cid
            )
        ) == 1
        row = db.scalar(select(ComPhysicalCount).where(ComPhysicalCount.id == cid))
        assert row.status == "CERRADA"

        # El ítem resuelto conserva su resolución (nada se borra ni edita en historia)
        item_row = db.scalar(
            select(ComPhysicalCountItem).where(ComPhysicalCountItem.id == item["id"])
        )
        assert item_row.resolution == "OBSERVADA"
        assert item_row.resolved_at is not None
        assert tenant_id  # sanity


def test_downgrade_017_drops_tables_custody_intact(app) -> None:
    client, headers, supplier_id, _cylinder_ids, dispatch_id = _setup(app, ["FIS-1301", "FIS-1302"])
    count = _create_count(client, headers, supplier_id)
    client.post(
        f"{COUNTS}/{count['id']}/close",
        headers=headers,
        json={"found": [{"serial": "FIS-1301"}]},
    )
    detail = client.get(f"{COUNTS}/{count['id']}", headers=headers).json()
    item = detail["items"][0]
    client.post(
        f"{COUNTS}/{count['id']}/items/{item['id']}/resolve",
        headers=headers,
        json={"resolution": "RECLAMADA", "reason": "prueba de reversibilidad"},
    )

    module_path = (
        PROJECT_ROOT / "plugins" / "commerce" / "migrations" / "017_physical_counts.py"
    )
    spec = importlib.util.spec_from_file_location("compras_migration_0017", module_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "0017"

    with app.state.session_factory() as db:
        from plugins.commerce.purchase.backend.models import (
            ComDispatch,
            ComDispatchCylinder,
        )

        custody_rows = db.scalar(
            select(func.count()).select_from(ComDispatchCylinder).where(
                ComDispatchCylinder.status == "EN_CUSTODIA"
            )
        )
        dispatch_rows = db.scalar(select(func.count()).select_from(ComDispatch))
        assert custody_rows == 2
        assert dispatch_rows == 1

        migration.downgrade(db)
        db.commit()

        bind = db.connection()
        inspector = inspect(bind)
        # Aserción negativa: las 4 tablas del conteo físico AUSENTES
        assert not inspector.has_table("com_physical_counts")
        assert not inspector.has_table("com_physical_count_expected_serials")
        assert not inspector.has_table("com_physical_count_items")
        assert not inspector.has_table("com_physical_count_events")
        # Custodia, despachos y demás compras intactos
        assert inspector.has_table("com_dispatches")
        assert inspector.has_table("com_dispatch_cylinders")
        assert inspector.has_table("com_suppliers")
        assert inspector.has_table("com_supplier_claims")
        assert inspector.has_table("com_purchase_orders")
        assert db.scalar(
            select(func.count()).select_from(ComDispatchCylinder).where(
                ComDispatchCylinder.status == "EN_CUSTODIA"
            )
        ) == 2
        assert db.scalar(select(func.count()).select_from(ComDispatch)) == 1

        # Reversible: re-upgrade deja las 4 tablas operativas
        migration.upgrade(db)
        db.commit()
        inspector = inspect(db.connection())
        assert inspector.has_table("com_physical_counts")
        assert inspector.has_table("com_physical_count_expected_serials")
