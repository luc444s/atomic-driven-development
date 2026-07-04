from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.config import Settings
from apps.api.app.core.database import Base, build_engine, build_session_factory
from apps.api.app.main import create_app

PROJECT_ROOT = Path(__file__).resolve().parents[3]

_SHOULD_SKIP = os.environ.get("SYSTUTOR_PG_TEST", "0") not in ("1", "true", "yes")

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(
        _SHOULD_SKIP,
        reason="Requiere PostgreSQL. Usar SYSTUTOR_PG_TEST=1 para activar",
    ),
]


def _pg_settings(tmp_path: Path) -> Settings:
    return Settings(
        app_name="SYSTUTOR OSS Postgres Test",
        env="test",
        debug=True,
        version="0.2.0-test",
        api_prefix="/api/v1",
        log_level="ERROR",
        database_url="postgresql+psycopg://postgres:postgres@localhost:5432/systutor_test",
        redis_url="redis://localhost:6379/15",
        outbox_dispatch_batch_size=25,
        outbox_max_retries=2,
        jwt_secret_key="test-secret-key",
        jwt_access_token_ttl_minutes=30,
        plugins_dir=PROJECT_ROOT / "plugins",
        seed_demo_tenant_name="Demo Tenant",
        seed_demo_tenant_slug="demo",
        seed_demo_branch_name="Main Branch",
        seed_demo_branch_code="MAIN",
        seed_admin_email="admin@example.com",
        seed_admin_password="ChangeMe123!",
        seed_admin_full_name="System Admin",
    )


@pytest.fixture()
def pg_engine(tmp_path: Path) -> Any:
    settings = _pg_settings(tmp_path)
    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        engine.dispose()


@pytest.fixture()
def pg_app(tmp_path: Path, pg_engine: Engine) -> Any:
    settings = _pg_settings(tmp_path)
    app = create_app(settings)
    app.state.session_factory = build_session_factory(settings)
    return app


def _setup_stock_env_pg(app: Any) -> dict[str, str]:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
        db.commit()

    from apps.api.app.api.v1.core.common import CoreActionContext
    from apps.api.app.api.v1.core.services.plugins import set_core_plugin_enabled
    from apps.api.app.kernel.plugins.persistent import sync_plugin_registry_state

    for plugin_id in ("crm", "logistics", "productos", "stock"):
        with app.state.session_factory() as db:
            app.state.plugin_registry.discover()
            sync_plugin_registry_state(db, registry=app.state.plugin_registry)
            set_core_plugin_enabled(
                db,
                registry=app.state.plugin_registry,
                plugin_id=plugin_id,
                context_builder=app.state.plugin_runtime.context_builder,
                is_enabled=True,
                action_context=CoreActionContext(
                    tenant_id=seeded_demo["tenant_id"],
                    branch_id=seeded_demo["branch_id"],
                    actor_user_id=seeded_demo["user_id"],
                    correlation_id=f"test-enable-{plugin_id}",
                    request_id=f"test-enable-{plugin_id}",
                ),
            )
            db.commit()

    from apps.api.app.core.lifecycle import bootstrap_app_state
    bootstrap_app_state(app, app.state.settings)
    return seeded_demo


