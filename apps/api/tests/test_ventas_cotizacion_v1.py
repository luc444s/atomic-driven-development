# ruff: noqa: S101
from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.app.api.v1.core.common import CoreActionContext
from apps.api.app.api.v1.core.services.plugins import set_core_plugin_enabled
from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.lifecycle import bootstrap_app_state
from apps.api.app.kernel.plugins.persistent import sync_plugin_registry_state
from apps.api.tests.test_logistics_plugin import auth_headers, enable_crm_plugin
from apps.api.tests.test_productos_plugin import enable_productos_plugin
from plugins.ventas.cotizacion.backend.models import QuoteDraft, QuoteItem


def enable_ventas_plugin(app, seeded_demo: dict[str, str]) -> None:
    enable_crm_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        set_core_plugin_enabled(
            db,
            registry=app.state.plugin_registry,
            plugin_id="ventas",
            context_builder=app.state.plugin_runtime.context_builder,
            is_enabled=True,
            action_context=CoreActionContext(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                actor_user_id=seeded_demo["user_id"],
                correlation_id="test-ventas-enable",
                request_id="test-ventas-enable",
            ),
        )
        db.commit()

    bootstrap_app_state(app, app.state.settings)

    with app.state.session_factory() as db:
        seed_demo_data(db, app.state.settings, app.state.plugin_runtime.list_results())
        db.commit()


def _create_draft(
    db_session: Session,
    tenant_id: str,
    *,
    status: str = "DRAFT",
    delivery_date_val: date | None = None,
) -> QuoteDraft:
    draft = QuoteDraft(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        customer_id=str(uuid.uuid4()),
        customer_name="Juan Pérez",
        status=status,
        delivery_date=delivery_date_val or date.today(),
        created_by=str(uuid.uuid4()),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    item = QuoteItem(
        id=str(uuid.uuid4()),
        quote_draft_id=draft.id,
        product_id=str(uuid.uuid4()),
        product_name="Cilindro 10kg",
        quantity=400,
        created_at=datetime.now(UTC),
    )
    db_session.add(draft)
    db_session.add(item)
    db_session.commit()
    return draft


# ── list with filters ────────────────────────────────────────────────


def test_list_cotizaciones_sin_filtros_retorna_todas(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    _create_draft(db_session, seeded_demo["tenant_id"])
    _create_draft(db_session, seeded_demo["tenant_id"], status="CONFIRMED")

    response = client.get("/api/v1/plugins/ventas/cotizaciones", headers=headers)
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 2


def test_list_cotizaciones_filtra_por_status(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    _create_draft(db_session, seeded_demo["tenant_id"], status="DRAFT")
    _create_draft(db_session, seeded_demo["tenant_id"], status="CONFIRMED")

    response = client.get(
        "/api/v1/plugins/ventas/cotizaciones?status=DRAFT",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "DRAFT"


def test_list_cotizaciones_filtra_por_rango_fechas(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    _create_draft(db_session, seeded_demo["tenant_id"], delivery_date_val=date(2026, 7, 20))
    _create_draft(db_session, seeded_demo["tenant_id"], delivery_date_val=date(2026, 7, 25))
    _create_draft(db_session, seeded_demo["tenant_id"], delivery_date_val=date(2026, 7, 30))

    response = client.get(
        "/api/v1/plugins/ventas/cotizaciones?date_from=2026-07-22&date_to=2026-07-28",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["delivery_date"] == "2026-07-25"


def test_list_cotizaciones_filtra_por_status_y_fecha(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    _create_draft(db_session, seeded_demo["tenant_id"], status="DRAFT", delivery_date_val=date(2026, 7, 25))
    _create_draft(db_session, seeded_demo["tenant_id"], status="CONFIRMED", delivery_date_val=date(2026, 7, 25))

    response = client.get(
        "/api/v1/plugins/ventas/cotizaciones?status=DRAFT&date_from=2026-07-01&date_to=2026-07-31",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "DRAFT"


# ── patch status ─────────────────────────────────────────────────────


def test_patch_status_draft_a_confirmed(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    draft = _create_draft(db_session, seeded_demo["tenant_id"], status="DRAFT")

    response = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{draft.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "CONFIRMED"
    assert payload["customer"]["name"] == "Juan Pérez"
    assert payload["items"][0]["product_name"] == "Cilindro 10kg"
    assert payload["items"][0]["quantity"] == 400


def test_patch_status_confirmed_a_converted(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    draft = _create_draft(db_session, seeded_demo["tenant_id"], status="CONFIRMED")

    response = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{draft.id}/status",
        json={"status": "CONVERTED"},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "CONVERTED"


def test_patch_status_rechaza_confirmar_dos_veces(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    draft = _create_draft(db_session, seeded_demo["tenant_id"], status="DRAFT")

    r1 = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{draft.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert r1.status_code == 200, r1.text

    r2 = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{draft.id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert r2.status_code == 409, r2.text


def test_patch_status_rechaza_convertir_sin_confirmar(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    draft = _create_draft(db_session, seeded_demo["tenant_id"], status="DRAFT")

    response = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{draft.id}/status",
        json={"status": "CONVERTED"},
        headers=headers,
    )
    assert response.status_code == 409, response.text


def test_patch_status_404_si_no_existe(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    headers = auth_headers(client)

    fake_id = str(uuid.uuid4())
    response = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{fake_id}/status",
        json={"status": "CONFIRMED"},
        headers=headers,
    )
    assert response.status_code == 404, response.text


def test_patch_status_sin_auth_retorna_401(
    client: TestClient, app, db_session: Session, seeded_demo: dict[str, str]
) -> None:
    enable_ventas_plugin(app, seeded_demo)
    draft = _create_draft(db_session, seeded_demo["tenant_id"], status="DRAFT")

    response = client.patch(
        f"/api/v1/plugins/ventas/cotizaciones/{draft.id}/status",
        json={"status": "CONFIRMED"},
    )
    assert response.status_code in (401, 403), response.text
