from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from plugins.tms.backend.legacy.schemas import SalidaLegacy


@dataclass
class JornadaMaterializada:
    vehiculo_placa: str
    chofer_dni: str
    fecha: date
    operaciones: list[dict] = field(default_factory=list)

    @property
    def jornada_key(self) -> str:
        return f"{self.vehiculo_placa}|{self.chofer_dni}|{self.fecha.isoformat()}"


def materialize_salida(salida: SalidaLegacy) -> JornadaMaterializada:
    jornada = JornadaMaterializada(
        vehiculo_placa=salida.placa.strip(),
        chofer_dni=salida.dnichofer.strip(),
        fecha=salida.fecha.date(),
    )
    jornada.operaciones.append(
        {
            "tipo": "CUSTOMER_DELIVERY",
            "cod_movimiento_legacy": salida.cod_movimiento,
            "cliente": salida.cliente,
            "cod_cliente": salida.cod_cliente,
            "almacen": salida.almacen,
            "nro_guia": salida.nro_guia,
            "transportista": salida.transportista,
            "lugar_inicio": salida.lugar_inicio or salida.dir_inicio,
            "lugar_destino": salida.lugar_destino or salida.dir_destino,
            "items": [
                {
                    "cod_producto": item.cod_producto,
                    "producto": item.producto,
                    "pesito": item.pesito,
                    "cantidad": item.cantidad,
                    "seriales": list(item.seriales),
                }
                for item in salida.items
            ],
            "observacion": salida.observacion,
            "total": salida.total,
        }
    )
    return jornada
