from plugins.logistics.backend.services.contracts import (
    build_contract_series,
    format_contract_number,
)


def test_build_contract_series_keeps_alphanumeric_warehouse_code() -> None:
    assert build_contract_series("CT", "4VL", 2026) == "CT4VL26"


def test_build_contract_series_normalizes_spacing_and_case() -> None:
    assert build_contract_series("CT", " ul-7 ", 2026) == "CTUL726"


def test_format_contract_number_pads_sequence() -> None:
    assert format_contract_number("CT4VL26", 4) == "CT4VL26-000004"
