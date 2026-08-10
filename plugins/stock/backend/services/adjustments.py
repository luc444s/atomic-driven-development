from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

FOUR_DECIMALS = Decimal("0.0001")
ZERO_QUANTITY = Decimal("0.000")


def _avg_cost(total_cost: Decimal, quantity: Decimal) -> Decimal:
    if quantity == ZERO_QUANTITY:
        return Decimal("0.0000")
    return (total_cost / quantity).quantize(FOUR_DECIMALS, rounding=ROUND_HALF_UP)


def resolve_positive_adjust_unit_cost(
    *, current_quantity: Decimal, current_total_cost: Decimal, unit_cost: float | None
) -> float:
    if unit_cost is not None:
        return unit_cost
    if current_quantity > ZERO_QUANTITY:
        return float(_avg_cost(current_total_cost, current_quantity))
    return 0.0
