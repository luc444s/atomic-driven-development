from types import SimpleNamespace

from plugins.logistics.backend.services import state_machine


def test_has_valid_adr_accepts_cargo_description_when_label_missing(monkeypatch) -> None:
    monkeypatch.setattr(
        state_machine,
        "resolve_product_adr",
        lambda db, product_id: SimpleNamespace(
            category="3",
            un_number="1072",
            label=None,
            cargo_description="UN 1072 OXIGENO COMPRIMIDO",
        ),
    )
    cylinder = SimpleNamespace(product_id="prod-1", gas_group_id=None)

    assert state_machine.has_valid_adr(None, cylinder) is True


def test_has_valid_adr_rejects_missing_label_and_description(monkeypatch) -> None:
    monkeypatch.setattr(
        state_machine,
        "resolve_product_adr",
        lambda db, product_id: SimpleNamespace(
            category="3",
            un_number="1072",
            label=None,
            cargo_description=None,
        ),
    )
    cylinder = SimpleNamespace(product_id="prod-1", gas_group_id=None)

    assert state_machine.has_valid_adr(None, cylinder) is False