def _login(client: TestClient) -> dict[str, str]:
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_product(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    cat = client.post(
        "/api/v1/plugins/productos/catalog/categories",
        headers=headers,
        json={"code": "ENERGIA", "name": "Energia", "description": ""},
    ).json()
    line = client.post(
        "/api/v1/plugins/productos/catalog/lines",
        headers=headers,
        json={"code": "GASES", "name": "Gases", "category_id": cat["id"]},
    ).json()
    subline = client.post(
        "/api/v1/plugins/productos/catalog/subline",
        headers=headers,
        json={"code": "GLP", "name": "GLP", "line_id": line["id"]},
    ).json()
    brand = client.post(
        "/api/v1/plugins/productos/catalog/brands",
        headers=headers,
        json={"code": "GENERICA", "name": "Generica"},
    ).json()
    unit = client.post(
        "/api/v1/plugins/productos/catalog/units",
        headers=headers,
        json={"code": "KG", "name": "Kilogramo", "equivalencia": 1, "kg_factor": 1},
    ).json()
    subcat = client.post(
        "/api/v1/plugins/productos/catalog/subcategories",
        headers=headers,
        json={"code": "GAS", "name": "Gas"},
    ).json()
    resp = client.post(
        "/api/v1/plugins/productos/products",
        headers=headers,
        json={
            "sku": "GLP10",
            "name": "GLP 10kg",
            "short_description": "GLP10",
            "line_id": line["id"],
            "subline_id": subline["id"],
            "brand_id": brand["id"],
            "unit_id": unit["id"],
            "box_unit_id": unit["id"],
            "qty_per_box": 1,
            "subcategory_id": subcat["id"],
            "status_code": "ACTIVO",
            "condition_code": "GAS",
            "weight_kg": 10,
            "content_m3": 0.1,
            "country_code": "PE",
            "delivery_time": "24h",
            "is_service": False,
            "is_active": True,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def _create_warehouse(
    client: TestClient, headers: dict[str, str], code: str, name: str
) -> dict[str, Any]:
    resp = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"code": code, "name": name},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── helpers for service-level concurrency ────────────────────────────────


def _make_ctx(user_id: str, tenant_id: str) -> Any:
    from plugins.stock.backend.common import StockActionContext

    return StockActionContext(
        tenant_id=tenant_id,
        branch_id=None,
        actor_user_id=user_id,
        correlation_id="concurrency-test",
        request_id="concurrency-test",
    )


def _do_adjust(
    session_factory: Any,
    tenant_id: str,
    product_id: str,
    warehouse_id: str,
    quantity: float,
    user_id: str,
    results: list,
    index: int,
) -> None:
    from plugins.stock.backend.services.operations import adjust_stock

    try:
        with session_factory() as db:
            adjust_stock(
                db=db,
                tenant_id=tenant_id,
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=quantity,
                reason=f"concurrent-test-{index}",
                idempotency_key=None,
                action_context=_make_ctx(user_id, tenant_id),
            )
            db.commit()
        results[index] = ("ok", None)
    except Exception as e:
        results[index] = ("error", str(e))


# ── concurrency tests ────────────────────────────────────────────────────


def test_concurrent_adjustments_same_product(pg_app: Any) -> None:
    """10 threads adjust +1 on the same product+warehouse. Final must be 10."""
    seeded = _setup_stock_env_pg(pg_app)
    session_factory = pg_app.state.session_factory
    tenant_id = seeded["tenant_id"]
    user_id = seeded["user_id"]

    with TestClient(pg_app) as client:
        headers = _login(client)
        warehouse = _create_warehouse(client, headers, code="PGC01", name="PG Concurrency 1")
        product = _create_product(client, headers)

    warehouse_id = warehouse["id"]
    product_id = product["id"]
    n_threads = 10
    results: list = [None] * n_threads

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futs = [
            pool.submit(
                _do_adjust, session_factory, tenant_id, product_id,
                warehouse_id, 1.0, user_id, results, i,
            )
            for i in range(n_threads)
        ]
        wait(futs)

    errors = [r for r in results if r[0] == "error"]
    assert not errors, f"{len(errors)} threads fallaron: {errors}"

    from plugins.stock.backend.models import StockBalance

    with session_factory() as db:
        balance = (
            db.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product_id,
                StockBalance.warehouse_id == warehouse_id,
            )
            .first()
        )

    assert balance is not None
    assert balance.quantity == 10.0, f"Esperado 10.0, obtenido {balance.quantity}"


def test_concurrent_adjustments_mixed_sign(pg_app: Any) -> None:
    """5 threads +1, 5 threads -1 on same balance. Final >= 0."""
    seeded = _setup_stock_env_pg(pg_app)
    session_factory = pg_app.state.session_factory
    tenant_id = seeded["tenant_id"]
    user_id = seeded["user_id"]

    with TestClient(pg_app) as client:
        headers = _login(client)
        warehouse = _create_warehouse(client, headers, code="PGC02", name="PG Concurrency 2")
        product = _create_product(client, headers)

    warehouse_id = warehouse["id"]
    product_id = product["id"]

    with session_factory() as db:
        from plugins.stock.backend.services.operations import adjust_stock

        adjust_stock(
            db=db, tenant_id=tenant_id, product_id=product_id,
            warehouse_id=warehouse_id, quantity=5.0,
            reason="seed", idempotency_key="seed-mixed",
            action_context=_make_ctx(user_id, tenant_id),
        )
        db.commit()

    n_threads = 10
    results: list = [None] * n_threads

    def _do_adjust_sign(
        session_factory: Any, tenant_id: str, product_id: str, warehouse_id: str,
        sign: float, user_id: str, results: list, index: int,
    ) -> None:
        from plugins.stock.backend.services.operations import adjust_stock

        try:
            with session_factory() as db:
                adjust_stock(
                    db=db, tenant_id=tenant_id, product_id=product_id,
                    warehouse_id=warehouse_id, quantity=sign,
                    reason=f"mixed-{index}", idempotency_key=None,
                    action_context=_make_ctx(user_id, tenant_id),
                )
                db.commit()
            results[index] = ("ok", None)
        except Exception as e:
            results[index] = ("error", str(e))

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futs = [
            pool.submit(
                _do_adjust_sign, session_factory, tenant_id, product_id,
                warehouse_id, 1.0 if i < 5 else -1.0, user_id, results, i,
            )
            for i in range(n_threads)
        ]
        wait(futs)

    errors = [r for r in results if r[0] == "error"]
    allowed = [r for r in errors if "insuficiente" in r[1].lower()]
    unexpected = [r for r in errors if r not in allowed]
    assert not unexpected, f"Errores inesperados: {unexpected}"

    from plugins.stock.backend.models import StockBalance

    with session_factory() as db:
        balance = (
            db.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product_id,
                StockBalance.warehouse_id == warehouse_id,
            )
            .first()
        )

    if balance is not None:
        assert balance.quantity >= 0, f"Balance negativo: {balance.quantity}"


