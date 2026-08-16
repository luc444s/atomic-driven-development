from __future__ import annotations

from typing import Any

import httpx


class DuplicateReceiptError(Exception):
    pass


class StockConnector:
    def __init__(self, base_url: str, internal_token: str) -> None:
        self._base = base_url.rstrip("/")
        self._token = internal_token

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self._base}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=10,
        )
        if response.status_code == 409:
            raise DuplicateReceiptError(
                f"Duplicate idempotency key: {payload.get('idempotency_key', '?')}"
            )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]

    def purchase_in(
        self,
        *,
        product_id: str,
        warehouse_id: str,
        quantity: float,
        unit_cost: float,
        reference_type: str,
        reference_id: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        return self._post(
            "/purchase-in",
            {
                "product_id": product_id,
                "warehouse_id": warehouse_id,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "idempotency_key": idempotency_key,
            },
        )
