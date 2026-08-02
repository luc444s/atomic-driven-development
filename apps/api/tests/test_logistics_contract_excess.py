# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
)
from plugins.logistics.backend.models import (
    LogisticsContractExcessTracking,
    LogisticsCylinder,
    LogisticsCylinderContract,
    LogisticsCylinderOwnership,
    LogisticsCylinderStateLog,
)
from plugins.logistics.backend.services.contracts_excess import sweep_contract_excess


def _build_cylinder(
    *, tenant_id: str, branch_id: str, serial: str, product_id: str, state: str
) -> LogisticsCylinder:
    return LogisticsCylinder(
        tenant_id=tenant_id,
        branch_id=branch_id,
        serial=serial,
        product_id=product_id,
        condition="CILPRO",
        current_state=state,
    )


def _create_customer(
    client: TestClient, headers: dict[str, str], *, name: str, document_number: str
) -> dict[str, str]:
    response = client.post(
        "/api/v1/plugins/crm/customers",
        headers=headers,
        json={
            "legal_name": name,
            "document_type_code": "DNI",
            "document_number": document_number,
            "country_code": "PER",
            "billing_type": "por_operacion",
            "is_exempt": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _setup_contract(
    db,
    *,
    seeded_demo: dict[str, str],
    customer_id: str,
    product_id: str,
    quantity: int,
    wait_days: int = 3,
    auto_renew: bool = True,
    warehouse_id: str | None = None,
) -> LogisticsCylinderContract:
    contract = LogisticsCylinderContract(
        tenant_id=seeded_demo["tenant_id"],
        branch_id=seeded_demo["branch_id"],
        warehouse_id=warehouse_id,
        contract_type="ANNUAL",
        status="ACTIVE",
        customer_id=customer_id,
        customer_snapshot={"legal_name": customer_id},
        start_date=datetime.now(UTC).date(),
        renewal_type="MANUAL",
        cylinder_type_id=product_id,
        cylinder_condition="CILPRO",
        quantity=quantity,
        unit_price=10,
        excess_wait_days=wait_days,
        auto_renew_on_excess=auto_renew,
        created_by=seeded_demo["user_id"],
    )
    db.add(contract)
    db.flush()
    return contract


def _put_cylinders_at_customer(
    db,
    *,
    seeded_demo: dict[str, str],
    customer_id: str,
    product_id: str,
    serials: list[str],
    days_ago: int = 1,
) -> None:
    now = datetime.now(UTC)
    for serial in serials:
        cylinder = _build_cylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial=serial,
            product_id=product_id,
            state="EN_CLIENTE_LLENO",
        )
        db.add(cylinder)
        db.flush()
        db.add(
            LogisticsCylinderOwnership(
                cylinder_id=cylinder.id,
                customer_id=customer_id,
                customer_name=customer_id,
                condition="CILPRO",
                created_by=seeded_demo["user_id"],
                change_date=now - timedelta(days=days_ago),
            )
        )
        db.add(
            LogisticsCylinderStateLog(
                tenant_id=seeded_demo["tenant_id"],
                cylinder_id=cylinder.id,
                to_state="EN_CLIENTE_LLENO",
                changed_by=seeded_demo["user_id"],
                created_at=now - timedelta(days=days_ago),
            )
        )
    db.flush()


def test_excess_detection_creates_tracking_and_auto_contract_after_wait(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = _create_customer(
            client, headers, name="Cliente Motor SAC", document_number="11111111"
        )
        product = create_product(client, headers, sku="BOMB-EX-1", name="Bombona Exceso")

        warehouse = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Almacen Motor", "code": "AMOT", "address": "Av. Motor 1"},
        ).json()

    with app.state.session_factory() as db:
        contract = _setup_contract(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=product["id"],
            quantity=2,
            wait_days=1,
            warehouse_id=warehouse["id"],
        )
        # 3 cilindros en cliente: exceso = 1
        _put_cylinders_at_customer(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=product["id"],
            serials=["EX-001", "EX-002", "EX-003"],
        )
        db.commit()

        # Primer sweep: exceso detectado, tracking ACTIVE, sin contrato (wait 1 día no vencido)
        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC)
        )
        assert result["trackings_created"] == 1
        assert result["contracts_created"] == 0

        tracking = db.scalar(
            select(LogisticsContractExcessTracking).where(
                LogisticsContractExcessTracking.customer_id == customer["id"]
            )
        )
        assert tracking is not None
        assert tracking.status == "ACTIVE"
        assert tracking.excess_qty == 1
        assert tracking.base_unit_price == 10
        assert tracking.base_contract_type == "ANNUAL"

        # Segundo sweep (mismo exceso): no duplica tracking
        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC)
        )
        assert result["trackings_created"] == 0
        assert result["contracts_created"] == 0

        # El exceso persiste más del wait_days: auto-crea contrato
        later = tracking.first_detected_at + timedelta(days=2)
        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=later
        )
        assert result["contracts_created"] == 1

        db.refresh(tracking)
        assert tracking.status == "CONTRACT_CREATED"
        assert tracking.created_contract_id is not None
        created = db.get(LogisticsCylinderContract, tracking.created_contract_id)
        assert created is not None
        assert created.quantity == 1
        assert created.unit_price == 10
        assert created.contract_type == "ANNUAL"
        assert created.source_contract_id == contract.id
        assert created.excess_wait_days == 1

        # Idempotencia: un nuevo sweep no crea otro contrato
        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=later + timedelta(hours=1)
        )
        assert result["contracts_created"] == 0

        db.rollback()


