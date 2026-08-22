from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field

from sqlalchemy import Select, select
from sqlalchemy.orm import Session
from systutor.kernel.tenants.models import Branch, Tenant

from plugins.crm.backend.models import CrmCustomer, CrmCustomerAddress
from plugins.logistics.backend.models import LogisticsWarehouse
from plugins.productos.backend.models import Product, ProductLine, ProductUnit
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.legacy.schemas import (
    AlmacenLegacy,
    ClienteLegacy,
    ProductoDetalleLegacy,
    ProductoLegacy,
    PuntoLegacy,
)

DETALLE_CONCURRENCY = 25
PUNTOS_CONCURRENCY = 25

_GAS_LINE_NAMES = {
    "GAS CARBONICO",
    "ARGON",
    "OXIGENO",
    "MEZCLA",
    "NITROGENO",
    "ACETILENO",
    "HELIO",
    "OXIGENO MEDIC",
    "OXIGENO 20K",
    "ARGON 20K",
    "MEZCLA 20K",
    "OXIGENO 21K",
}


@dataclass(slots=True)
class LinkContext:
    tenant: Tenant
    branch: Branch
    actor_user_id: str


@dataclass(slots=True)
class LinkSummary:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    details: list[str] = field(default_factory=list)


def _document_parts(cliente: ClienteLegacy) -> tuple[str, str] | None:
    ruc = (cliente.ruc or "").strip()
    if re.fullmatch(r"\d{11}", ruc):
        return ("RUC", ruc)
    dni = (cliente.dni or "").strip()
    if re.fullmatch(r"\d{8}", dni):
        return ("DNI", dni)
    return None


def _customer_select_doc(
    db: Session, tenant_id: str, doc_type: str, doc_number: str
) -> CrmCustomer | None:
    stmt: Select[tuple[CrmCustomer]] = select(CrmCustomer).where(
        CrmCustomer.tenant_id == tenant_id,
        CrmCustomer.document_type_code == doc_type,
        CrmCustomer.document_number == doc_number,
    )
    return db.scalar(stmt)


def _customer_select_external(
    db: Session, tenant_id: str, external_code: str
) -> CrmCustomer | None:
    stmt: Select[tuple[CrmCustomer]] = select(CrmCustomer).where(
        CrmCustomer.tenant_id == tenant_id,
        CrmCustomer.external_code == external_code,
    )
    return db.scalar(stmt)


def link_clientes(
    db: Session,
    clientes: list[ClienteLegacy],
    ctx: LinkContext,
    client: LegacyApiClient,
) -> LinkSummary:
    summary = LinkSummary()

    async def _fetch_puntos(cliente_id: int) -> list[PuntoLegacy]:
        try:
            return await client.get_puntos(cliente_id)
        except Exception:
            return []

    async def _fetch_all() -> dict[int, list[PuntoLegacy]]:
        semaphore = asyncio.Semaphore(PUNTOS_CONCURRENCY)

        async def _bounded(cliente_id: int) -> list[PuntoLegacy]:
            async with semaphore:
                return await _fetch_puntos(cliente_id)

        tasks = [asyncio.ensure_future(_bounded(c.id)) for c in clientes]
        results = await asyncio.gather(*tasks)
        return {c.id: results[i] for i, c in enumerate(clientes)}

    puntos_map = asyncio.run(_fetch_all())

    for cliente in clientes:
        doc = _document_parts(cliente)
        customer: CrmCustomer | None = None
        if doc is not None:
            customer = _customer_select_doc(db, ctx.tenant.id, doc[0], doc[1])
        if customer is None:
            customer = _customer_select_external(db, ctx.tenant.id, f"LEG-{cliente.id}")

        if customer is None:
            doc_type, doc_number = doc if doc is not None else ("OTRO", str(cliente.id))
            customer = CrmCustomer(
                tenant_id=ctx.tenant.id,
                external_code=f"LEG-{cliente.id}",
                legal_name=(cliente.nombre or "Sin asignar")[:200],
                commercial_name=None,
                document_type_code=doc_type,
                document_number=doc_number[:30],
                country_code="PE",
                email=(cliente.email or None),
                phone=(cliente.telefono or None),
                is_active=True,
                created_by=ctx.actor_user_id,
            )
            db.add(customer)
            db.flush()
            summary.created += 1
        else:
            customer.legal_name = (cliente.nombre or "Sin asignar")[:200]
            customer.external_code = customer.external_code or f"LEG-{cliente.id}"
            if not customer.email and cliente.email:
                customer.email = cliente.email
            if not customer.phone and cliente.telefono:
                customer.phone = cliente.telefono
            db.add(customer)
            summary.updated += 1

        if cliente.direccion and customer.fiscal_address_id is None:
            address = _ensure_address(db, ctx, customer.id, cliente.direccion)
            customer.fiscal_address_id = address.id
            db.add(customer)

        for punto in puntos_map.get(cliente.id, []):
            if punto.direccion:
                _ensure_address(db, ctx, customer.id, punto.direccion)

    db.commit()
    return summary


