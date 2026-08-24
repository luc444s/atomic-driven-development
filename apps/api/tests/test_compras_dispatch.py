"""Tests COMPRAS-005: despacho por serial y custodia del proveedor."""
from __future__ import annotations

from fastapi.testclient import TestClient
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.plugins.persistent import sync_plugin_registry_state

from apps.api.app.commands.seed_demo import seed_demo_data


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    token = response.json()["access_token"]
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


def _setup(app) -> tuple[TestClient, dict[str, str], str, list[str]]:
    """Devuelve client, headers, supplier_id y 2 cylinder_ids creados en lg_cylinders."""
    with app.state.session_factory() as db:
        seeded = seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
    enable_compras_plugin(app, seeded)

    client = TestClient(app)
    headers = auth_headers(client)

    supplier_id = client.post(
        "/api/v1/plugins/compras/purchase/suppliers",
        headers=headers,
        json={"name": "Proveedor Despachos"},
    ).json()["id"]

    cylinder_ids: list[str] = []
    with app.state.session_factory() as db:
        for i, serial in enumerate(["DISP-0001", "DISP-0002"]):
            from plugins.logistics.backend.models.cylinder import LogisticsCylinder

            cyl = LogisticsCylinder(
                tenant_id=seeded["tenant_id"],
                serial=serial,
                container_type="CYLINDER",
                current_state="EN_ALMACEN_VACIO",
            )
            db.add(cyl)
            db.flush()
            cylinder_ids.append(cyl.id)
        db.commit()

    return client, headers, supplier_id, cylinder_ids


def test_dispatch_create_requires_valid_tenant_cylinders(app) -> None:
    client, headers, supplier_id, cylinder_ids = _setup(app)

    # Cilindro inexistente → 400
    bad = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "cylinders": [{"cylinder_id": "no-existe", "service_type": "LLENADO"}],
        },
    )
    assert bad.status_code == 400, bad.text
    assert "no encontrado" in bad.json()["detail"]

    # Creación válida con ambos seriales
    ok = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "notes": "despacho de prueba",
            "cylinders": [
                {"cylinder_id": cylinder_ids[0], "service_type": "LLENADO"},
                {"cylinder_id": cylinder_ids[1], "service_type": "PH"},
            ],
        },
    )
    assert ok.status_code == 201, ok.text
    body = ok.json()
    assert body["status"] == "PREPARADO"
    assert len(body["cylinders"]) == 2


def test_dispatch_rejects_duplicate_serial_and_cylinders_in_other_custody(app) -> None:
    client, headers, supplier_id, cylinder_ids = _setup(app)
    base = {"supplier_id": supplier_id}

    dup = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={**base, "cylinders": [{"cylinder_id": cylinder_ids[0]}, {"cylinder_id": cylinder_ids[0]}]},
    )
    assert dup.status_code == 400
    assert "duplicado" in dup.json()["detail"].lower()

    # Primer despacho confirmado → cilindro 0 queda EN_CUSTODIA
    first = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={**base, "cylinders": [{"cylinder_id": cylinder_ids[0]}]},
    ).json()
    client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{first['id']}/confirm", headers=headers
    )

    # Intentar enviar el mismo cilindro a otro despacho → 400 (§8/§45)
    second = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={**base, "cylinders": [{"cylinder_id": cylinder_ids[0]}]},
    )
    assert second.status_code == 400, second.text
    assert "custodia" in second.json()["detail"].lower()


def test_confirm_moves_all_items_to_custody_and_cancel_only_in_preparado(app) -> None:
    client, headers, supplier_id, cylinder_ids = _setup(app)

    d1 = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={"supplier_id": supplier_id, "cylinders": [{"cylinder_id": cylinder_ids[0]}]},
    ).json()
    d2 = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={"supplier_id": supplier_id, "cylinders": [{"cylinder_id": cylinder_ids[1]}]},
    ).json()

    # Confirmar d1 → sus items EN_CUSTODIA
    confirmed = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{d1['id']}/confirm", headers=headers
    ).json()
    assert confirmed["status"] == "DESPACHADO"
    assert all(c["status"] == "EN_CUSTODIA" for c in confirmed["cylinders"])

    # DESPACHADO es terminal para cancel
    late_cancel = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{d1['id']}/cancel", headers=headers
    )
    assert late_cancel.status_code == 400

    # Cancelar d2 aún PREPARADO funciona y no deja custodia
    cancelled = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{d2['id']}/cancel", headers=headers
    ).json()
    assert cancelled["status"] == "CANCELLED" or cancelled["status"] == "CANCELADO"
    custody = client.get(
        f"/api/v1/plugins/compras/purchase/dispatches/suppliers/{supplier_id}/custody",
        headers=headers,
    ).json()
    assert all(e["cylinder_id"] != cylinder_ids[1] for e in custody)


def test_custody_listing_with_days_out_and_summary(app) -> None:
    client, headers, supplier_id, cylinder_ids = _setup(app)

    dispatch = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={"supplier_id": supplier_id, "cylinders": [{"cylinder_id": cylinder_ids[0], "service_type": "LLENADO"}]},
    ).json()
    client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{dispatch['id']}/confirm", headers=headers
    )

    custody = client.get(
        f"/api/v1/plugins/compras/purchase/dispatches/suppliers/{supplier_id}/custody",
        headers=headers,
    ).json()
    assert len(custody) == 1
    entry = custody[0]
    assert entry["cylinder_id"] == cylinder_ids[0]
    assert entry["serial"] == "DISP-0001"
    assert entry["days_out"] >= 0

    summary = client.get(
        "/api/v1/plugins/compras/purchase/dispatches/custody/summary", headers=headers
    ).json()
    row = next(r for r in summary if r["supplier_id"] == supplier_id)
    assert row["total_cylinders"] == 1
    assert row["oldest_days_out"] >= 0

    # Filtro permanencia §12: days_gt alto excluye la entrada joven
    strict = client.get(
        f"/api/v1/plugins/compras/purchase/dispatches/suppliers/{supplier_id}/custody?days_gt=9999",
        headers=headers,
    ).json()
    assert strict == []


