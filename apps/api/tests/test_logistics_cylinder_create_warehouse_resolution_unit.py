from plugins.logistics.backend.routers.cylinders import _requires_creation_warehouse
from plugins.logistics.backend.schemas import CylinderCreateFields


def test_requires_creation_warehouse_for_cryogenic_tank_without_entry_mode() -> None:
    payload = CylinderCreateFields(container_type="CRYOGENIC_TANK")

    assert _requires_creation_warehouse(payload) is True


def test_requires_creation_warehouse_for_operational_entry_mode() -> None:
    payload = CylinderCreateFields(entry_mode="EMPTY_FROM_WAREHOUSE")

    assert _requires_creation_warehouse(payload) is True


def test_does_not_require_creation_warehouse_for_plain_manual_cylinder() -> None:
    payload = CylinderCreateFields()

    assert _requires_creation_warehouse(payload) is False