def test_concurrent_transfers_from_same_warehouse(pg_app: Any) -> None:
    """5 threads transfer 10 units each from WH-A to different WHs. Origin must end at 50."""
    seeded = _setup_stock_env_pg(pg_app)
    session_factory = pg_app.state.session_factory
    tenant_id = seeded["tenant_id"]
    user_id = seeded["user_id"]

    with TestClient(pg_app) as client:
        headers = _login(client)
        origin = _create_warehouse(client, headers, code="PGTRORIG", name="PG Transfer Origin")
        product = _create_product(client, headers)
        dest_ids = [
            _create_warehouse(client, headers, code=f"PGTRD{i}", name=f"PG Dest {i}")
            for i in range(5)
        ]

    origin_id = origin["id"]
    product_id = product["id"]
    dest_ids = [d["id"] for d in dest_ids]

    from plugins.stock.backend.services.operations import adjust_stock

    with session_factory() as db:
        adjust_stock(
            db=db, tenant_id=tenant_id, product_id=product_id,
            warehouse_id=origin_id, quantity=100.0,
            reason="seed transfers", idempotency_key="seed-transfers",
            action_context=_make_ctx(user_id, tenant_id),
        )
        db.commit()

    results: list = [None] * 5

    def _do_transfer(
        session_factory: Any, tenant_id: str, product_id: str,
        from_wh: str, to_wh: str, qty: float, user_id: str,
        results: list, index: int,
    ) -> None:
        from plugins.stock.backend.services.operations import transfer_stock

        try:
            with session_factory() as db:
                transfer_stock(
                    db=db, tenant_id=tenant_id, product_id=product_id,
                    from_warehouse_id=from_wh, to_warehouse_id=to_wh,
                    quantity=qty, notes=f"ct-{index}", idempotency_key=None,
                    action_context=_make_ctx(user_id, tenant_id),
                )
                db.commit()
            results[index] = ("ok", None)
        except Exception as e:
            results[index] = ("error", str(e))

    with ThreadPoolExecutor(max_workers=5) as pool:
        futs = [
            pool.submit(
                _do_transfer, session_factory, tenant_id, product_id,
                origin_id, dest_id, 10.0, user_id, results, i,
            )
            for i, dest_id in enumerate(dest_ids)
        ]
        wait(futs)

    errors = [r for r in results if r[0] == "error"]
    assert not errors, f"{len(errors)} transfers fallaron: {errors}"

    from plugins.stock.backend.models import StockBalance

    with session_factory() as db:
        origin_bal = (
            db.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product_id,
                StockBalance.warehouse_id == origin_id,
            )
            .first()
        )
        dest_bals = [
            db.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product_id,
                StockBalance.warehouse_id == did,
            )
            .first()
            for did in dest_ids
        ]

    assert origin_bal is not None
    assert origin_bal.quantity == 50.0, f"Origin tiene {origin_bal.quantity}, esperado 50"
    for i, b in enumerate(dest_bals):
        assert b is not None, f"destino {i} sin balance"
        assert b.quantity == 10.0, f"Destino {i} tiene {b.quantity}, esperado 10"


