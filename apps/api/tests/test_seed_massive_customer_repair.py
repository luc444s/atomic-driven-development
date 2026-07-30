from __future__ import annotations

from sqlalchemy import select

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.commands.seed_massive import repair_seed_customer_possession_orphans
from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_customer,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
)
from plugins.crm.backend.models import CrmCustomer
from plugins.logistics.backend.models import (
    LogisticsCustomerCylinderLedger,
    LogisticsCylinder,
    LogisticsCylinderOwnership,
)


def _create_orphan_customer_cylinder(client, app, *, state: str) -> tuple[dict[str, str], str, str]:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db,
            app.state.settings,
            app.state.plugin_runtime.list_results(),
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    headers = auth_headers(client)
    sku = "ORPH-EV" if state == "EN_CLIENTE_VACIO" else "ORPH-EL"
    create_customer(
        client,
        headers,
        name=f"Cliente {sku}",
        document_number="20100070970",
    )
    product = create_product(
        client,
        headers,
        sku=sku,
        name=f"Producto {state}",
    )

    with app.state.session_factory() as db:
        product_id = product["id"]
        cylinder = LogisticsCylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial=f"ORPH-{state}",
            product_id=product_id,
            condition="CILPRO",
            current_state=state,
            is_active=True,
        )
        db.add(cylinder)
        db.commit()
        return seeded_demo, cylinder.id, product_id


def test_seed_customer_repair_is_idempotent(client, app) -> None:
    seeded_demo, cylinder_id, _product_id = _create_orphan_customer_cylinder(
        client,
        app,
        state="EN_CLIENTE_VACIO",
    )

    with app.state.session_factory() as db:
        customers = list(
            db.scalars(
                select(CrmCustomer)
                .where(CrmCustomer.tenant_id == seeded_demo["tenant_id"])
                .order_by(CrmCustomer.created_at.asc())
            ).all()
        )
        stats_first = repair_seed_customer_possession_orphans(
            db,
            seeded_demo["tenant_id"],
            seeded_demo["user_id"],
            customers,
            env="test",
            allow_fallback=False,
        )
        assert stats_first["resolved_by_fallback"] == 1

    with app.state.session_factory() as db:
        customers = list(
            db.scalars(
                select(CrmCustomer)
                .where(CrmCustomer.tenant_id == seeded_demo["tenant_id"])
                .order_by(CrmCustomer.created_at.asc())
            ).all()
        )
        stats_second = repair_seed_customer_possession_orphans(
            db,
            seeded_demo["tenant_id"],
            seeded_demo["user_id"],
            customers,
            env="test",
            allow_fallback=False,
        )
        assert stats_second["skipped_repaired"] >= 1
        ownerships = list(
            db.scalars(
                select(LogisticsCylinderOwnership).where(
                    LogisticsCylinderOwnership.cylinder_id == cylinder_id
                )
            ).all()
        )
        ledgers = list(
            db.scalars(
                select(LogisticsCustomerCylinderLedger).where(
                    LogisticsCustomerCylinderLedger.cylinder_id == cylinder_id,
                    LogisticsCustomerCylinderLedger.source_type == "SEED_ORPHAN_REPAIR",
                )
            ).all()
        )
        assert len(ownerships) == 1
        assert len(ledgers) == 1


def test_seed_customer_repair_blocks_fallback_in_production(client, app) -> None:
    seeded_demo, cylinder_id, _product_id = _create_orphan_customer_cylinder(
        client,
        app,
        state="EN_CLIENTE_LLENO",
    )

    with app.state.session_factory() as db:
        customers = list(
            db.scalars(
                select(CrmCustomer)
                .where(CrmCustomer.tenant_id == seeded_demo["tenant_id"])
                .order_by(CrmCustomer.created_at.asc())
            ).all()
        )
        stats = repair_seed_customer_possession_orphans(
            db,
            seeded_demo["tenant_id"],
            seeded_demo["user_id"],
            customers,
            env="production",
            allow_fallback=False,
        )
        assert stats["not_repairable"] == 1
        ownership = db.scalar(
            select(LogisticsCylinderOwnership).where(
                LogisticsCylinderOwnership.cylinder_id == cylinder_id
            )
        )
        assert ownership is None
