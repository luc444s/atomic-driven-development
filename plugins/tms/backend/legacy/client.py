from __future__ import annotations

from typing import Any

import httpx

from plugins.tms.backend.legacy.schemas import (
    AlmacenLegacy,
    ClienteLegacy,
    EgresoRequest,
    LegacyAuthError,
    LegacyBadResponseError,
    LegacyTimeoutError,
    MovimientoLegacyResult,
    ProductoDetalleLegacy,
    ProductoLegacy,
    PuntoLegacy,
    SalidaLegacy,
    StockLegacy,
)


class LegacyApiClient:
    def __init__(
        self,
        base_url: str,
        token: str,
        *,
        timeout_seconds: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_seconds
        self._max_retries = max_retries

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}"}

    async def _get_json(self, path: str) -> Any:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.get(url, headers=self._headers())
                if response.status_code == 401:
                    raise LegacyAuthError("Token legacy invalido (401)", status_code=401)
                if response.status_code >= 400:
                    raise LegacyBadResponseError(
                        f"API legacy respondio {response.status_code} en {path}",
                        status_code=response.status_code,
                    )
                return response.json()
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise LegacyTimeoutError(
                        f"Timeout/fallo de conexion al API legacy en {path}: {exc}"
                    ) from exc
        raise LegacyTimeoutError(f"No se pudo conectar al API legacy: {last_error}")

    async def _post_json(self, path: str, payload: dict[str, Any]) -> Any:
        url = f"{self._base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
            if response.status_code == 401:
                raise LegacyAuthError("Token legacy invalido (401)", status_code=401)
            if response.status_code >= 400:
                raise LegacyBadResponseError(
                    f"API legacy respondio {response.status_code} en {path}",
                    status_code=response.status_code,
                )
            return response.json()
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            raise LegacyTimeoutError(
                f"Timeout/fallo de conexion al API legacy en {path}: {exc}"
            ) from exc

    async def get_clientes(self) -> list[ClienteLegacy]:
        data = await self._get_json("/clientes")
        return [ClienteLegacy.model_validate(item) for item in data]

    async def get_puntos(self, cliente_id: int) -> list[PuntoLegacy]:
        data = await self._get_json(f"/clientes/{cliente_id}/puntos")
        return [PuntoLegacy.model_validate(item) for item in data]

    async def get_productos(self) -> list[ProductoLegacy]:
        data = await self._get_json("/productos")
        return [ProductoLegacy.model_validate(item) for item in data]

    async def get_producto(self, producto_id: int) -> ProductoDetalleLegacy:
        data = await self._get_json(f"/productos/{producto_id}")
        return ProductoDetalleLegacy.model_validate(data)

    async def get_stock(self, cod_producto: int | None = None) -> list[StockLegacy]:
        path = "/stock" if cod_producto is None else f"/stock?cod_producto={cod_producto}"
        data = await self._get_json(path)
        return [StockLegacy.model_validate(item) for item in data]

    async def get_almacenes(self) -> list[AlmacenLegacy]:
        data = await self._get_json("/almacenes")
        return [AlmacenLegacy.model_validate(item) for item in data]

    async def registrar_egreso(self, request: EgresoRequest) -> MovimientoLegacyResult:
        data = await self._post_json("/stock/movement", request.model_dump())
        return MovimientoLegacyResult.model_validate(data)

    async def get_salidas(
        self,
        *,
        limit: int = 100,
        desde: str | None = None,
        hasta: str | None = None,
        cliente: int | None = None,
        almacen: int | None = None,
    ) -> list[SalidaLegacy]:
        params: list[str] = [f"limit={limit}"]
        if desde is not None:
            params.append(f"desde={desde}")
        if hasta is not None:
            params.append(f"hasta={hasta}")
        if cliente is not None:
            params.append(f"cliente={cliente}")
        if almacen is not None:
            params.append(f"almacen={almacen}")
        path = f"/salidas?{'&'.join(params)}"
        data = await self._get_json(path)
        return [SalidaLegacy.model_validate(item) for item in data]

    async def get_salida(self, cod_movimiento: int) -> SalidaLegacy:
        data = await self._get_json(f"/salidas/{cod_movimiento}")
        return SalidaLegacy.model_validate(data)


__all__ = ["LegacyApiClient"]
