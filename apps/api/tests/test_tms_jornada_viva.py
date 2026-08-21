from __future__ import annotations

import asyncio
import json
from datetime import date
from typing import Any, cast

import httpx
import pytest
from sqlalchemy.orm import Session
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.models import Branch, Tenant

import plugins.tms.backend.models  # noqa: F401  (registra tms_jornada en Base.metadata)
from plugins.logistics.backend.models import (
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.models import JornadaTMS
from plugins.tms.backend.services.drivers import driver_email, normalize_driver_dni
from plugins.tms.backend.services.sync import sync_salidas_hoy

SALIDA_LIMPIA = {
    "cod_movimiento": 42470,
    "fecha": "2026-08-20T14:24:38",
    "nro_documento": "",
    "cod_cliente": 4587,
    "cliente": "M.H. EIRL",
    "almacen": 1,
    "placa": "RAM/BEI-793",
    "dnichofer": "",
    "nro_guia": "Orden Salida 001-102024",
    "transportista": "D78839842-ARANGO LLANTOY ALFONSO JORGE",
    "lugar_inicio": "",
    "lugar_destino": "CAL. LAS ESMERALDAS NRO. 243 URB. LA RINCONADA",
    "dir_inicio": "",
    "dir_destino": "CAL. LAS ESMERALDAS NRO. 243 URB. LA RINCONADA",
    "empresa_trans": "OXIGENO NARVA E.I.R.L.",
    "ruc_empresa": "20480944063",
    "observacion": "",
    "total": 0,
    "tipo_transaccion": "CONTADO",
    "items": [{"cod_producto": 0, "producto": "", "pesito": 2, "cantidad": 0}],
}

CLIENTE_4587 = {
    "id": 4587,
    "dni": "",
    "ruc": "",
    "nombre": "M.H. EIRL",
    "direccion": "AV. FEDERICO VILLARREAL 551",
    "telefono": "",
    "email": "",
}


class FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeAsyncClient:
    def __init__(self, salidas: list[dict], clientes: list[dict]) -> None:
        self._salidas = salidas
        self._clientes = clientes

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        pass

    async def get(self, url: str, headers: dict[str, str] | None = None) -> FakeResponse:
        if url.rstrip("/").endswith("/clientes") or "/clientes?" in url:
            return FakeResponse(200, self._clientes)
        if "/salidas" in url:
            return FakeResponse(200, self._salidas)
        return FakeResponse(404, {"error": "not_found"})


def _make_api(monkeypatch: pytest.MonkeyPatch, salidas: list[dict], clientes: list[dict]) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_: FakeAsyncClient(salidas, clientes))


def _seed_context(db_session: Session) -> tuple[Tenant, Branch, User]:
    from apps.api.app.commands.seed_demo import (
        _get_or_create_admin_user,
        _get_or_create_branch,
        _get_or_create_tenant,
    )

    settings = type("S", (), {})()
    settings.seed_admin_email = "admin@example.com"
    settings.seed_admin_full_name = "System Admin"
    settings.seed_admin_password = "adminpass"
    settings.seed_demo_tenant_slug = "demo"
    settings.seed_demo_tenant_name = "Demo"
    settings.seed_demo_branch_code = "MAIN"
    settings.seed_demo_branch_name = "Sucursal Principal"

    tenant = _get_or_create_tenant(db_session, settings)
    branch = _get_or_create_branch(db_session, tenant, settings)
    user = _get_or_create_admin_user(db_session, tenant, branch, settings)
    return tenant, branch, user


def _seed_warehouse(db_session: Session, tenant_id: str) -> None:
    existing = db_session.query(LogisticsWarehouse).filter_by(
        tenant_id=tenant_id, code="1"
    ).scalar()
    if existing is not None:
        return
    db_session.add(
        LogisticsWarehouse(
            tenant_id=tenant_id,
            name="OXIPUR",
            code="1",
            warehouse_type="FIXED",
            is_active=True,
        )
    )
    db_session.flush()


def test_normalize_driver_dni_resuelve_prefijo_sucio() -> None:
    assert normalize_driver_dni("", "D78839842-ARANGO LLANTOY ALFONSO JORGE") == "78839842"
    assert normalize_driver_dni("4492", "D44973574-HIRVING LEON CALDERON") == "44973574"
    assert normalize_driver_dni("46209157", "AYRTOM SALDARRIAGA SALDARRIAGA") == "46209157"
    assert normalize_driver_dni("", "") == ""


def test_sync_materializa_jornada_viva(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_api(monkeypatch, [SALIDA_LIMPIA], [CLIENTE_4587])
    tenant, branch, user = _seed_context(db_session)
    _seed_warehouse(db_session, tenant.id)
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    res = asyncio.run(
        sync_salidas_hoy(
            db_session,
            client,
            hoy=date(2026, 8, 20),
            tenant=tenant,
            branch=branch,
            actor_user_id=user.id,
        )
    )

    assert res["creadas"] == 1
    assert res["sesiones_vivas"] == 1

    sessions = db_session.query(LogisticsVehicleSession).all()
    assert len(sessions) == 1
    s = sessions[0]
    assert s.status == "DRAFT"
    assert s.origin_warehouse_id is not None

    vehicle = db_session.query(LogisticsVehicle).filter_by(tenant_id=tenant.id).all()
    assert any(v.plate == "RAM/BEI-793" for v in vehicle)

    driver = db_session.query(User).filter_by(email=driver_email("78839842")).one_or_none()
    assert driver is not None
    assert driver.category == "driver"

    snapshot = db_session.query(JornadaTMS).filter_by(cod_movimiento_legacy=42470).one()
    assert snapshot.estado == "draft"
    items = json.loads(snapshot.items)
    assert items[0]["pesito"] == 2.0


def test_sync_idempotente_sesion_unica(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_api(monkeypatch, [SALIDA_LIMPIA], [CLIENTE_4587])
    tenant, branch, user = _seed_context(db_session)
    _seed_warehouse(db_session, tenant.id)
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    asyncio.run(
        sync_salidas_hoy(
            db_session, client, hoy=date(2026, 8, 20),
            tenant=tenant, branch=branch, actor_user_id=user.id,
        )
    )
    asyncio.run(
        sync_salidas_hoy(
            db_session, client, hoy=date(2026, 8, 20),
            tenant=tenant, branch=branch, actor_user_id=user.id,
        )
    )

    assert db_session.query(LogisticsVehicleSession).count() == 1
    assert db_session.query(LogisticsVehicle).filter_by(tenant_id=tenant.id).count() == 1
    assert db_session.query(JornadaTMS).count() == 1


def test_sync_sin_placa_no_crea_sesion(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    salida = cast(dict, dict(SALIDA_LIMPIA))
    salida["placa"] = ""
    _make_api(monkeypatch, [salida], [CLIENTE_4587])
    tenant, branch, user = _seed_context(db_session)
    _seed_warehouse(db_session, tenant.id)
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    res = asyncio.run(
        sync_salidas_hoy(
            db_session, client, hoy=date(2026, 8, 20),
            tenant=tenant, branch=branch, actor_user_id=user.id,
        )
    )

    assert res["sesiones_vivas"] == 0
    assert db_session.query(LogisticsVehicleSession).count() == 0
    snapshot = db_session.query(JornadaTMS).one()
    assert snapshot.estado == "pendiente"