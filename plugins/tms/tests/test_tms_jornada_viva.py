from __future__ import annotations

import asyncio
import json
from datetime import date
from typing import Any, cast

import httpx
import pytest

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
    "items": [
        {
            "cod_producto": 1868,
            "producto": "ABRAZADERAS",
            "pesito": 2,
            "cantidad": 1,
            "seriales": ["21k418065"],
        }
    ],
}

LEGACY_PRODUCT_ID = 1868

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
        if "/salidas/" in url and not url.rstrip("/").endswith("/salidas"):
            cod = int(url.rstrip("/").split("/")[-1])
            detalle = next((s for s in self._salidas if s["cod_movimiento"] == cod), None)
            if detalle is None:
                return FakeResponse(404, {"error": "not_found"})
            return FakeResponse(200, detalle)
        if "/salidas" in url:
            lista = [{k: v for k, v in s.items() if k != "items"} for s in self._salidas]
            return FakeResponse(200, lista)
        return FakeResponse(404, {"error": "not_found"})


def _make_api(monkeypatch: pytest.MonkeyPatch, salidas: list[dict], clientes: list[dict]) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", lambda **_: FakeAsyncClient(salidas, clientes))


@pytest.fixture()
def host_ctx(tms_state):
    """Semilla del contexto host falso: warehouse + producto legacy."""
    tms_state.warehouses["1"] = "wh-1"
    tms_state.products[LEGACY_PRODUCT_ID] = f"prod-{LEGACY_PRODUCT_ID}"
    return tms_state


def test_normalize_driver_dni_resuelve_prefijo_sucio() -> None:
    assert normalize_driver_dni("", "D78839842-ARANGO LLANTOY ALFONSO JORGE") == "78839842"
    assert normalize_driver_dni("4492", "D44973574-HIRVING LEON CALDERON") == "44973574"
    assert normalize_driver_dni("46209157", "AYRTOM SALDARRIAGA SALDARRIAGA") == "46209157"
    assert normalize_driver_dni("", "") == ""


def test_sync_materializa_jornada_viva(
    db_session, host_ctx, tms_state, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_api(monkeypatch, [SALIDA_LIMPIA], [CLIENTE_4587])
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    res = asyncio.run(
        sync_salidas_hoy(
            db_session,
            client,
            hoy=date(2026, 8, 20),
            tenant_id=tms_state.tenant_id,
            branch_id=tms_state.branch_id,
            actor_user_id=tms_state.actor_user_id,
        )
    )

    assert res["creadas"] == 1
    assert res["sesiones_vivas"] == 1

    assert len(tms_state.sessions) == 1
    s = tms_state.sessions[0]
    assert s["warehouse_id"] == "wh-1"

    vehicle_ids = list(tms_state.vehicles.values())
    assert len(vehicle_ids) == 1
    assert s["vehicle_id"] == vehicle_ids[0]

    dni = "78839842"
    assert dni in tms_state.drivers
    assert s["driver_id"] == tms_state.drivers[dni]
    assert driver_email(dni) == "78839842@oxipur.com"

    snapshot = db_session.query(JornadaTMS).filter_by(cod_movimiento_legacy=42470).one()
    assert snapshot.estado == "draft"
    items = json.loads(snapshot.items)
    assert items[0]["pesito"] == 2.0

    # plan de carga: un plan para la sesión con el producto correcto y seriales
    plans = tms_state.plans.get(s["id"], [])
    assert len(plans) == 1
    plan_items = plans[0]["items"]
    assert len(plan_items) == 1
    assert plan_items[0]["product_id"] == f"prod-{LEGACY_PRODUCT_ID}"
    assert float(plan_items[0]["planned_quantity"]) == 2.0
    assert json.loads(plan_items[0]["notes"]) == {"seriales": ["21k418065"]}


def test_sync_idempotente_sesion_unica(
    db_session, host_ctx, tms_state, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_api(monkeypatch, [SALIDA_LIMPIA], [CLIENTE_4587])
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    asyncio.run(
        sync_salidas_hoy(
            db_session, client, hoy=date(2026, 8, 20),
            tenant_id=tms_state.tenant_id, branch_id=tms_state.branch_id,
            actor_user_id=tms_state.actor_user_id,
        )
    )
    asyncio.run(
        sync_salidas_hoy(
            db_session, client, hoy=date(2026, 8, 20),
            tenant_id=tms_state.tenant_id, branch_id=tms_state.branch_id,
            actor_user_id=tms_state.actor_user_id,
        )
    )

    assert len(tms_state.sessions) == 1
    assert len(tms_state.vehicles) == 1
    assert db_session.query(JornadaTMS).count() == 1
    total_planes = sum(len(v) for v in tms_state.plans.values())
    assert total_planes == 2  # segundo sync re-materializa el plan sobre sesión existente


def test_sync_sin_placa_no_crea_sesion(
    db_session, host_ctx, tms_state, monkeypatch: pytest.MonkeyPatch
) -> None:
    salida = cast(dict, dict(SALIDA_LIMPIA))
    salida["placa"] = ""
    _make_api(monkeypatch, [salida], [CLIENTE_4587])
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    res = asyncio.run(
        sync_salidas_hoy(
            db_session, client, hoy=date(2026, 8, 20),
            tenant_id=tms_state.tenant_id, branch_id=tms_state.branch_id,
            actor_user_id=tms_state.actor_user_id,
        )
    )

    assert res["sesiones_vivas"] == 0
    assert len(tms_state.sessions) == 0
    assert not tms_state.plans
    snapshot = db_session.query(JornadaTMS).one()
    assert snapshot.estado == "pendiente"
