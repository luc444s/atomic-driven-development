# ruff: noqa: E501
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.models import (
    LogisticsAgendaTaskType,
    LogisticsBrand,
    LogisticsCylinderCondition,
    LogisticsCylinderState,
    LogisticsDeliveryPoint,
    LogisticsGasProduct,
    LogisticsMovementType,
    LogisticsServiceType,
    LogisticsStateTransition,
    LogisticsVehicle,
    LogisticsWarehouse,
    LogisticsZone,
)

STATE_DEFINITIONS: tuple[tuple[str, bool, str], ...] = (
    ("CREADO_VACIO", False, "Cilindro nuevo registrado"),
    ("EN_ALMACEN_VACIO", False, "Disponible en almacen, vacio"),
    ("EN_LLENADO", False, "En proceso de llenado"),
    ("LLENADO_OK", False, "Listo para despacho"),
    ("CARGA_EN_VEHICULO", False, "Asignado y cargado a vehiculo"),
    ("EN_RUTA", False, "En traslado hacia cliente o destino"),
    ("EN_CLIENTE_LLENO", False, "En posesion del cliente, lleno"),
    ("EN_CLIENTE_VACIO", False, "En posesion del cliente, vacio"),
    ("VACIO_EN_ALMACEN", False, "Devuelto a almacen pendiente de formalizacion"),
    ("DESCARGADO_POR_RECEPCIONAR", False, "Descargado pendiente de recepcion"),
    ("RECEPCIONADO", False, "Recepcionado conforme"),
    ("EN_MANTENIMIENTO", False, "En mantenimiento"),
    ("PARA_REPARACION", False, "Pendiente de reparacion"),
    ("PARA_TRASLADO", False, "Pendiente de traslado"),
    ("BLOQUEADO", True, "Bloqueado administrativamente"),
    ("OBSERVADO", True, "Observado, requiere revision"),
    ("DE_BAJA", True, "Baja definitiva"),
    ("PERDIDO", True, "Perdido"),
)

TRANSITION_DEFINITIONS: tuple[tuple[str, str, bool, bool, str], ...] = (
    ("CREADO_VACIO", "EN_ALMACEN_VACIO", False, False, "Alta inicial"),
    ("EN_ALMACEN_VACIO", "LLENADO_OK", True, True, "Llenado completado"),
    ("EN_ALMACEN_VACIO", "EN_MANTENIMIENTO", False, False, "Envio a mantenimiento"),
    ("EN_ALMACEN_VACIO", "PARA_REPARACION", False, False, "Marcado para reparacion"),
    ("EN_ALMACEN_VACIO", "DE_BAJA", False, False, "Baja definitiva"),
    ("EN_ALMACEN_VACIO", "PERDIDO", False, False, "Perdida reportada"),
    ("EN_ALMACEN_VACIO", "PARA_TRASLADO", False, False, "Asignado a traslado"),
    ("EN_ALMACEN_VACIO", "EN_LLENADO", False, False, "Ingreso a llenado"),
    ("EN_LLENADO", "LLENADO_OK", False, False, "Llenado validado"),
    ("LLENADO_OK", "CARGA_EN_VEHICULO", False, False, "Carga en vehiculo"),
    ("LLENADO_OK", "EN_CLIENTE_LLENO", False, False, "Despacho directo"),
    ("CARGA_EN_VEHICULO", "EN_RUTA", False, False, "Salida de ruta"),
    ("EN_RUTA", "EN_CLIENTE_LLENO", False, False, "Entrega completa"),
    ("EN_RUTA", "DESCARGADO_POR_RECEPCIONAR", False, False, "Descargado en destino"),
    ("DESCARGADO_POR_RECEPCIONAR", "RECEPCIONADO", False, False, "Recepcion conforme"),
    ("RECEPCIONADO", "EN_ALMACEN_VACIO", False, False, "Ingreso formal a almacen"),
    ("EN_CLIENTE_LLENO", "EN_CLIENTE_VACIO", False, False, "Consumo por cliente"),
    ("EN_CLIENTE_LLENO", "VACIO_EN_ALMACEN", False, False, "Devolucion directa"),
    ("EN_CLIENTE_LLENO", "EN_RUTA", False, False, "Recojo programado"),
    ("EN_CLIENTE_VACIO", "EN_RUTA", False, False, "Recojo desde cliente"),
    ("EN_CLIENTE_VACIO", "EN_ALMACEN_VACIO", False, False, "Recepcion directa en almacen"),
    ("EN_CLIENTE_VACIO", "PERDIDO", False, False, "Cliente no devuelve"),
    ("EN_CLIENTE_VACIO", "VACIO_EN_ALMACEN", False, False, "Devolucion a almacen"),
    ("EN_CLIENTE_VACIO", "PARA_REPARACION", False, False, "Danado en cliente"),
    ("VACIO_EN_ALMACEN", "EN_ALMACEN_VACIO", False, False, "Formalizacion en inventario"),
    ("EN_MANTENIMIENTO", "EN_ALMACEN_VACIO", False, False, "Mantenimiento completado"),
    ("PARA_REPARACION", "EN_MANTENIMIENTO", False, False, "Inicio de reparacion"),
    ("PARA_REPARACION", "DE_BAJA", False, False, "Reparacion no viable"),
    ("PARA_TRASLADO", "EN_RUTA", False, False, "Inicio de traslado"),
    ("PARA_TRASLADO", "EN_ALMACEN_VACIO", False, False, "Traslado cancelado"),
    ("BLOQUEADO", "EN_ALMACEN_VACIO", False, False, "Desbloqueo"),
    ("OBSERVADO", "EN_ALMACEN_VACIO", False, False, "Observacion levantada"),
    ("OBSERVADO", "DE_BAJA", False, False, "Baja por observacion"),
)

