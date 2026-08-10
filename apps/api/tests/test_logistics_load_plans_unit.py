from types import SimpleNamespace
from typing import Any, cast

import pytest

from plugins.logistics.backend.services import load_plans


def test_raise_stock_error_for_load_line_reports_no_stock() -> None:
    with pytest.raises(ValueError, match="El producto Oxigeno Industrial B10 no tiene stock"):
        load_plans._raise_stock_error_for_load_line(
            product_name="Oxigeno Industrial B10",
            available_quantity=0,
            planned_quantity=2,
        )


def test_raise_stock_error_for_load_line_reports_insufficient_stock() -> None:
    with pytest.raises(ValueError, match="no tiene stock suficiente"):
        load_plans._raise_stock_error_for_load_line(
            product_name="Oxigeno Industrial B10",
            available_quantity=1,
            planned_quantity=2,
        )


def test_ensure_available_stock_for_load_line_uses_balance_available_quantity(monkeypatch) -> None:
    monkeypatch.setattr(
        load_plans,
        "get_warehouse_balances",
        lambda db, tenant_id, warehouse_id: SimpleNamespace(
            items=[SimpleNamespace(product_id="prod-1", available_quantity=3)]
        ),
    )

    load_plans._ensure_available_stock_for_load_line(
        cast(Any, None),
        tenant_id="tenant-1",
        product_id="prod-1",
        product_name="Producto prueba",
        planned_quantity=2,
        source_warehouse_id="wh-1",
    )
