"""Adaptador del plugin TMS hacia el kernel del monorepo.

Mismo estatus fronterizo que ports.py: es el único otro módulo autorizado
a importar systutor/logistics/crm/productos. Construye TmsPorts con las
implementaciones reales del host.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select

from systutor.api.deps import get_db_session
from systutor.core.database import build_session_factory
from systutor.kernel.auth.dependencies import require_permission as _require_permission
from systutor.kernel.auth.models import User
from systutor.kernel.auth.security import hash_password
from systutor.kernel.permissions.models import Role
from systutor.kernel.permissions.service import assign_role_to_user
from systutor.kernel.tenants.models import Branch, Tenant
from systutor.kernel.tenants.service import assign_branch_to_user

from apps.api.app.config import get_settings

from plugins.crm.backend.models import CrmCustomer, CrmCustomerAddress
from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.dto.load_plans import (
    LoadPlanItemUpsert,
    LoadPlanUpsertRequest,
)
from plugins.logistics.backend.models import (
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.services.load_plans import upsert_load_plan
from plugins.logistics.backend.services.sessions import create_vehicle_session
from plugins.productos.backend.models import Product, ProductLine, ProductUnit

from plugins.tms.backend.ports import (
    AddressSpec,
    BranchView,
    CustomerPatch,
    CustomerUpsert,
    CustomerView,
    LineSpec,
    LiveSessionSpec,
    LoadPlanItemSpec,
    ProductPatch,
    ProductRefView,
    ProductUpsert,
    SyncContextView,
    TenantView,
    TmsPorts,
    UnitSpec,
    WarehouseUpsertResult,
)


def db_session_dependency(request):
    """Dependencia FastAPI que delega en get_db_session del host."""
    return get_db_session(request)


def require_permission(name: str) -> Any:
    return _require_permission(name)


def session_factory() -> Any:
    return build_session_factory(get_settings())


def resolve_sync_context(db: Any) -> SyncContextView:
    settings = get_settings()
    tenant = db.scalar(select(Tenant).where(Tenant.slug == settings.seed_demo_tenant_slug))
    branch = actor = None
    if tenant is not None:
        branch = db.scalar(
            select(Branch).where(
                Branch.tenant_id == tenant.id,
                Branch.code == settings.seed_demo_branch_code,
            )
        )
        actor = db.scalar(select(User).where(User.email == settings.seed_admin_email))
    return SyncContextView(
        tenant=TenantView(id=tenant.id),
        branch=BranchView(id=branch.id) if branch is not None else None,
        actor_user_id=actor.id if actor is not None else None,
    )


# ---------------------------------------------------------------------------
# Jornadas vivas (logistics + auth)
# ---------------------------------------------------------------------------


def ensure_driver(db: Any, *, tenant_id: str, branch_id: str | None, dni: str,
                  full_name: str) -> str:
    email = f"{dni}@oxipur.com"
    user = db.scalar(select(User).where(User.email == email))
    if user is not None:
        return user.id
    role = db.scalar(
        select(Role).where(Role.tenant_id == tenant_id, Role.name == "driver")
    )
    if role is None:
        role = Role(
            tenant_id=tenant_id,
            name="driver",
            description="Conductor — operaciones de ruta y consulta de catalogo",
        )
        db.add(role)
        db.flush()
    user = User(
        tenant_id=tenant_id,
        branch_id=None,
        email=email,
        full_name=full_name.strip() or f"Conductor {dni}",
        password_hash=hash_password(dni),
        is_active=True,
        category="driver",
    )
    db.add(user)
    db.flush()
    branch = db.get(Branch, branch_id) if branch_id else None
    assign_branch_to_user(db, user, branch)
    assign_role_to_user(db, user=user, role=role)
    db.flush()
    return user.id


def _normalize_plate(placa: str) -> str:
    return placa.strip().upper().replace("-", "").replace("/", "")


def ensure_vehicle(db: Any, *, tenant_id: str, plate: str,
                   vehicle_type: str | None = None) -> str:
    canonical = _normalize_plate(plate)
    for v in db.scalars(
        select(LogisticsVehicle).where(
            LogisticsVehicle.tenant_id == tenant_id,
            LogisticsVehicle.is_active.is_(True),
        )
    ).all():
        if _normalize_plate(v.plate) == canonical:
            return v.id
    vehicle = LogisticsVehicle(
        tenant_id=tenant_id,
        plate=plate.strip().upper(),
        vehicle_type=vehicle_type or "CAMION",
        is_active=True,
    )
    db.add(vehicle)
    db.flush()
    return vehicle.id


def find_warehouse_id(db: Any, *, tenant_id: str, code: str) -> str | None:
    wh = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.tenant_id == tenant_id,
            LogisticsWarehouse.code == code,
        )
    )
    return wh.id if wh is not None else None


def find_product_id_by_legacy(db: Any, *, tenant_id: str, legacy_id: int) -> str | None:
    p = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.legacy_id == legacy_id)
    )
    return p.id if p is not None else None


def find_live_session_id(db: Any, *, tenant_id: str, vehicle_id: str,
                         driver_id: str, fecha: date) -> str | None:
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
            return s.id
    return None


def create_live_session(db: Any, spec: LiveSessionSpec) -> str:
    payload = type(
        "LiveSessionPayload",
        (),
        {
            "vehicle_id": spec.vehicle_id,
            "driver_id": spec.driver_id,
            "origin_warehouse_id": spec.origin_warehouse_id,
            "route_id": None,
        },
    )()
    context = LogisticsActionContext(
        tenant_id=spec.tenant_id,
        branch_id=spec.branch_id,
        actor_user_id=spec.actor_user_id,
        correlation_id=None,
        request_id=None,
    )
    session = create_vehicle_session(
        db,
        tenant_id=spec.tenant_id,
        payload=payload,
        action_context=context,
        opened_at=spec.opened_at,
    )
    return session.id


def upsert_load_plan_items(db: Any, *, session_id: str, tenant_id: str,
                           actor_user_id: str, notes: str,
                           items: list[LoadPlanItemSpec]) -> bool:
    if not items:
        return False
    session_obj = db.get(LogisticsVehicleSession, session_id)
    if session_obj is None:
        return False
    payload = LoadPlanUpsertRequest(
        notes=notes,
        items=[
            LoadPlanItemUpsert(
                product_id=i.product_id,
                planned_quantity=i.planned_quantity,
                source_warehouse_id=i.source_warehouse_id,
                notes=i.notes,
            )
            for i in items
        ],
    )
    context = LogisticsActionContext(
        tenant_id=tenant_id,
        branch_id=None,
        actor_user_id=actor_user_id,
        correlation_id=None,
        request_id=None,
    )
    upsert_load_plan(db, session=session_obj, payload=payload, action_context=context)
    return True


# ---------------------------------------------------------------------------
# Link legacy — clientes (crm)
# ---------------------------------------------------------------------------


def find_customer_by_doc(db: Any, *, tenant_id: str, doc_type: str,
                         doc_number: str) -> CustomerView | None:
    c = db.scalar(
        select(CrmCustomer).where(
            CrmCustomer.tenant_id == tenant_id,
            CrmCustomer.document_type_code == doc_type,
            CrmCustomer.document_number == doc_number,
        )
    )
    return CustomerView(id=c.id, fiscal_address_id=c.fiscal_address_id) if c else None


def find_customer_by_external(db: Any, *, tenant_id: str,
                              external_code: str) -> CustomerView | None:
    c = db.scalar(
        select(CrmCustomer).where(
            CrmCustomer.tenant_id == tenant_id,
            CrmCustomer.external_code == external_code,
        )
    )
    return CustomerView(id=c.id, fiscal_address_id=c.fiscal_address_id) if c else None


def create_customer(db: Any, u: CustomerUpsert) -> str:
    customer = CrmCustomer(
        tenant_id=u.tenant_id,
        external_code=u.external_code,
        legal_name=u.legal_name[:200],
        commercial_name=None,
        document_type_code=u.document_type_code,
        document_number=u.document_number[:30],
        country_code="PE",
        email=u.email or None,
        phone=u.phone or None,
        is_active=True,
        created_by=u.created_by,
    )
    db.add(customer)
    db.flush()
    return customer.id


def patch_customer(db: Any, customer_id: str, p: CustomerPatch) -> None:
    customer = db.get(CrmCustomer, customer_id)
    if customer is None:
        return
    customer.legal_name = p.legal_name[:200]
    customer.external_code = customer.external_code or p.external_code_fallback
    if not customer.email and p.email:
        customer.email = p.email
    if not customer.phone and p.phone:
        customer.phone = p.phone
    db.add(customer)


def ensure_customer_address(db: Any, a: AddressSpec) -> str:
    line1 = (a.line1 or "Sin direccion")[:200]
    existing = db.scalar(
        select(CrmCustomerAddress).where(
            CrmCustomerAddress.tenant_id == a.tenant_id,
            CrmCustomerAddress.customer_id == a.customer_id,
            CrmCustomerAddress.line1 == line1,
        )
    )
    if existing is not None:
        return existing.id
    address = CrmCustomerAddress(
        tenant_id=a.tenant_id,
        customer_id=a.customer_id,
        address_type="DELIVERY",
        line1=line1,
        country_code="PE",
    )
    db.add(address)
    db.flush()
    return address.id


def set_fiscal_address(db: Any, *, customer_id: str, address_id: str) -> None:
    customer = db.get(CrmCustomer, customer_id)
    if customer is not None:
        customer.fiscal_address_id = address_id
        db.add(customer)


# ---------------------------------------------------------------------------
# Link legacy — productos (productos)
# ---------------------------------------------------------------------------


def existing_product_by_legacy(db: Any, *, tenant_id: str,
                               legacy_id: int) -> ProductRefView | None:
    p = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.legacy_id == legacy_id)
    )
    return ProductRefView(id=p.id) if p else None


def existing_product_by_sku(db: Any, *, tenant_id: str, sku: str) -> str | None:
    p = db.scalar(
        select(Product).where(Product.tenant_id == tenant_id, Product.sku == sku)
    )
    return p.id if p else None


def used_skus(db: Any, *, tenant_id: str) -> set[str]:
    return set(
        db.scalars(select(Product.sku).where(Product.tenant_id == tenant_id)).all()
    )


def create_product(db: Any, u: ProductUpsert) -> str:
    product = Product(
        tenant_id=u.tenant_id,
        legacy_id=u.legacy_id,
        sku=u.sku,
        name=u.name[:200],
        line_id=u.line_id,
        unit_id=u.unit_id,
        status_code="ACTIVO",
        condition_code=u.condition_code,
        weight_kg=u.weight_kg,
        content_m3=u.content_m3,
        country_code="PE",
        is_active=True,
        created_by=u.created_by,
    )
    db.add(product)
    db.flush()
    return product.id


def patch_product(db: Any, product_id: str, p: ProductPatch) -> None:
    product = db.get(Product, product_id)
    if product is None:
        return
    product.legacy_id = product.legacy_id or p.legacy_id
    product.name = p.name[:200]
    product.line_id = p.line_id
    product.unit_id = p.unit_id
    if product.weight_kg is None and p.weight_kg is not None:
        product.weight_kg = p.weight_kg
    if product.content_m3 is None and p.content_m3 is not None:
        product.content_m3 = p.content_m3
    db.add(product)


def ensure_product_line(db: Any, s: LineSpec) -> str:
    line = db.scalar(
        select(ProductLine).where(
            ProductLine.tenant_id == s.tenant_id, ProductLine.code == s.code
        )
    )
    if line is None:
        line = ProductLine(tenant_id=s.tenant_id, code=s.code, name=s.name[:100])
        db.add(line)
        db.flush()
    return line.id


def ensure_product_unit(db: Any, s: UnitSpec) -> str:
    unit = db.scalar(
        select(ProductUnit).where(
            ProductUnit.tenant_id == s.tenant_id, ProductUnit.code == s.code
        )
    )
    if unit is None:
        unit = ProductUnit(tenant_id=s.tenant_id, code=s.code, name=s.name[:50])
        db.add(unit)
        db.flush()
    return unit.id


# ---------------------------------------------------------------------------
# Link legacy — almacenes (logistics)
# ---------------------------------------------------------------------------


def upsert_warehouse(db: Any, *, tenant_id: str, branch_id: str, code: str,
                     name: str, is_primary: bool) -> WarehouseUpsertResult:
    warehouse = db.scalar(
        select(LogisticsWarehouse).where(
            LogisticsWarehouse.tenant_id == tenant_id,
            LogisticsWarehouse.code == code,
        )
    )
    if warehouse is None:
        warehouse = LogisticsWarehouse(
            tenant_id=tenant_id,
            branch_id=branch_id,
            code=code,
            name=(name or f"Almacen {code}")[:100],
            warehouse_type="FIXED",
            is_primary=is_primary,
            is_active=True,
        )
        db.add(warehouse)
        db.flush()
        return WarehouseUpsertResult(warehouse_id=warehouse.id, created=True)
    warehouse.name = (name or warehouse.name)[:100]
    db.add(warehouse)
    return WarehouseUpsertResult(warehouse_id=warehouse.id, created=False)


def build_host_ports() -> TmsPorts:
    return TmsPorts(
        db_session_dependency=db_session_dependency,
        require_permission=require_permission,
        get_settings=get_settings,
        session_factory=session_factory,
        resolve_sync_context=resolve_sync_context,
        hash_secret=hash_password,
        ensure_driver=ensure_driver,
        ensure_vehicle=ensure_vehicle,
        find_warehouse_id=find_warehouse_id,
        find_product_id_by_legacy=find_product_id_by_legacy,
        find_live_session_id=find_live_session_id,
        create_live_session=create_live_session,
        upsert_load_plan_items=upsert_load_plan_items,
        find_customer_by_doc=find_customer_by_doc,
        find_customer_by_external=find_customer_by_external,
        create_customer=create_customer,
        patch_customer=patch_customer,
        ensure_customer_address=ensure_customer_address,
        set_fiscal_address=set_fiscal_address,
        existing_product_by_legacy=existing_product_by_legacy,
        existing_product_by_sku=existing_product_by_sku,
        used_skus=used_skus,
        create_product=create_product,
        patch_product=patch_product,
        ensure_product_line=ensure_product_line,
        ensure_product_unit=ensure_product_unit,
        upsert_warehouse=upsert_warehouse,
    )