MOVEMENT_TYPE_DEFINITIONS: tuple[tuple[str, str, str, bool, str | None, str | None], ...] = (
    ("SC", "Salida a cliente", "EGRESO", True, "EN_ALMACEN_VACIO", "EN_CLIENTE_LLENO"),
    ("IC", "Ingreso desde cliente", "INGRESO", True, "EN_CLIENTE_VACIO", "EN_ALMACEN_VACIO"),
    ("IP", "Ingreso proveedor", "INGRESO", True, "CREADO_VACIO", "EN_ALMACEN_VACIO"),
    ("SP", "Salida a proveedor", "EGRESO", True, "EN_ALMACEN_VACIO", "EN_RUTA"),
    ("TR", "Traslado interno", "TRASLADO", True, "EN_ALMACEN_VACIO", "EN_ALMACEN_VACIO"),
    ("MV", "Envio a mantenimiento", "EGRESO", True, "EN_ALMACEN_VACIO", "EN_MANTENIMIENTO"),
)

AGENDA_TASK_TYPE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("ENTREGA", "Llevar cilindros llenos"),
    ("RECOJO", "Recoger cilindros vacios"),
    ("SERVICIO", "Mantenimiento en sitio"),
    ("VISITA", "Visita programada"),
    ("COBRO", "Cobranza"),
)

GAS_PRODUCT_DEFINITIONS: tuple[tuple[str, str, float, str], ...] = (
    ("GLP10", "GLP 10kg", 10, "KG"),
    ("GLP15", "GLP 15kg", 15, "KG"),
    ("GLP45", "GLP 45kg", 45, "KG"),
)

BRAND_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("GENERICA", "Generica"),
    ("INDURA", "Indura"),
    ("SOLYGAS", "Solygas"),
)

SERVICE_TYPE_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("RETIMBRADO", "Retimbrado"),
    ("VALVULA", "Cambio de valvula"),
    ("PINTURA", "Pintura"),
    ("INSPECCION", "Inspeccion"),
)

CONDITION_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("CILPRO", "Cilindro propio"),
    ("CILCLI", "Cilindro del cliente"),
    ("CILPROV", "Cilindro del proveedor"),
    ("CILGAR", "Cilindro en garantia"),
)


def list_cylinder_states(db: Session) -> list[LogisticsCylinderState]:
    return list(
        db.scalars(select(LogisticsCylinderState).order_by(LogisticsCylinderState.code)).all()
    )


def list_state_transitions(db: Session) -> list[LogisticsStateTransition]:
    return list(
        db.scalars(
            select(LogisticsStateTransition).order_by(
                LogisticsStateTransition.from_state,
                LogisticsStateTransition.to_state,
            )
        ).all()
    )


def list_movement_types(db: Session) -> list[LogisticsMovementType]:
    return list(
        db.scalars(select(LogisticsMovementType).order_by(LogisticsMovementType.code)).all()
    )


def list_agenda_task_types(db: Session) -> list[LogisticsAgendaTaskType]:
    return list(
        db.scalars(select(LogisticsAgendaTaskType).order_by(LogisticsAgendaTaskType.code)).all()
    )


def list_warehouses_catalog(db: Session, *, tenant_id: str) -> list[LogisticsWarehouse]:
    return list(
        db.scalars(
            select(LogisticsWarehouse)
            .where(
                LogisticsWarehouse.tenant_id == tenant_id, LogisticsWarehouse.is_active.is_(True)
            )
            .order_by(LogisticsWarehouse.name)
        ).all()
    )