def test_concurrent_adjust_lost_update_detection(pg_app: Any) -> None:
    """20 concurrent adjusts on same balance. With FOR UPDATE, final=20."""
    seeded = _setup_stock_env_pg(pg_app)
    session_factory = pg_app.state.session_factory
    tenant_id = seeded["tenant_id"]
    user_id = seeded["user_id"]

    with TestClient(pg_app) as client:
        headers = _login(client)
        warehouse = _create_warehouse(client, headers, code="PGLU01", name="PG Lost Update")
        product = _create_product(client, headers)

    warehouse_id = warehouse["id"]
    product_id = product["id"]
    n_threads = 20
    results: list = [None] * n_threads

    with ThreadPoolExecutor(max_workers=n_threads) as pool:
        futs = [
            pool.submit(
                _do_adjust, session_factory, tenant_id, product_id,
                warehouse_id, 1.0, user_id, results, i,
            )
            for i in range(n_threads)
        ]
        wait(futs)

    errors = [r for r in results if r[0] == "error"]
    assert not errors, f"{len(errors)} threads fallaron: {errors}"

    from plugins.stock.backend.models import StockBalance

    with session_factory() as db:
        balance = (
            db.query(StockBalance)
            .filter(
                StockBalance.tenant_id == tenant_id,
                StockBalance.product_id == product_id,
                StockBalance.warehouse_id == warehouse_id,
            )
            .first()
        )

    assert balance is not None
    assert balance.quantity == float(n_threads), (
        f"Lost update! Esperado {n_threads}, obtenido {balance.quantity}. "
        "SELECT FOR UPDATE no funciona correctamente."
    )


def test_lock_balance_row_creates_and_reuses(pg_app: Any) -> None:
    """_lock_balance_row creates a zero balance row and reuses it."""
    seeded = _setup_stock_env_pg(pg_app)
    session_factory = pg_app.state.session_factory
    tenant_id = seeded["tenant_id"]
    user_id = seeded["user_id"]

    with TestClient(pg_app) as client:
        headers = _login(client)
        warehouse = _create_warehouse(client, headers, code="PGLC01", name="PG Lock")
        product = _create_product(client, headers)

    from plugins.stock.backend.services.operations import _lock_balance_row

    warehouse_id = warehouse["id"]
    product_id = product["id"]

    with session_factory() as db:
        b1 = _lock_balance_row(
            db, tenant_id=tenant_id, product_id=product_id,
            warehouse_id=warehouse_id, actor_user_id=user_id,
        )
        assert b1 is not None
        assert b1.quantity == 0.0
        b1_id = b1.id

        b2 = _lock_balance_row(
            db, tenant_id=tenant_id, product_id=product_id,
            warehouse_id=warehouse_id, actor_user_id=user_id,
        )
        assert b2.id == b1_id
        db.commit()

    with session_factory() as db:
        from plugins.stock.backend.models import StockBalance
        row = db.query(StockBalance).filter(
            StockBalance.tenant_id == tenant_id,
            StockBalance.product_id == product_id,
            StockBalance.warehouse_id == warehouse_id,
        ).first()
        assert row is not None
        assert row.id == b1_id
