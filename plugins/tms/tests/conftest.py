from __future__ import annotations

from dataclasses import asdict

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from plugins.tms.backend.models import JornadaTMS, TmsBase
from plugins.tms.backend.ports import TmsPorts, set_ports


# ---------------------------------------------------------------------------
# Puertos falsos — el suite nunca toca systutor ni otros plugins
# ---------------------------------------------------------------------------


class FakeTmsState:
    def __init__(self) -> None:
        self.tenant_id = "t-1"
        self.branch_id = "b-1"
        self.actor_user_id = "u-1"
        self.warehouses: dict[str, str] = {}
        self.products: dict[int, str] = {}
        self.vehicles: dict[str, str] = {}  # placa normalizada -> id
        self.drivers: dict[str, str] = {}  # dni -> user_id
        self.sessions: list[dict] = []
        self.plans: dict[str, list[dict]] = {}

    # -- sync jornadas vivas -------------------------------------------------

    def ensure_driver(self, db, *, tenant_id, branch_id, dni, full_name) -> str:
        if dni not in self.drivers:
            self.drivers[dni] = f"drv-{len(self.drivers) + 1}"
        return self.drivers[dni]

    def ensure_vehicle(self, db, *, tenant_id, plate, vehicle_type=None) -> str:
        key = plate.strip().upper().replace("-", "").replace("/", "")
        if key not in self.vehicles:
            self.vehicles[key] = f"veh-{len(self.vehicles) + 1}"
        return self.vehicles[key]

    def find_warehouse_id(self, db, *, tenant_id, code):
        return self.warehouses.get(code)

    def find_product_id_by_legacy(self, db, *, tenant_id, legacy_id):
        return self.products.get(legacy_id)

    def find_live_session_id(self, db, *, tenant_id, vehicle_id, driver_id, fecha):
        for s in self.sessions:
            if (
                s["vehicle_id"] == vehicle_id
                and s["driver_id"] == driver_id
                and s["fecha"] == fecha
            ):
                return s["id"]
        return None

    def create_live_session(self, db, spec) -> str:
        sid = f"ses-{len(self.sessions) + 1}"
        self.sessions.append(
            {
                "id": sid,
                "tenant_id": spec.tenant_id,
                "vehicle_id": spec.vehicle_id,
                "driver_id": spec.driver_id,
                "warehouse_id": spec.origin_warehouse_id,
                "branch_id": spec.branch_id,
                "actor_user_id": spec.actor_user_id,
                "fecha": spec.opened_at.date() if hasattr(spec.opened_at, "date") else spec.opened_at,
            }
        )
        return sid

    def upsert_load_plan_items(self, db, *, session_id, tenant_id, actor_user_id,
                               notes, items) -> bool:
        if not items:
            return False
        self.plans.setdefault(session_id, [])
        self.plans[session_id].append(
            {"notes": notes, "items": [asdict(i) for i in items]}
        )
        return True

    def reset(self) -> None:
        self.warehouses.clear()
        self.products.clear()
        self.vehicles.clear()
        self.drivers.clear()
        self.sessions.clear()
        self.plans.clear()

    # -- link legacy ---------------------------------------------------------

    def hash_secret(self, s: str) -> str:
        return f"hashed:{s}"


def _fake_ports(state: FakeTmsState) -> TmsPorts:
    def _noop(*args, **kwargs):
        return None

    def _none(*args, **kwargs):
        return None

    return TmsPorts(
        db_session_dependency=lambda: None,
        require_permission=lambda name: (lambda *a, **k: None),
        get_settings=lambda: type(
            "S",
            (),
            {
                "seed_demo_tenant_slug": state.tenant_id,
                "seed_demo_branch_code": state.branch_id,
                "seed_admin_email": state.actor_user_id,
                "legacy_api_base_url": "http://legacy.test/api",
                "legacy_api_token": "tok",
            },
        )(),
        session_factory=lambda: None,
        resolve_sync_context=lambda db: None,
        hash_secret=state.hash_secret,
        ensure_driver=state.ensure_driver,
        ensure_vehicle=state.ensure_vehicle,
        find_warehouse_id=state.find_warehouse_id,
        find_product_id_by_legacy=state.find_product_id_by_legacy,
        find_live_session_id=state.find_live_session_id,
        create_live_session=state.create_live_session,
        upsert_load_plan_items=state.upsert_load_plan_items,
        find_customer_by_doc=_none,
        find_customer_by_external=_none,
        create_customer=_noop,
        patch_customer=_noop,
        ensure_customer_address=_noop,
        set_fiscal_address=_noop,
        existing_product_by_legacy=_none,
        existing_product_by_sku=_none,
        used_skus=lambda db, *, tenant_id: set(),
        create_product=_noop,
        patch_product=_noop,
        ensure_product_line=_noop,
        ensure_product_unit=_noop,
        upsert_warehouse=_noop,
    )


_state = FakeTmsState()
set_ports(_fake_ports(_state))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tms_state() -> FakeTmsState:
    _state.reset()
    return _state


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    TmsBase.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def jornada_seq():
    counter = {"n": 5000}

    def next_cod() -> int:
        counter["n"] += 1
        return counter["n"]

    return next_cod


def make_jornada(db: Session, next_cod, estado: str = "pendiente") -> JornadaTMS:
    j = JornadaTMS(
        cod_movimiento_legacy=next_cod(),
        estado=estado,
        almacen=1,
        cod_cliente=4587,
        cliente="M.H. EIRL",
        tipo_transaccion="CONTADO",
        items="[]",
    )
    db.add(j)
    db.flush()
    return j
