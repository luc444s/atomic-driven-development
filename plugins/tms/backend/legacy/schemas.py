from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ClienteLegacy(BaseModel):
    id: int
    dni: str = ""
    ruc: str = ""
    nombre: str = ""
    direccion: str = ""
    telefono: str = ""
    email: str = ""


class PuntoLegacy(BaseModel):
    id: int
    direccion: str = ""
    telefono: str = ""
    contacto: str = ""
    ubigeo: str = ""
    zona: str = ""
    correo: str = ""


class ProductoLegacy(BaseModel):
    id: int
    nro: str = ""
    nombre: str = ""
    linea: int = 0
    unidad: int = 0
    linea_nombre: str = ""
    unidad_nombre: str = ""


class ProductoDetalleLegacy(ProductoLegacy):
    m3: float = 0.0
    peso_kg: float = 0.0
    peso_tara_kg: float = 0.0
    peso_total_kg: float = 0.0
    unidad_medida: str = ""


class StockLegacy(BaseModel):
    cod_producto: int
    almacen: int
    stock: float


class AlmacenLegacy(BaseModel):
    cod: int
    descripcion: str = ""
    razon_social: int = 0


class MovimientoLegacyResult(BaseModel):
    status: str
    cod_movimiento: int = 0


class SalidaItemLegacy(BaseModel):
    cod_producto: int
    producto: str = ""
    pesito: float = 0.0
    cantidad: float = 0.0


class SalidaLegacy(BaseModel):
    cod_movimiento: int
    fecha: datetime
    nro_documento: str = ""
    cod_cliente: int = 0
    cliente: str = ""
    almacen: int = 0
    placa: str = ""
    dnichofer: str = ""
    nro_guia: str = ""
    transportista: str = ""
    lugar_inicio: str = ""
    lugar_destino: str = ""
    dir_inicio: str = ""
    dir_destino: str = ""
    empresa_trans: str = ""
    ruc_empresa: str = ""
    observacion: str = ""
    total: float = 0.0
    tipo_transaccion: str = ""
    items: list[SalidaItemLegacy] = Field(default_factory=list)


class LegacyApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class LegacyAuthError(LegacyApiError):
    pass


class LegacyTimeoutError(LegacyApiError):
    pass


class LegacyBadResponseError(LegacyApiError):
    pass


class EgresoRequest(BaseModel):
    cod_producto: int
    almacen: int
    cantidad: float = Field(gt=0)
    idempotency_key: str = Field(min_length=1, max_length=90)
