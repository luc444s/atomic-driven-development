from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TmsBase(DeclarativeBase):
    """Base declarativa propia del plugin — sin dependencia del host."""


def utc_now() -> datetime:
    return datetime.now(UTC)


class JornadaTMS(TmsBase):
    __tablename__ = "tms_jornada"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cod_movimiento_legacy: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    fecha: Mapped[date] = mapped_column(Date)
    estado: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    placa: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    chofer_dni: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    almacen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cod_cliente: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cliente: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    direccion_llegada: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    tipo_transaccion: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    observacion: Mapped[str] = mapped_column(String(400), default="", nullable=False)
    items: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now, nullable=False
    )
