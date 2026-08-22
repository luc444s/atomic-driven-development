from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field

from plugins.tms.backend import ports
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
    tenant_id: str
    branch_id: str
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


def link_clientes(
    db,
    clientes: list[ClienteLegacy],
    ctx: LinkContext,
    client: LegacyApiClient,
) -> LinkSummary:
    p = ports.get_ports()
    summary = LinkSummary()

    async def _fetch_puntos(cliente_id: int) -> list[PuntoLegacy]:
        try:
            return await client.get_puntos(cliente_id)
        except Exception:
            return []

    async def _fetch_all() -> dict[int, list[PuntoLegacy]]:
        semaphore = asyncio.Semaphore(PUNTOS_CONCURRENCY)

        def _bounded(cliente_id: int) -> "asyncio.Future[list[PuntoLegacy]]":
            return asyncio.ensure_future(_guarded(cliente_id))

        async def _guarded(cliente_id: int) -> list[PuntoLegacy]:
            async with semaphore:
                return await _fetch_puntos(cliente_id)

        tasks = [_bounded(c.id) for c in clientes]
        results = await asyncio.gather(*tasks)
        return {c.id: results[i] for i, c in enumerate(clientes)}

    puntos_map = asyncio.run(_fetch_all())

    for cliente in clientes:
        doc = _document_parts(cliente)
        customer = None
        if doc is not None:
            customer = p.find_customer_by_doc(
                db, tenant_id=ctx.tenant_id, doc_type=doc[0], doc_number=doc[1]
            )
        if customer is None:
            customer = p.find_customer_by_external(
                db, tenant_id=ctx.tenant_id, external_code=f"LEG-{cliente.id}"
            )

        if customer is None:
            doc_type, doc_number = doc if doc is not None else ("OTRO", str(cliente.id))
            customer_id = p.create_customer(
                db,
                ports.CustomerUpsert(
                    tenant_id=ctx.tenant_id,
                    external_code=f"LEG-{cliente.id}",
                    legal_name=(cliente.nombre or "Sin asignar")[:200],
                    document_type_code=doc_type,
                    document_number=doc_number[:30],
                    email=cliente.email or None,
                    phone=cliente.telefono or None,
                    created_by=ctx.actor_user_id,
                ),
            )
            summary.created += 1
        else:
            customer_id = customer.id
            p.patch_customer(
                db,
                customer_id,
                ports.CustomerPatch(
                    legal_name=(cliente.nombre or "Sin asignar")[:200],
                    email=cliente.email or None,
                    phone=cliente.telefono or None,
                    external_code_fallback=f"LEG-{cliente.id}",
                ),
            )
            summary.updated += 1

        if cliente.direccion and customer is not None and customer.fiscal_address_id is None:
            address_id = p.ensure_customer_address(
                db,
                ports.AddressSpec(
                    tenant_id=ctx.tenant_id,
                    customer_id=customer_id,
                    line1=cliente.direccion,
                ),
            )
            p.set_fiscal_address(db, customer_id=customer_id, address_id=address_id)

        for punto in puntos_map.get(cliente.id, []):
            if punto.direccion:
                p.ensure_customer_address(
                    db,
                    ports.AddressSpec(
                        tenant_id=ctx.tenant_id,
                        customer_id=customer_id,
                        line1=punto.direccion,
                    ),
                )

    db.commit()
    return summary


def link_productos(
    db,
    productos: list[ProductoLegacy],
    ctx: LinkContext,
    client: LegacyApiClient,
) -> LinkSummary:
    p = ports.get_ports()
    summary = LinkSummary()
    line_cache = _ensure_lines(db, ctx, productos)
    unit_cache = _ensure_units(db, ctx, productos)
    used_skus: set[str] = p.used_skus(db, tenant_id=ctx.tenant_id)

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

        tasks = [asyncio.ensure_future(_bounded(pr.id)) for pr in productos]
        results = await asyncio.gather(*tasks)
        return {
            pr.id: resultado
            for i, pr in enumerate(productos)
            if (resultado := results[i]) is not None
        }

    detalles = asyncio.run(_fetch_all())

    for producto in productos:
        existing = p.existing_product_by_legacy(
            db, tenant_id=ctx.tenant_id, legacy_id=producto.id
        )
        sku: str
        if existing is None:
            sku = _unique_sku(producto)
            existing_id = p.existing_product_by_sku(db, tenant_id=ctx.tenant_id, sku=sku)
        else:
            existing_id = existing.id
            sku = ""

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
        weight = detalle.peso_kg if detalle and detalle.peso_kg > 0 else None
        volume = detalle.m3 if detalle and detalle.m3 > 0 else None
        name = (producto.nombre or "Sin asignar")[:200]

        if existing_id is None:
            p.create_product(
                db,
                ports.ProductUpsert(
                    tenant_id=ctx.tenant_id,
                    legacy_id=producto.id,
                    sku=sku,
                    name=name,
                    line_id=line_id,
                    unit_id=unit_id,
                    condition_code=condition,
                    weight_kg=weight,
                    content_m3=volume,
                    created_by=ctx.actor_user_id,
                ),
            )
            summary.created += 1
        else:
            p.patch_product(
                db,
                existing_id,
                ports.ProductPatch(
                    legacy_id=producto.id,
                    name=name,
                    line_id=line_id,
                    unit_id=unit_id,
                    weight_kg=weight,
                    content_m3=volume,
                ),
            )
            summary.updated += 1

    db.commit()
    return summary


def _ensure_lines(
    db,
    ctx: LinkContext,
    productos: list[ProductoLegacy],
) -> dict[int, str]:
    p = ports.get_ports()
    cache: dict[int, str] = {}
    for producto in productos:
        if producto.linea in cache:
            continue
        code = f"LEG-L{producto.linea}"
        name = producto.linea_nombre if producto.linea != 0 else "Sin linea"
        cache[producto.linea] = p.ensure_product_line(
            db,
            ports.LineSpec(
                tenant_id=ctx.tenant_id,
                code=code,
                name=(name or f"Linea {producto.linea}")[:100],
            ),
        )
    db.commit()
    return cache


def _ensure_units(
    db,
    ctx: LinkContext,
    productos: list[ProductoLegacy],
) -> dict[int, str]:
    p = ports.get_ports()
    cache: dict[int, str] = {}
    for producto in productos:
        if producto.unidad in cache:
            continue
        code = f"LEG-U{producto.unidad}"
        name = producto.unidad_nombre if producto.unidad != 0 else "Sin unidad"
        cache[producto.unidad] = p.ensure_product_unit(
            db,
            ports.UnitSpec(
                tenant_id=ctx.tenant_id,
                code=code,
                name=(name or f"Unidad {producto.unidad}")[:50],
            ),
        )
    db.commit()
    return cache


def link_almacenes(
    db,
    almacenes: list[AlmacenLegacy],
    ctx: LinkContext,
) -> LinkSummary:
    p = ports.get_ports()
    summary = LinkSummary()
    for almacen in almacenes:
        code = str(almacen.cod)
        result = p.upsert_warehouse(
            db,
            tenant_id=ctx.tenant_id,
            branch_id=ctx.branch_id,
            code=code,
            name=(almacen.descripcion or f"Almacen {code}"),
            is_primary=almacen.cod == 1,
        )
        if result.created:
            summary.created += 1
        else:
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
