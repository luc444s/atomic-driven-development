from __future__ import annotations

from plugins.tms.backend import ports
from plugins.tms.backend.services.drivers import driver_email, ensure_driver_user
from plugins.tms.backend.services.vehicles import SEED_PLATES, ensure_vehicle

DRIVERS = [
    {"dni": "46209157", "nombre": "AYRTOM SALDARRIAGA SALDARRIAGA"},
    {"dni": "44973574", "nombre": "LEON CALDERON HIRVING BENGAMIN YSAIT"},
    {"dni": "48429083", "nombre": "REYES POLO GERSON JHOAO"},
]


def main() -> int:
    p = ports.get_ports()
    settings = p.get_settings()
    session_factory = p.session_factory()

    with session_factory() as db:
        ctx = p.resolve_sync_context(db)
        if ctx.tenant is None:
            print(f"No existe tenant demo. Correr seed_demo.")
            return 1
        tenant_id = ctx.tenant.id
        branch_id = ctx.branch.id if ctx.branch else None

        for d in DRIVERS:
            user_id = ensure_driver_user(
                db,
                tenant_id=tenant_id,
                branch_id=branch_id,
                dni=d["dni"],
                full_name=d["nombre"],
            )
            print(
                f"driver   {d['dni']}  {d['nombre']}  ({driver_email(d['dni'])})  -> {user_id}"
            )

        for placa in SEED_PLATES:
            vehicle_id = ensure_vehicle(db, tenant_id=tenant_id, plate=placa)
            print(f"vehiculo {placa}  ->  {vehicle_id}")

        db.commit()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