def _ensure_address(
    db: Session,
    ctx: LinkContext,
    customer_id: str,
    direccion: str,
) -> CrmCustomerAddress:
    line1 = (direccion or "Sin direccion")[:200]
    stmt: Select[tuple[CrmCustomerAddress]] = select(CrmCustomerAddress).where(
        CrmCustomerAddress.tenant_id == ctx.tenant.id,
        CrmCustomerAddress.customer_id == customer_id,
        CrmCustomerAddress.line1 == line1,
    )
    existing = db.scalar(stmt)
    if existing is not None:
        return existing
    address = CrmCustomerAddress(
        tenant_id=ctx.tenant.id,
        customer_id=customer_id,
        address_type="DELIVERY",
        line1=line1,
        country_code="PE",
    )
    db.add(address)
    db.flush()
    return address


def link_productos(
    db: Session,
    productos: list[ProductoLegacy],
    ctx: LinkContext,
    client: LegacyApiClient,
) -> LinkSummary:
    summary = LinkSummary()
    line_cache = _ensure_lines(db, ctx, productos)
    unit_cache = _ensure_units(db, ctx, productos)
    used_skus: set[str] = set(
        db.scalars(select(Product.sku).where(Product.tenant_id == ctx.tenant.id)).all()
    )

    def _unique_sku(producto: ProductoLegacy) -> str:
        nro = (producto.nro or "").strip()
        base = (nro or str(producto.id))[:30]
        if base not in used_skus:
            used_skus.add(base)
            return base
        suffix = f"-{producto.id}"
        candidate = base[: 30 - len(suffix)] + suffix
        if candidate not in used_skus:
            used_skus.add(candidate)
            return candidate
        candidate = str(producto.id)[:30]
        used_skus.add(candidate)
        return candidate

    async def _fetch_detalle(producto_id: int) -> ProductoDetalleLegacy | None:
        try:
            return await client.get_producto(producto_id)
        except Exception:
            return None

    async def _fetch_all() -> dict[int, ProductoDetalleLegacy]:
        semaphore = asyncio.Semaphore(DETALLE_CONCURRENCY)

        async def _bounded(producto_id: int) -> ProductoDetalleLegacy | None:
            async with semaphore:
                return await _fetch_detalle(producto_id)

        tasks = [asyncio.ensure_future(_bounded(p.id)) for p in productos]
        results = await asyncio.gather(*tasks)
        return {
            p.id: resultado
            for i, p in enumerate(productos)
            if (resultado := results[i]) is not None
        }

    detalles = asyncio.run(_fetch_all())

    for producto in productos:
        stmt: Select[tuple[Product]] = select(Product).where(
            Product.tenant_id == ctx.tenant.id,
            Product.legacy_id == producto.id,
        )
        existing = db.scalar(stmt)
        if existing is None:
            sku = _unique_sku(producto)
            stmt_sku: Select[tuple[Product]] = select(Product).where(
                Product.tenant_id == ctx.tenant.id,
                Product.sku == sku,
            )
            existing = db.scalar(stmt_sku)

        line_id = line_cache.get(producto.linea)
        unit_id = unit_cache.get(producto.unidad)
        if line_id is None or unit_id is None:
            summary.skipped += 1
            continue

        detalle = detalles.get(producto.id)
        condition = (
            "GAS"
            if (producto.linea_nombre or "").strip().upper() in _GAS_LINE_NAMES
            else "PRODUCTO"
        )

        if existing is None:
            product = Product(
                tenant_id=ctx.tenant.id,
                legacy_id=producto.id,
                sku=sku,
                name=(producto.nombre or "Sin asignar")[:200],
                line_id=line_id,
                unit_id=unit_id,
                status_code="ACTIVO",
                condition_code=condition,
                weight_kg=detalle.peso_kg if detalle and detalle.peso_kg > 0 else None,
                content_m3=detalle.m3 if detalle and detalle.m3 > 0 else None,
                country_code="PE",
                is_active=True,
                created_by=ctx.actor_user_id,
            )
            db.add(product)
            summary.created += 1
        else:
            existing.legacy_id = existing.legacy_id or producto.id
            existing.name = (producto.nombre or "Sin asignar")[:200]
            existing.line_id = line_id
            existing.unit_id = unit_id
            if existing.weight_kg is None and detalle is not None and detalle.peso_kg > 0:
                existing.weight_kg = detalle.peso_kg
            if existing.content_m3 is None and detalle is not None and detalle.m3 > 0:
                existing.content_m3 = detalle.m3
            db.add(existing)
            summary.updated += 1

    db.commit()
    return summary


