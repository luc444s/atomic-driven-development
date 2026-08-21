from __future__ import annotations

import json
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session
from systutor.kernel.tenants.models import Branch, Tenant

from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.models import LogisticsVehicleSession, LogisticsWarehouse
from plugins.logistics.backend.services.sessions import create_vehicle_session
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.legacy.schemas import SalidaLegacy
from plugins.tms.backend.models import JornadaTMS
from plugins.tms.backend.services.drivers import ensure_driver_user, normalize_driver_dni
from plugins.tms.backend.services.materialize import materialize_salida
from plugins.tms.backend.services.vehicles import ensure_vehicle


def _estado_para(salida: SalidaLegacy) -> str:
    j = materialize_salida(salida)
    placa = j.vehiculo_placa.strip()
    chofer = normalize_driver_dni(j.chofer_dni, salida.transportista)
    return "draft" if (placa and chofer) else "pendiente"


def _resolve_warehouse(
    db: Session, *, tenant_id: str, almacen: int
) -> LogisticsWarehouse | None:
    return db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.tenant_id == tenant_id,
            LogisticsWarehouse.code == str(almacen),
        )
    )


def _find_live_session(
    db: Session,
    *,
    tenant_id: str,
    vehicle_id: str,
    driver_id: str,
    fecha: date,
) -> LogisticsVehicleSession | None:
    sessions = list(
        db.scalars(
            select(LogisticsVehicleSession).where(
                LogisticsVehicleSession.tenant_id == tenant_id,
                LogisticsVehicleSession.vehicle_id == vehicle_id,
                LogisticsVehicleSession.driver_id == driver_id,
                LogisticsVehicleSession.status.in_(["DRAFT", "LOADING"]),
            )
        ).all()
    )
    for s in sessions:
        if s.opened_at.date() == fecha:
            return s
    return None


def _materialize_live_session(
    db: Session,
    *,
    tenant: Tenant,
    branch: Branch | None,
    actor_user_id: str,
    salida: SalidaLegacy,
) -> LogisticsVehicleSession | None:
    placa = salida.placa.strip()
    dni = normalize_driver_dni(salida.dnichofer, salida.transportista)
    if not placa or not dni:
        return None

    fecha = salida.fecha.date()
    vehicle = ensure_vehicle(db, tenant=tenant, plate=placa, vehicle_type="CAMION")
    driver = ensure_driver_user(
        db,
        tenant=tenant,
        branch=branch,
        dni=dni,
        full_name=salida.transportista or f"Conductor {dni}",
    )
    warehouse = _resolve_warehouse(db, tenant_id=tenant.id, almacen=salida.almacen)
    if warehouse is None:
        return None

    existing = _find_live_session(
        db,
        tenant_id=tenant.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        fecha=fecha,
    )
    if existing is not None:
        return existing

    payload = type(
        "LiveSessionPayload",
        (),
        {
            "vehicle_id": vehicle.id,
            "driver_id": driver.id,
            "origin_warehouse_id": warehouse.id,
            "route_id": None,
        },
    )()
    context = LogisticsActionContext(
        tenant_id=tenant.id,
        branch_id=branch.id if branch is not None else None,
        actor_user_id=actor_user_id,
        correlation_id=None,
        request_id=None,
    )
    return create_vehicle_session(
        db,
        tenant_id=tenant.id,
        payload=payload,
        action_context=context,
        opened_at=salida.fecha,
    )


async def sync_salidas_hoy(
    db: Session,
    client: LegacyApiClient,
    hoy: date | None = None,
    *,
    tenant: Tenant | None = None,
    branch: Branch | None = None,
    actor_user_id: str | None = None,
) -> dict:
    hoy = hoy or date.today()
    desde = hoy.isoformat()
    hasta = datetime(hoy.year, hoy.month, hoy.day, 23, 59, 59).isoformat()

    salidas = await client.get_salidas(desde=desde, hasta=hasta, limit=500)
    clientes = {c.id: c for c in await client.get_clientes()}

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

        if tenant is not None and actor_user_id:
            if placa and chofer:
                session = _materialize_live_session(
                    db,
                    tenant=tenant,
                    branch=branch,
                    actor_user_id=actor_user_id,
                    salida=salida,
                )
                if session is not None:
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
    if tenant is not None:
        res["sesiones_vivas"] = sesiones
        res["sesiones_omitidas"] = sesiones_omitidas
    return res