from __future__ import annotations

from sqlalchemy import select
from systutor.core.database import build_session_factory
from systutor.kernel.tenants.models import Branch, Tenant

from apps.api.app.config import get_settings
from plugins.tms.backend.services.drivers import ensure_driver_user
from plugins.tms.backend.services.vehicles import SEED_PLATES, ensure_vehicle

DRIVERS = [
    {"dni": "46209157", "nombre": "AYRTOM SALDARRIAGA SALDARRIAGA"},
    {"dni": "44973574", "nombre": "LEON CALDERON HIRVING BENGAMIN YSAIT"},
    {"dni": "48429083", "nombre": "REYES POLO GERSON JHOAO"},
]


def main() -> int:
    settings = get_settings()
    session_factory = build_session_factory(settings)

    with session_factory() as db:
        stmt = select(Tenant).where(Tenant.slug == settings.seed_demo_tenant_slug)
        tenant = db.scalar(stmt)
        if tenant is None:
            print(f"No existe tenant '{settings.seed_demo_tenant_slug}'. Correr seed_demo.")
            return 1

        stmt_branch = select(Branch).where(
            Branch.tenant_id == tenant.id,
            Branch.code == settings.seed_demo_branch_code,
        )
        branch = db.scalar(stmt_branch)

        for d in DRIVERS:
            user = ensure_driver_user(
                db,
                tenant=tenant,
                branch=branch,
                dni=d["dni"],
                full_name=d["nombre"],
            )
            print(f"driver   {d['dni']}  {user.full_name}  ({user.email})")

        for placa in SEED_PLATES:
            vehicle = ensure_vehicle(db, tenant=tenant, plate=placa, vehicle_type="CAMION")
            print(f"vehiculo {placa}  ->  {vehicle.id}")

        db.commit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())