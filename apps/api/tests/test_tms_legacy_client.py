from __future__ import annotations

import asyncio
import json
from typing import Any, cast

import httpx
import pytest

from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.legacy.schemas import (
    EgresoRequest,
    LegacyAuthError,
    LegacyBadResponseError,
    LegacyTimeoutError,
)


class FakeResponse:
    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Any:
        return self._payload


class FakeAsyncClient:
    def __init__(self, response: object) -> None:
        self._response = response
        self.last_headers: dict[str, str] | None = None

    async def __aenter__(self) -> FakeAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str]) -> FakeResponse:
        self.last_headers = headers
        if isinstance(self._response, Exception):
            raise self._response
        return cast(FakeResponse, self._response)

    async def post(self, url: str, json: Any, headers: dict[str, str]) -> FakeResponse:
        self.last_headers = headers
        if isinstance(self._response, Exception):
            raise self._response
        return cast(FakeResponse, self._response)


@pytest.fixture()
def client() -> LegacyApiClient:
    return LegacyApiClient("http://legacy.test/api", "tok123", timeout_seconds=1.0, max_retries=1)


def _monkeypatch_client(monkeypatch: pytest.MonkeyPatch, fake: FakeAsyncClient) -> None:
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)


def test_get_clientes_happy_path(client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {
            "id": 7,
            "dni": "00000000",
            "ruc": "",
            "nombre": "VARIOS",
            "direccion": "",
            "telefono": "",
            "email": "",
        },
        {
            "id": 10,
            "dni": "",
            "ruc": "20123456789",
            "nombre": "EMPRESA SAC",
            "direccion": "Av. Siempre Viva",
            "telefono": "044123456",
            "email": "a@b.com",
        },
    ]
    fake = FakeAsyncClient(FakeResponse(200, payload))
    _monkeypatch_client(monkeypatch, fake)

    result = asyncio.run(client.get_clientes())

    assert len(result) == 2
    assert result[0].nombre == "VARIOS"
    assert result[1].ruc == "20123456789"
    assert fake.last_headers == {"Authorization": "Bearer tok123"}


def test_get_clientes_vacio(client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeAsyncClient(FakeResponse(200, []))
    _monkeypatch_client(monkeypatch, fake)

    result = asyncio.run(client.get_clientes())

    assert result == []


def test_401_lanza_error_controlado(
    client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = FakeAsyncClient(FakeResponse(401, {"error": "unauthorized"}))
    _monkeypatch_client(monkeypatch, fake)

    with pytest.raises(LegacyAuthError):
        asyncio.run(client.get_clientes())


def test_404_lanza_bad_response(client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeAsyncClient(FakeResponse(404, {"error": "not_found"}))
    _monkeypatch_client(monkeypatch, fake)

    with pytest.raises(LegacyBadResponseError):
        asyncio.run(client.get_puntos(999999))


def test_timeout_reintenta_y_erra(client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeAsyncClient(httpx.TimeoutException("timeout"))
    _monkeypatch_client(monkeypatch, fake)

    with pytest.raises(LegacyTimeoutError):
        asyncio.run(client.get_stock())


def test_registrar_egreso_envia_payload(
    client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent: list[dict[str, Any]] = []

    class CapturingClient(FakeAsyncClient):
        async def post(self, url: str, json: Any, headers: dict[str, str]) -> FakeResponse:
            sent.append(json)
            self.last_headers = headers
            return FakeResponse(201, {"status": "created", "cod_movimiento": 42})

    fake = CapturingClient(FakeResponse(201, {}))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: fake)

    result = asyncio.run(
        client.registrar_egreso(
            EgresoRequest(cod_producto=1868, almacen=1, cantidad=5, idempotency_key="K1")
        )
    )

    assert result.status == "created"
    assert result.cod_movimiento == 42
    assert sent[0] == {"cod_producto": 1868, "almacen": 1, "cantidad": 5.0, "idempotency_key": "K1"}


def test_json_invalido_controla_error(
    client: LegacyApiClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ExplodingJson:
        status_code: int = 200

        def json(self) -> Any:
            raise json.JSONDecodeError("bad", "x", 0)

    fake: Any = FakeAsyncClient(ExplodingJson())
    _monkeypatch_client(monkeypatch, fake)

    with pytest.raises(ValueError):
        asyncio.run(client.get_productos())
