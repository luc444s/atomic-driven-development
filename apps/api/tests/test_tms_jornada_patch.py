from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

import plugins.tms.backend.models  # noqa: F401
from plugins.tms.backend.models import JornadaTMS
from plugins.tms.backend.routers.jornadas import (
    JornadaItemEdit,
    JornadaPatchRequest,
    edit_jornada,
    get_jornada,
    list_jornadas,
)

_SEQ = 5000


def _jornada(db: Session, estado: str = "pendiente") -> JornadaTMS:
    global _SEQ
    _SEQ += 1
    j = JornadaTMS(
        cod_movimiento_legacy=_SEQ,
        fecha=date(2026, 8, 20),
        estado=estado,
        placa="",
        chofer_dni="",
        almacen=1,
        cod_cliente=4587,
        cliente="M.H. EIRL",
        tipo_transaccion="CONTADO",
        items="[]",
    )
    db.add(j)
    db.flush()
    return j


def test_patch_placa_transiciona_pendiente_a_draft(db_session: Session) -> None:
    j = _jornada(db_session, estado="pendiente")

    res = edit_jornada(
        j.id,
        JornadaPatchRequest(placa="RAM/BEI-793", chofer_dni="78839842"),
        db=db_session,
        _=None,
    )

    assert res["estado"] == "draft"
    assert res["placa"] == "RAM/BEI-793"
    db_session.refresh(j)
    assert j.estado == "draft"


def test_patch_solo_observacion_no_toca_otros(db_session: Session) -> None:
    j = _jornada(db_session, estado="draft")
    j.placa = "P1"
    j.chofer_dni = "D1"

    res = edit_jornada(
        j.id,
        JornadaPatchRequest(observacion="nota"),
        db=db_session,
        _=None,
    )

    assert res["observacion"] == "nota"
    db_session.refresh(j)
    assert j.placa == "P1"
    assert j.chofer_dni == "D1"


def test_patch_items_serializa(db_session: Session) -> None:
    j = _jornada(db_session, estado="draft")

    edit_jornada(
        j.id,
        JornadaPatchRequest(
            items=[JornadaItemEdit(cod_producto=1868, producto="ABRAZADERAS", pesito=5, cantidad=0)]
        ),
        db=db_session,
        _=None,
    )

    db_session.refresh(j)
    assert '"pesito": 5.0' in j.items


def test_patch_confirmada_rechaza_409(db_session: Session) -> None:
    j = _jornada(db_session, estado="confirmed")

    with pytest.raises(HTTPException) as exc:
        edit_jornada(j.id, JornadaPatchRequest(placa="X"), db=db_session, _=None)
    assert exc.value.status_code == 409


def test_patch_inexistente_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc:
        edit_jornada(999999, JornadaPatchRequest(placa="X"), db=db_session, _=None)
    assert exc.value.status_code == 404


def test_get_jornada_detalle_devuelve_items(db_session: Session) -> None:
    j = _jornada(db_session, estado="draft")
    j.items = '[{"cod_producto": 1868, "producto": "ABRAZADERAS", "pesito": 5.0, "cantidad": 0}]'
    db_session.flush()

    res = get_jornada(j.id, db=db_session, _=None)

    assert res["id"] == j.id
    assert res["estado"] == "draft"
    assert res["items"] == [
        {"cod_producto": 1868, "producto": "ABRAZADERAS", "pesito": 5.0, "cantidad": 0}
    ]


def test_get_jornada_inexistente_404(db_session: Session) -> None:
    with pytest.raises(HTTPException) as exc:
        get_jornada(999999, db=db_session, _=None)
    assert exc.value.status_code == 404


def test_list_jornadas_filtra_por_estado(db_session: Session) -> None:
    _jornada(db_session, estado="draft")
    _jornada(db_session, estado="pendiente")
    db_session.flush()

    res = list_jornadas(estado="draft", limit=50, offset=0, db=db_session, _=None)

    assert res["total"] == 1
    assert res["items"][0]["estado"] == "draft"