def test_excess_global_is_capped_by_contract_limit(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = _create_customer(
            client, headers, name="Cliente Cupo SAC", document_number="22222222"
        )
        gas_a = create_product(client, headers, sku="BOMB-A-1", name="Gas A")
        gas_b = create_product(client, headers, sku="BOMB-B-1", name="Gas B")
        warehouse = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Almacen Cupo", "code": "ACUP", "address": "Av. Cupo 1"},
        ).json()

    with app.state.session_factory() as db:
        # Cupo: 5 de A. Posesión: 5 de A + 3 de B (sin contrato) → exceso global 3, todo de B.
        contract_a = _setup_contract(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=gas_a["id"],
            quantity=5,
            wait_days=0,
            warehouse_id=warehouse["id"],
        )
        _put_cylinders_at_customer(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=gas_a["id"],
            serials=["CP-A1", "CP-A2", "CP-A3", "CP-A4", "CP-A5"],
        )
        _put_cylinders_at_customer(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=gas_b["id"],
            serials=["CP-B1", "CP-B2", "CP-B3"],
        )
        db.commit()

        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC)
        )
        assert result["contracts_created"] == 0  # primer sweep: solo detecta
        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC)
        )
        assert result["contracts_created"] == 1  # wait_days=0: auto-crea en el segundo sweep

        tracking = db.scalar(
            select(LogisticsContractExcessTracking).where(
                LogisticsContractExcessTracking.customer_id == customer["id"],
                LogisticsContractExcessTracking.cylinder_type_id == gas_b["id"],
            )
        )
        assert tracking is not None
        assert tracking.excess_qty == 3  # el exceso global (3) se asigna al tipo sin contrato
        assert tracking.created_contract_id is not None
        created = db.get(LogisticsCylinderContract, tracking.created_contract_id)
        assert created is not None
        assert created.cylinder_type_id == gas_b["id"]  # contrato del tipo excedente
        assert created.quantity == 3
        assert created.source_contract_id == contract_a.id  # hereda del contrato del cupo

        db.rollback()


def test_excess_resolves_when_possession_normalizes(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = _create_customer(
            client, headers, name="Cliente Resolve SAC", document_number="33333333"
        )
        product = create_product(client, headers, sku="BOMB-R-1", name="Bombona Resolve")

    with app.state.session_factory() as db:
        _setup_contract(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=product["id"],
            quantity=2,
            wait_days=1,
        )
        _put_cylinders_at_customer(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=product["id"],
            serials=["RS-001", "RS-002", "RS-003"],
        )
        db.commit()

        sweep_contract_excess(db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC))
        tracking = db.scalar(
            select(LogisticsContractExcessTracking).where(
                LogisticsContractExcessTracking.customer_id == customer["id"]
            )
        )
        assert tracking is not None and tracking.status == "ACTIVE"

        # El cilindro vuelve al almacén: posesión normalizada (2 = límite)
        cylinder = db.scalar(
            select(LogisticsCylinder).where(
                LogisticsCylinder.serial == "RS-003"
            )
        )
        cylinder.current_state = "EN_ALMACEN_VACIO"
        db.add(cylinder)
        db.flush()
        db.add(
            LogisticsCylinderStateLog(
                tenant_id=seeded_demo["tenant_id"],
                cylinder_id=cylinder.id,
                to_state="EN_ALMACEN_VACIO",
                changed_by=seeded_demo["user_id"],
                created_at=datetime.now(UTC),
            )
        )
        db.commit()

        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC)
        )
        assert result["trackings_resolved"] == 1
        db.refresh(tracking)
        assert tracking.status == "RESOLVED"
        assert tracking.resolved_reason == "posesion normalizada"

        db.rollback()


def test_excess_without_contract_does_not_auto_create(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = _create_customer(
            client, headers, name="Cliente Sin Cupo SAC", document_number="44444444"
        )
        product = create_product(client, headers, sku="BOMB-N-1", name="Bombona Sin Cupo")

    with app.state.session_factory() as db:
        # Sin contratos ACTIVOS: el sweep no crea tracking ni contrato
        _put_cylinders_at_customer(
            db,
            seeded_demo=seeded_demo,
            customer_id=customer["id"],
            product_id=product["id"],
            serials=["NC-001"],
        )
        db.commit()

        result = sweep_contract_excess(
            db, tenant_id=seeded_demo["tenant_id"], now=datetime.now(UTC)
        )
        assert result["contracts_created"] == 0

        tracking = db.scalar(
            select(LogisticsContractExcessTracking).where(
                LogisticsContractExcessTracking.customer_id == customer["id"]
            )
        )
        assert tracking is None

        db.rollback()
