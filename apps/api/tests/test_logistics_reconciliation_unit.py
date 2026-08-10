from plugins.logistics.backend.dto.reconciliation import ReconciliationLineRead
from plugins.logistics.backend.services.reconciliation import (
    _merge_expected_lines_with_physical_counts,
)


def test_merge_expected_lines_with_physical_counts_does_not_double_count_existing_product() -> None:
    merged = _merge_expected_lines_with_physical_counts(
        expected_lines=[
            ReconciliationLineRead(
                product_id="prod-1",
                product_name="Oxigeno Industrial B10",
                expected_quantity=7,
            )
        ],
        physical_counts={"prod-1": 7},
        product_name_resolver=lambda pid: pid,
    )

    assert len(merged) == 1
    assert merged[0].expected_quantity == 7


def test_merge_expected_lines_with_physical_counts_adds_missing_product() -> None:
    merged = _merge_expected_lines_with_physical_counts(
        expected_lines=[
            ReconciliationLineRead(
                product_id="prod-1",
                product_name="Oxigeno Industrial B10",
                expected_quantity=7,
            )
        ],
        physical_counts={"prod-2": 2},
        product_name_resolver=lambda pid: f"Producto {pid}",
    )

    assert len(merged) == 2
    assert merged[1].product_id == "prod-2"
    assert merged[1].expected_quantity == 2
