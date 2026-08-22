"""Puertos TMS hacia el host.

ÚNICO módulo del plugin autorizado a conocer artefactos externos
(kernel, logistics, crm, productos, config del host). El resto del plugin
depende exclusivamente de los protocolos, views y registro definidos aquí.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Protocol


# ---------------------------------------------------------------------------
# Views (contratos mínimos de datos que TMS consume del host)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TenantView:
    id: str


@dataclass(slots=True)
class BranchView:
    id: str


@dataclass(slots=True)
class SyncContextView:
    tenant: TenantView
    branch: BranchView | None
    actor_user_id: str | None


@dataclass(slots=True)
class CustomerView:
    id: str
    fiscal_address_id: str | None = None


@dataclass(slots=True)
class ProductRefView:
    id: str


@dataclass(slots=True)
class CustomerUpsert:
    tenant_id: str
    external_code: str
    legal_name: str
    document_type_code: str
    document_number: str
    email: str | None = None
    phone: str | None = None
    created_by: str | None = None


@dataclass(slots=True)
class CustomerPatch:
    legal_name: str
    email: str | None
    phone: str | None
    external_code_fallback: str


@dataclass(slots=True)
class AddressSpec:
    tenant_id: str
    customer_id: str
    line1: str


@dataclass(slots=True)
class LineSpec:
    tenant_id: str
    code: str
    name: str


@dataclass(slots=True)
class UnitSpec:
    tenant_id: str
    code: str
    name: str


@dataclass(slots=True)
class ProductUpsert:
    tenant_id: str
    legacy_id: int
    sku: str
    name: str
    line_id: str
    unit_id: str
    condition_code: str
    weight_kg: float | None = None
    content_m3: float | None = None
    created_by: str | None = None


@dataclass(slots=True)
class ProductPatch:
    legacy_id: int
    name: str
    line_id: str
    unit_id: str
    weight_kg: float | None
    content_m3: float | None


@dataclass(slots=True)
class LoadPlanItemSpec:
    product_id: str
    planned_quantity: float
    source_warehouse_id: str
    notes: str | None = None


@dataclass(slots=True)
class LiveSessionSpec:
    tenant_id: str
    vehicle_id: str
    driver_id: str
    origin_warehouse_id: str
    branch_id: str | None
    actor_user_id: str
    opened_at: Any


@dataclass(slots=True)
class WarehouseUpsertResult:
    warehouse_id: str
    created: bool


# ---------------------------------------------------------------------------
# Protocolo de contexto de host (duck-typed por el loader de plugins)
# ---------------------------------------------------------------------------


class HostContext(Protocol):
    def register_router(self, router: Any) -> None: ...

    def register_permissions(self, permissions: list[str]) -> None: ...

    def register_events(self, events: list[str]) -> None: ...


# ---------------------------------------------------------------------------
# Puertos
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class TmsPorts:
    # runtime host
    db_session_dependency: Callable[..., Any]
    require_permission: Callable[[str], Any]
    get_settings: Callable[[], Any]
    session_factory: Callable[[], Any]

    # sync jornadas vivas
    resolve_sync_context: Callable[[Any], SyncContextView]
    hash_secret: Callable[[str], str]
    ensure_driver: Callable[..., str]
    ensure_vehicle: Callable[..., str]
    find_warehouse_id: Callable[..., str | None]
    find_product_id_by_legacy: Callable[..., str | None]
    find_live_session_id: Callable[..., str | None]
    create_live_session: Callable[..., str]
    upsert_load_plan_items: Callable[..., bool]

    # link legacy — clientes
    find_customer_by_doc: Callable[..., CustomerView | None]
    find_customer_by_external: Callable[..., CustomerView | None]
    create_customer: Callable[..., str]
    patch_customer: Callable[..., None]
    ensure_customer_address: Callable[..., str]
    set_fiscal_address: Callable[..., None]

    # link legacy — productos
    existing_product_by_legacy: Callable[..., ProductRefView | None]
    existing_product_by_sku: Callable[..., str | None]
    used_skus: Callable[..., set[str]]
    create_product: Callable[..., str]
    patch_product: Callable[..., None]
    ensure_product_line: Callable[..., str]
    ensure_product_unit: Callable[..., str]

    # link legacy — almacenes
    upsert_warehouse: Callable[..., WarehouseUpsertResult]


# ---------------------------------------------------------------------------
# Registro global de puertos
# ---------------------------------------------------------------------------

_ports: TmsPorts | None = None


def set_ports(ports: TmsPorts) -> None:
    global _ports
    _ports = ports


def reset_ports() -> None:
    global _ports
    _ports = None


def get_ports() -> TmsPorts:
    if _ports is None:
        from plugins.tms.backend.host_adapter import build_host_ports

        set_ports(build_host_ports())
    assert _ports is not None
    return _ports


def db_session(request: Any = None) -> Any:
    """Dependencia FastAPI estable que delega en los puertos actuales."""
    return get_ports().db_session_dependency(request)


def permission_dependency(name: str) -> Any:
    """Devuelve la dependencia FastAPI del host para el permiso dado.

    Se evalúa al importar el router; configurar puertos antes de importar.
    """
    return get_ports().require_permission(name)
