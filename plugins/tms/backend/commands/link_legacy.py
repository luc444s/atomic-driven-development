from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import select
from systutor.core.database import build_session_factory
from systutor.kernel.auth.models import User
from systutor.kernel.tenants.models import Branch, Tenant

from apps.api.app.config import get_settings
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.services.link_legacy import (
    LinkContext,
    LinkSummary,
    link_almacenes,
    link_clientes,
    link_productos,
)


def _resolve_context(db, settings) -> LinkContext:
    stmt = select(Tenant).where(Tenant.slug == settings.seed_demo_tenant_slug)
    tenant = db.scalar(stmt)
    if tenant is None:
        raise RuntimeError(
            f"No existe tenant '{settings.seed_demo_tenant_slug}'. Correr seed_demo primero."
        )

    stmt_branch = select(Branch).where(
        Branch.tenant_id == tenant.id,
        Branch.code == settings.seed_demo_branch_code,
    )
    branch = db.scalar(stmt_branch)
    if branch is None:
        raise RuntimeError(f"No existe branch '{settings.seed_demo_branch_code}'.")

    stmt_user = select(User).where(User.email == settings.seed_admin_email)
    actor = db.scalar(stmt_user)
    if actor is None:
        raise RuntimeError(f"No existe usuario '{settings.seed_admin_email}'.")

    return LinkContext(tenant=tenant, branch=branch, actor_user_id=actor.id)


def _print_summary(label: str, summary: LinkSummary) -> None:
    print(
        f"[{label}] creados={summary.created} actualizados={summary.updated} "
        f"omitidos={summary.skipped} errores={summary.errors}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Enlaza datos legacy (ERP-SYSTUTOR.API) con OSS (clientes, productos, almacenes). "
            "Stock NO se enlaza: legacy es dueño del stock (decision de desacople)."
        )
    )
    parser.add_argument("--all", action="store_true", help="sincronizar todos los dominios")
    parser.add_argument("--clientes", action="store_true")
    parser.add_argument("--productos", action="store_true")
    parser.add_argument("--almacenes", action="store_true")
    args = parser.parse_args()

    if not any([args.all, args.clientes, args.productos, args.almacenes]):
        parser.print_help()
        return 1

    settings = get_settings()
    if not settings.legacy_api_base_url or not settings.legacy_api_token:
        print("Falta SYSTUTOR_LEGACY_API_BASE_URL o SYSTUTOR_LEGACY_API_TOKEN en .env")
        return 1

    client = LegacyApiClient(settings.legacy_api_base_url, settings.legacy_api_token)
    session_factory = build_session_factory(settings)

    with session_factory() as db:
        ctx = _resolve_context(db, settings)
        print(f"Tenant: {ctx.tenant.name} ({ctx.tenant.id})")

        if args.all or args.almacenes:
            almacenes = asyncio.run(client.get_almacenes())
            summary = link_almacenes(db, almacenes, ctx)
            _print_summary("almacenes", summary)

        if args.all or args.clientes:
            clientes = asyncio.run(client.get_clientes())
            summary = link_clientes(db, clientes, ctx, client)
            _print_summary("clientes", summary)

        if args.all or args.productos:
            productos = asyncio.run(client.get_productos())
            summary = link_productos(db, productos, ctx, client)
            _print_summary("productos", summary)

    print("Link legacy completado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
