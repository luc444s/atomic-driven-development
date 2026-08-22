import asyncio

from sqlalchemy import select

from plugins.tms.backend import ports
from plugins.tms.backend.legacy.client import LegacyApiClient
from plugins.tms.backend.services.link_legacy import (
    LinkContext,
    link_almacenes,
    link_clientes,
    link_productos,
)
from plugins.tms.backend.services.vehicles import SEED_PLATES, ensure_vehicle


def main() -> int:
    p = ports.get_ports()
    settings = p.get_settings()
    session_factory = p.session_factory()
    client = LegacyApiClient(settings.legacy_api_base_url, settings.legacy_api_token)

    with session_factory() as db:
        ctx_view = p.resolve_sync_context(db)
        if ctx_view.tenant is None:
            print("Tenant demo no encontrado")
            return 1
        ctx = LinkContext(
            tenant_id=ctx_view.tenant.id,
            branch_id=ctx_view.branch.id if ctx_view.branch else "",
            actor_user_id=ctx_view.actor_user_id or "",
        )

        clientes = asyncio.run(client.get_clientes())
        s1 = link_clientes(db, clientes, ctx, client)
        print(f"clientes -> {s1}")

        productos = asyncio.run(client.get_productos())
        s2 = link_productos(db, productos, ctx, client)
        print(f"productos -> {s2}")

        almacenes = asyncio.run(client.get_almacenes())
        s3 = link_almacenes(db, almacenes, ctx)
        print(f"almacenes -> {s3}")

        for plate in SEED_PLATES:
            vehicle_id = ensure_vehicle(db, tenant_id=ctx.tenant_id, plate=plate)
            print(f"vehiculo {plate} -> {vehicle_id}")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