def _ensure_lines(
    db: Session,
    ctx: LinkContext,
    productos: list[ProductoLegacy],
) -> dict[int, str]:
    cache: dict[int, str] = {}
    for producto in productos:
        if producto.linea in cache:
            continue
        code = f"LEG-L{producto.linea}"
        name = producto.linea_nombre if producto.linea != 0 else "Sin linea"
        stmt: Select[tuple[ProductLine]] = select(ProductLine).where(
            ProductLine.tenant_id == ctx.tenant.id,
            ProductLine.code == code,
        )
        line = db.scalar(stmt)
        if line is None:
            line = ProductLine(
                tenant_id=ctx.tenant.id,
                code=code,
                name=(name or f"Linea {producto.linea}")[:100],
            )
            db.add(line)
            db.flush()
        cache[producto.linea] = line.id
    db.commit()
    return cache


def _ensure_units(
    db: Session,
    ctx: LinkContext,
    productos: list[ProductoLegacy],
) -> dict[int, str]:
    cache: dict[int, str] = {}
    for producto in productos:
        if producto.unidad in cache:
            continue
        code = f"LEG-U{producto.unidad}"
        name = producto.unidad_nombre if producto.unidad != 0 else "Sin unidad"
        stmt: Select[tuple[ProductUnit]] = select(ProductUnit).where(
            ProductUnit.tenant_id == ctx.tenant.id,
            ProductUnit.code == code,
        )
        unit = db.scalar(stmt)
        if unit is None:
            unit = ProductUnit(
                tenant_id=ctx.tenant.id,
                code=code,
                name=(name or f"Unidad {producto.unidad}")[:50],
            )
            db.add(unit)
            db.flush()
        cache[producto.unidad] = unit.id
    db.commit()
    return cache


def link_almacenes(
    db: Session,
    almacenes: list[AlmacenLegacy],
    ctx: LinkContext,
) -> LinkSummary:
    summary = LinkSummary()
    for almacen in almacenes:
        code = str(almacen.cod)
        stmt: Select[tuple[LogisticsWarehouse]] = select(LogisticsWarehouse).where(
            LogisticsWarehouse.tenant_id == ctx.tenant.id,
            LogisticsWarehouse.code == code,
        )
        warehouse = db.scalar(stmt)
        if warehouse is None:
            warehouse = LogisticsWarehouse(
                tenant_id=ctx.tenant.id,
                branch_id=ctx.branch.id,
                code=code,
                name=(almacen.descripcion or f"Almacen {code}")[:100],
                warehouse_type="FIXED",
                is_primary=almacen.cod == 1,
                is_active=True,
            )
            db.add(warehouse)
            summary.created += 1
        else:
            warehouse.name = (almacen.descripcion or warehouse.name)[:100]
            db.add(warehouse)
            summary.updated += 1
    db.commit()
    return summary


__all__ = [
    "LinkContext",
    "LinkSummary",
    "link_almacenes",
    "link_clientes",
    "link_productos",
]