# ── COMPRAS-007: retorno por serial + vínculo opcional a jornadas ──

def _crear_y_confirmar(client, headers, supplier_id, cylinder_id):
    d = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={"supplier_id": supplier_id, "cylinders": [{"cylinder_id": cylinder_id}]},
    ).json()
    client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{d['id']}/confirm", headers=headers
    )
    return d


def test_return_marks_serials_devuelto_and_keeps_others_in_custody(app) -> None:
    client, headers, supplier_id, cyls = _setup(app)
    d1 = _crear_y_confirmar(client, headers, supplier_id, cyls[0])
    d2 = _crear_y_confirmar(client, headers, supplier_id, cyls[1])

    # Retorno parcial: solo el serial de d2
    ret = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{d2['id']}/return",
        headers=headers,
        json={"cylinders": [{"cylinder_id": cyls[1]}], "notes": "volvio hoy"},
    )
    assert ret.status_code == 200, ret.text
    body = ret.json()
    assert body["status"] == "RETORNADO"  # único serial → custodia resuelta
    item = body["cylinders"][0]
    assert item["status"] == "DEVUELTO"
    assert item["returned_at"] is not None

    # El de d1 sigue en custodia
    custody = client.get(
        f"/api/v1/plugins/compras/purchase/dispatches/suppliers/{supplier_id}/custody",
        headers=headers,
    ).json()
    assert [e["cylinder_id"] for e in custody] == [cyls[0]]


def test_return_rejects_foreign_or_already_returned_serial(app) -> None:
    client, headers, supplier_id, cyls = _setup(app)
    _crear_y_confirmar(client, headers, supplier_id, cyls[0])
    foreign = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={"supplier_id": supplier_id, "cylinders": [{"cylinder_id": cyls[1]}]},
    ).json()
    client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{foreign['id']}/confirm",
        headers=headers,
    )

    ret = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{foreign['id']}/return",
        headers=headers,
        json={"cylinders": [{"cylinder_id": cyls[0]}]},
    )
    assert ret.status_code == 400
    assert "no pertenecen" in ret.json()["detail"]

    # Ya devuelto → 400
    client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{foreign['id']}/confirm",
        headers=headers,
    )
    first = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{foreign['id']}/return",
        headers=headers,
        json={"cylinders": [{"cylinder_id": cyls[1]}]},
    )
    assert first.status_code == 200
    again = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{foreign['id']}/return",
        headers=headers,
        json={"cylinders": [{"cylinder_id": cyls[1]}]},
    )
    assert again.status_code == 400
    # O bien por serial ya devuelto, o porque el despacho ya está RETORNADO
    assert "devueltos" in again.json()["detail"] or "RETORNADO" in again.json()["detail"]


def test_all_returned_moves_dispatch_to_retornado(app) -> None:
    client, headers, supplier_id, cyls = _setup(app)
    d = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "cylinders": [
                {"cylinder_id": cyls[0]},
                {"cylinder_id": cyls[1]},
            ],
        },
    ).json()["id"]
    client.post(f"/api/v1/plugins/compras/purchase/dispatches/{d}/confirm", headers=headers)

    detail = client.get(
        f"/api/v1/plugins/compras/purchase/dispatches/{d}", headers=headers
    ).json()
    ret = client.post(
        f"/api/v1/plugins/compras/purchase/dispatches/{d}/return",
        headers=headers,
        json={"cylinders": [{"cylinder_id": c["cylinder_id"]} for c in detail["cylinders"]]},
    )
    assert ret.status_code == 200
    assert ret.json()["status"] == "RETORNADO"

    custody = client.get(
        f"/api/v1/plugins/compras/purchase/dispatches/suppliers/{supplier_id}/custody",
        headers=headers,
    ).json()
    assert custody == []


def test_session_link_validates_tenant_and_operational_state(app) -> None:
    client, headers, supplier_id, cyls = _setup(app)
    d = client.post(
        "/api/v1/plugins/compras/purchase/dispatches",
        headers=headers,
        json={"supplier_id": supplier_id, "cylinders": [{"cylinder_id": cyls[0]}]},
    ).json()["id"]

    # Sesión inexistente → 400
    missing = client.patch(
        f"/api/v1/plugins/compras/purchase/dispatches/{d}/session-link",
        headers=headers,
        json={"kind": "outbound", "session_id": "no-existe"},
    )
    assert missing.status_code == 400
    assert "Jornada no encontrada" in missing.json()["detail"]

    # kind inválido → 422 (pattern del schema)
    bad_kind = client.patch(
        f"/api/v1/plugins/compras/purchase/dispatches/{d}/session-link",
        headers=headers,
        json={"kind": "otro", "session_id": None},
    )
    assert bad_kind.status_code == 422

    # Desvincular (session_id null) permitido en PREPARADO
    unlink = client.patch(
        f"/api/v1/plugins/compras/purchase/dispatches/{d}/session-link",
        headers=headers,
        json={"kind": "outbound", "session_id": None},
    )
    assert unlink.status_code == 200
