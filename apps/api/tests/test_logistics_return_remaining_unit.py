from plugins.logistics.backend.services import load_plans


def test_resolve_returned_warehouse_state_keeps_loaded_route_cylinder_as_loaded() -> None:
    assert (
        load_plans._resolve_returned_warehouse_state(
            current_state="EN_RUTA",
            has_positive_load=True,
        )
        == "LLENADO_OK"
    )


def test_resolve_returned_warehouse_state_marks_empty_route_cylinder_as_empty() -> None:
    assert (
        load_plans._resolve_returned_warehouse_state(
            current_state="EN_RUTA",
            has_positive_load=False,
        )
        == "EN_ALMACEN_VACIO"
    )


def test_resolve_returned_warehouse_state_maps_customer_states_explicitly() -> None:
    assert (
        load_plans._resolve_returned_warehouse_state(
            current_state="EN_CLIENTE_LLENO",
            has_positive_load=False,
        )
        == "LLENADO_OK"
    )
    assert (
        load_plans._resolve_returned_warehouse_state(
            current_state="EN_CLIENTE_VACIO",
            has_positive_load=True,
        )
        == "EN_ALMACEN_VACIO"
    )
