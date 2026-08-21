from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy.orm import Session

from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.legacy.schemas import SalidaLegacy
from plugins.tms.backend.models import JornadaTMS
from plugins.tms.backend.services.materialize import materialize_salida


def _estado_para(salida: SalidaLegacy) -> str:
    j = materialize_salida(salida)
    placa = j.vehiculo_placa.strip()
    chofer = j.chofer_dni.strip()
    return "draft" if (placa and chofer) else "pendiente"


async def sync_salidas_hoy(
    db: Session,
    client: LegacyApiClient,
    hoy: date | None = None,
) -> dict:
    hoy = hoy or date.today()
    desde = hoy.isoformat()
    hasta = datetime(hoy.year, hoy.month, hoy.day, 23, 59, 59).isoformat()

    salidas = await client.get_salidas(desde=desde, hasta=hasta, limit=500)
    clientes = {c.id: c for c in await client.get_clientes()}

    creadas = actualizadas = omitidas = 0
    for salida in salidas:
        estado = _estado_para(salida)
        placa = salida.placa.strip()
        chofer = salida.dnichofer.strip()
        direccion = ""
        cli = clientes.get(salida.cod_cliente)
        if cli is not None and cli.direccion:
            direccion = cli.direccion
        items_json = json.dumps(
            [i.model_dump() for i in salida.items], ensure_ascii=False
        )

        existente = (
            db.query(JornadaTMS)
            .filter_by(cod_movimiento_legacy=salida.cod_movimiento)
            .first()
        )
        if existente is None:
            db.add(
                JornadaTMS(
                    cod_movimiento_legacy=salida.cod_movimiento,
                    fecha=salida.fecha.date(),
                    estado=estado,
                    placa=placa,
                    chofer_dni=chofer,
                    almacen=salida.almacen,
                    cod_cliente=salida.cod_cliente,
                    cliente=salida.cliente,
                    direccion_llegada=direccion,
                    tipo_transaccion=salida.tipo_transaccion,
                    observacion=salida.observacion,
                    items=items_json,
                )
            )
            creadas += 1
        elif existente.estado in ("draft", "pendiente"):
            existente.placa = placa
            existente.chofer_dni = chofer
            existente.almacen = salida.almacen
            existente.cod_cliente = salida.cod_cliente
            existente.cliente = salida.cliente
            existente.direccion_llegada = direccion
            existente.tipo_transaccion = salida.tipo_transaccion
            existente.observacion = salida.observacion
            existente.items = items_json
            if existente.estado == "pendiente" and placa and chofer:
                existente.estado = "draft"
            actualizadas += 1
        else:
            omitidas += 1

    db.flush()
    return {"creadas": creadas, "actualizadas": actualizadas, "omitidas": omitidas}
