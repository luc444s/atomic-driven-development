from __future__ import annotations

import asyncio
import json
from datetime import date
from typing import Any, cast

import httpx
import pytest
from sqlalchemy.orm import Session

import plugins.tms.backend.models  # noqa: F401  (registra tms_jornada en Base.metadata)
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.models import JornadaTMS
from plugins.tms.backend.services.sync import sync_salidas_hoy

SALIDA_42470 = {
    "cod_movimiento": 42470,
    "fecha": "2026-08-20T14:24:38",
    "nro_documento": "",
    "cod_cliente": 4587,
    "cliente": "M.H. EIRL",
    "almacen": 1,
    "placa": "RAM/BEI-793",
    "dnichofer": "78839842",
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
        return None

    async def get(self, url: str, headers: dict[str, str]) -> FakeResponse:
        if "/salidas" in url:
            return FakeResponse(200, self._salidas)
        if "/clientes" in url:
            return FakeResponse(200, self._clientes)
        return FakeResponse(404, {"error": "not_found"})


def _make_api(monkeypatch: pytest.MonkeyPatch, salidas: list[dict], clientes: list[dict]) -> None:
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: FakeAsyncClient(salidas, clientes)
    )


def test_materializa_ultima_salida_via_api_a_draft(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_api(monkeypatch, [SALIDA_42470], [CLIENTE_4587])
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    res = asyncio.run(sync_salidas_hoy(db_session, client, hoy=date(2026, 8, 20)))

    assert res == {"creadas": 1, "actualizadas": 0, "omitidas": 0}
    jornadas = db_session.query(JornadaTMS).all()
    assert len(jornadas) == 1
    j = jornadas[0]
    assert j.estado == "draft"
    assert j.placa == "RAM/BEI-793"
    assert j.chofer_dni == "78839842"
    assert j.cod_cliente == 4587
    assert j.tipo_transaccion == "CONTADO"
    assert j.direccion_llegada == "AV. FEDERICO VILLARREAL 551"
    items = json.loads(j.items)
    assert items[0]["pesito"] == 2.0


def test_sync_idempotente_no_duplica(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    _make_api(monkeypatch, [SALIDA_42470], [CLIENTE_4587])
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    asyncio.run(sync_salidas_hoy(db_session, client, hoy=date(2026, 8, 20)))
    asyncio.run(sync_salidas_hoy(db_session, client, hoy=date(2026, 8, 20)))

    assert db_session.query(JornadaTMS).count() == 1


def test_salida_sin_placa_queda_pendiente(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    salida = cast(dict, dict(SALIDA_42470))
    salida["placa"] = ""
    salida["dnichofer"] = ""
    _make_api(monkeypatch, [salida], [CLIENTE_4587])
    client = LegacyApiClient("http://legacy.test/api", "tok", timeout_seconds=5)

    asyncio.run(sync_salidas_hoy(db_session, client, hoy=date(2026, 8, 20)))

    j = db_session.query(JornadaTMS).one()
    assert j.estado == "pendiente"