def list_vehicles_catalog(db: Session, *, tenant_id: str) -> list[LogisticsVehicle]:
    return list(
        db.scalars(
            select(LogisticsVehicle)
            .where(LogisticsVehicle.tenant_id == tenant_id, LogisticsVehicle.is_active.is_(True))
            .order_by(LogisticsVehicle.plate)
        ).all()
    )


def list_delivery_points_catalog(db: Session, *, tenant_id: str) -> list[LogisticsDeliveryPoint]:
    return list(
        db.scalars(
            select(LogisticsDeliveryPoint)
            .where(
                LogisticsDeliveryPoint.tenant_id == tenant_id,
                LogisticsDeliveryPoint.is_active.is_(True),
            )
            .order_by(LogisticsDeliveryPoint.address)
        ).all()
    )


def list_zones_catalog(db: Session, *, tenant_id: str) -> list[LogisticsZone]:
    return list(
        db.scalars(
            select(LogisticsZone)
            .where(LogisticsZone.tenant_id == tenant_id, LogisticsZone.is_active.is_(True))
            .order_by(LogisticsZone.name)
        ).all()
    )


def list_gas_products_catalog(db: Session, *, tenant_id: str) -> list[LogisticsGasProduct]:
    _ensure_tenant_envase_catalogs(db, tenant_id=tenant_id)
    return list(
        db.scalars(
            select(LogisticsGasProduct)
            .where(
                LogisticsGasProduct.tenant_id == tenant_id, LogisticsGasProduct.is_active.is_(True)
            )
            .order_by(LogisticsGasProduct.name)
        ).all()
    )


def list_brands_catalog(db: Session, *, tenant_id: str) -> list[LogisticsBrand]:
    _ensure_tenant_envase_catalogs(db, tenant_id=tenant_id)
    return list(
        db.scalars(
            select(LogisticsBrand)
            .where(LogisticsBrand.tenant_id == tenant_id, LogisticsBrand.is_active.is_(True))
            .order_by(LogisticsBrand.name)
        ).all()
    )


def list_service_types_catalog(db: Session, *, tenant_id: str) -> list[LogisticsServiceType]:
    _ensure_tenant_envase_catalogs(db, tenant_id=tenant_id)
    return list(
        db.scalars(
            select(LogisticsServiceType)
            .where(
                LogisticsServiceType.tenant_id == tenant_id,
                LogisticsServiceType.is_active.is_(True),
            )
            .order_by(LogisticsServiceType.name)
        ).all()
    )


def list_conditions_catalog(db: Session) -> list[LogisticsCylinderCondition]:
    _ensure_condition_catalog(db)
    return list(
        db.scalars(
            select(LogisticsCylinderCondition)
            .where(LogisticsCylinderCondition.is_active.is_(True))
            .order_by(LogisticsCylinderCondition.code)
        ).all()
    )


def _ensure_tenant_envase_catalogs(db: Session, *, tenant_id: str) -> None:
    has_gases = db.scalar(
        select(LogisticsGasProduct.id).where(LogisticsGasProduct.tenant_id == tenant_id).limit(1)
    )
    if has_gases is None:
        for code, name, content_kg, unit in GAS_PRODUCT_DEFINITIONS:
            db.add(
                LogisticsGasProduct(
                    tenant_id=tenant_id,
                    code=code,
                    name=name,
                    content_kg=content_kg,
                    unit=unit,
                )
            )

    has_brands = db.scalar(
        select(LogisticsBrand.id).where(LogisticsBrand.tenant_id == tenant_id).limit(1)
    )
    if has_brands is None:
        for code, name in BRAND_DEFINITIONS:
            db.add(LogisticsBrand(tenant_id=tenant_id, code=code, name=name))

    has_service_types = db.scalar(
        select(LogisticsServiceType.id).where(LogisticsServiceType.tenant_id == tenant_id).limit(1)
    )
    if has_service_types is None:
        for code, name in SERVICE_TYPE_DEFINITIONS:
            db.add(LogisticsServiceType(tenant_id=tenant_id, code=code, name=name))

    db.flush()


def _ensure_condition_catalog(db: Session) -> None:
    has_conditions = db.scalar(select(LogisticsCylinderCondition.code).limit(1))
    if has_conditions is None:
        for code, name in CONDITION_DEFINITIONS:
            db.add(LogisticsCylinderCondition(code=code, name=name))
        db.flush()
