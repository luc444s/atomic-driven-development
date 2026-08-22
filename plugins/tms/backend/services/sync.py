from __future__ import annotations

import json
from datetime import date, datetime

from plugins.tms.backend import ports
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.legacy.schemas import SalidaLegacy
from plugins.tms.backend.models import JornadaTMS
from plugins.tms.backend.services.drivers import normalize_driver_dni
from plugins.tms.backend.services.materialize import materialize_salida


def _estado_para(salida: SalidaLegacy) -> str:
    j = materialize_salida(salida)
    placa = j.vehiculo_placa.strip()
    chofer = normalize_driver_dni(j.chofer_dni, salida.transportista)
    return "draft" if (placa and chofer) else "pendiente"


def _materialize_load_plan(
    db,
    *,
    tenant_id: str,
    actor_user_id: str,
    session_id: str,
    warehouse_id: str,
    salida: SalidaLegacy,
) -> bool:
    p = ports.get_ports()
    items = []
    for item in salida.items:
        product_id = p.find_product_id_by_legacy(
            db, tenant_id=tenant_id, legacy_id=item.cod_producto
        )
        if product_id is None:
            continue
        quantity = item.pesito if item.pesito and float(item.pesito) > 0 else item.cantidad
        if not quantity or float(quantity) <= 0:
            continue
        items.append(
            ports.LoadPlanItemSpec(
                product_id=product_id,
                planned_quantity=float(quantity),
                source_warehouse_id=warehouse_id,
                notes=json.dumps({"seriales": list(item.seriales)}, ensure_ascii=False)
                if item.seriales
                else None,
            )
        )
    if not items:
        return False
    return p.upsert_load_plan_items(
        db,
        session_id=session_id,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        notes=f"Materializado desde salida legacy {salida.cod_movimiento}",
        items=items,
    )


def _materialize_live_session(
    db,
    *,
    tenant_id: str,
    branch_id: str | None,
    actor_user_id: str,
    salida: SalidaLegacy,
):
    p = ports.get_ports()
    placa = salida.placa.strip()
    dni = normalize_driver_dni(salida.dnichofer, salida.transportista)
    if not placa or not dni:
        return None

    fecha = salida.fecha.date()
    vehicle_id = p.ensure_vehicle(db, tenant_id=tenant_id, plate=placa, vehicle_type="CAMION")
    driver_id = p.ensure_driver(
        db,
        tenant_id=tenant_id,
        branch_id=branch_id,
        dni=dni,
        full_name=salida.transportista or f"Conductor {dni}",
    )
    warehouse_id = p.find_warehouse_id(db, tenant_id=tenant_id, code=str(salida.almacen))
    if warehouse_id is None:
        return None

    existing_id = p.find_live_session_id(
        db,
        tenant_id=tenant_id,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        fecha=fecha,
    )
    if existing_id is not None:
        _materialize_load_plan(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            session_id=existing_id,
            warehouse_id=warehouse_id,
            salida=salida,
        )
        return existing_id

    session_id = p.create_live_session(
        db,
        ports.LiveSessionSpec(
            tenant_id=tenant_id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            origin_warehouse_id=warehouse_id,
            branch_id=branch_id,
            actor_user_id=actor_user_id,
            opened_at=salida.fecha,
        ),
    )
    _materialize_load_plan(
        db,
        tenant_id=tenant_id,
        actor_user_id=actor_user_id,
        session_id=session_id,
        warehouse_id=warehouse_id,
        salida=salida,
    )
    return session_id


async def sync_salidas_hoy(
    db,
    client: LegacyApiClient,
    hoy: date | None = None,
    *,
    tenant_id: str | None = None,
    branch_id: str | None = None,
    actor_user_id: str | None = None,
) -> dict:
    hoy = hoy or date.today()
    desde = hoy.isoformat()
    hasta = datetime(hoy.year, hoy.month, hoy.day, 23, 59, 59).isoformat()

    salidas = await client.get_salidas(desde=desde, hasta=hasta, limit=500)
    clientes = {c.id: c for c in await client.get_clientes()}

    for idx, salida in enumerate(salidas):
        if salida.items:
            continue
        try:
            salidas[idx] = await client.get_salida(salida.cod_movimiento)
        except Exception:
            pass

    creadas = actualizadas = omitidas = 0
    sesiones = sesiones_omitidas = 0
    for salida in salidas:
        estado = _estado_para(salida)
        placa = salida.placa.strip()
        chofer = normalize_driver_dni(salida.dnichofer, salida.transportista)
        direccion = ""
        cli = clientes.get(salida.cod_cliente)
        if cli is not None and cli.direccion:
            direccion = cli.direccion
        items_json = json.dumps(
            [i.model_dump() for i in salida.items], ensure_ascii=False
        )

        if tenant_id is not None and actor_user_id:
            if placa and chofer:
                session_id = _materialize_live_session(
                    db,
                    tenant_id=tenant_id,
                    branch_id=branch_id,
                    actor_user_id=actor_user_id,
                    salida=salida,
                )
                if session_id is not None:
                    sesiones += 1
            else:
                sesiones_omitidas += 1

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
    res = {"creadas": creadas, "actualizadas": actualizadas, "omitidas": omitidas}
    if tenant_id is not None:
        res["sesiones_vivas"] = sesiones
        res["sesiones_omitidas"] = sesiones_omitidas
    return res
