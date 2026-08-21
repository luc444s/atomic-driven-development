from __future__ import annotations

from plugins.tms.backend.legacy.schemas import SalidaItemLegacy, SalidaLegacy
from plugins.tms.backend.services.materialize import JornadaMaterializada, materialize_salida


def _salida_ejemplo() -> SalidaLegacy:
    return SalidaLegacy(
        cod_movimiento=42468,
        fecha="2026-08-20T08:45:42",
        nro_documento="",
        cod_cliente=4,
        cliente="Movimiento x Inventariado",
        almacen=1,
        placa="ABC123",
        dnichofer="12345678",
        observacion="OSS:OSS-TEST",
        total=0,
        items=[SalidaItemLegacy(cod_producto=1868, producto="ABRAZADERAS", pesito=5, cantidad=0)],
    )


def test_materialize_salida_crea_jornada_con_operacion() -> None:
    salida = _salida_ejemplo()

    jornada = materialize_salida(salida)

    assert isinstance(jornada, JornadaMaterializada)
    assert jornada.vehiculo_placa == "ABC123"
    assert jornada.chofer_dni == "12345678"
    assert jornada.fecha.isoformat() == "2026-08-20"
    assert jornada.jornada_key == "ABC123|12345678|2026-08-20"
    assert len(jornada.operaciones) == 1
    op = jornada.operaciones[0]
    assert op["tipo"] == "CUSTOMER_DELIVERY"
    assert op["cod_movimiento_legacy"] == 42468
    assert op["items"][0]["producto"] == "ABRAZADERAS"
    assert op["items"][0]["pesito"] == 5.0


def test_materialize_salida_sin_placa_usa_vacio() -> None:
    salida = _salida_ejemplo()
    salida.placa = "  "

    jornada = materialize_salida(salida)

    assert jornada.vehiculo_placa == ""
    assert jornada.jornada_key == "|12345678|2026-08-20"
