from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from systutor.api.deps import get_db_session
from systutor.kernel.auth.dependencies import require_permission

from plugins.tms.backend.models import JornadaTMS

DB_SESSION = Depends(get_db_session)

router = APIRouter(prefix="/tms/jornadas", tags=["tms"])


class JornadaItemEdit(BaseModel):
    cod_producto: int = Field(ge=0)
    producto: str = ""
    pesito: float = 0.0
    cantidad: float = 0.0


class JornadaPatchRequest(BaseModel):
    placa: str | None = None
    chofer_dni: str | None = None
    direccion_llegada: str | None = None
    observacion: str | None = None
    tipo_transaccion: str | None = None
    items: list[JornadaItemEdit] | None = None


def _serializar(jornada: JornadaTMS) -> dict[str, Any]:
    try:
        items = json.loads(jornada.items) if jornada.items else []
    except (ValueError, TypeError):
        items = []
    return {
        "id": jornada.id,
        "cod_movimiento_legacy": jornada.cod_movimiento_legacy,
        "estado": jornada.estado,
        "fecha": jornada.fecha.isoformat() if jornada.fecha else None,
        "placa": jornada.placa,
        "chofer_dni": jornada.chofer_dni,
        "almacen": jornada.almacen,
        "cod_cliente": jornada.cod_cliente,
        "cliente": jornada.cliente,
        "direccion_llegada": jornada.direccion_llegada,
        "tipo_transaccion": jornada.tipo_transaccion,
        "observacion": jornada.observacion,
        "items": items,
    }


@router.get("", status_code=status.HTTP_200_OK)
def list_jornadas(
    estado: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = DB_SESSION,
    _: None = Depends(require_permission("tms.jornada.read")),
) -> dict[str, Any]:
    q = db.query(JornadaTMS)
    if estado:
        q = q.filter(JornadaTMS.estado == estado)
    total = q.count()
    filas = q.order_by(JornadaTMS.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [_serializar(x) for x in filas]}


@router.get("/{jornada_id}", status_code=status.HTTP_200_OK)
def get_jornada(
    jornada_id: int,
    db: Session = DB_SESSION,
    _: None = Depends(require_permission("tms.jornada.read")),
) -> dict[str, Any]:
    jornada = db.get(JornadaTMS, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no existe")
    return _serializar(jornada)


@router.patch("/{jornada_id}", status_code=status.HTTP_200_OK)
def edit_jornada(
    jornada_id: int,
    payload: JornadaPatchRequest,
    db: Session = DB_SESSION,
    _: None = Depends(require_permission("tms.jornada.edit")),
) -> dict[str, Any]:
    jornada = db.get(JornadaTMS, jornada_id)
    if jornada is None:
        raise HTTPException(status_code=404, detail="Jornada no existe")
    if jornada.estado == "confirmed":
        raise HTTPException(status_code=409, detail="Jornada confirmada no es editable")

    data = payload.model_dump(exclude_unset=True)
    for campo in ("placa", "chofer_dni", "direccion_llegada", "observacion", "tipo_transaccion"):
        if campo in data and data[campo] is not None:
            setattr(jornada, campo, data[campo])

    if "items" in data and data["items"] is not None:
        jornada.items = json.dumps([i.model_dump() for i in payload.items], ensure_ascii=False)

    placa = (jornada.placa or "").strip()
    chofer = (jornada.chofer_dni or "").strip()
    if jornada.estado == "pendiente" and placa and chofer:
        jornada.estado = "draft"

    db.commit()
    db.refresh(jornada)
    return {
        "id": jornada.id,
        "estado": jornada.estado,
        "placa": jornada.placa,
        "chofer_dni": jornada.chofer_dni,
        "direccion_llegada": jornada.direccion_llegada,
        "tipo_transaccion": jornada.tipo_transaccion,
        "observacion": jornada.observacion,
        "items": jornada.items,
    }


__all__ = ["router"]
