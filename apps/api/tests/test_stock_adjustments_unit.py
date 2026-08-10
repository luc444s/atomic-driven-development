from decimal import Decimal

from plugins.stock.backend.services.adjustments import resolve_positive_adjust_unit_cost


def test_resolve_positive_adjust_unit_cost_prefers_explicit_unit_cost() -> None:
    resolved = resolve_positive_adjust_unit_cost(
        current_quantity=Decimal("5.000"),
        current_total_cost=Decimal("37.5000"),
        unit_cost=9.25,
    )

    assert resolved == 9.25


def test_resolve_positive_adjust_unit_cost_uses_current_average_when_balance_exists() -> None:
    resolved = resolve_positive_adjust_unit_cost(
        current_quantity=Decimal("2.000"),
        current_total_cost=Decimal("15.0000"),
        unit_cost=None,
    )

    assert resolved == 7.5


def test_resolve_positive_adjust_unit_cost_returns_zero_for_zero_balance_without_cost() -> None:
    resolved = resolve_positive_adjust_unit_cost(
        current_quantity=Decimal("0.000"),
        current_total_cost=Decimal("0.0000"),
        unit_cost=None,
    )

    assert resolved == 0.0
