from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
)
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderContract,
    LogisticsCylinderOwnership,
    LogisticsCylinderStateLog,
    LogisticsMovement,
    LogisticsMovementItem,
)


def _build_cylinder(
    *,
    tenant_id: str,
    branch_id: str,
    serial: str,
    product_id: str,
    condition: str,
    state: str,
) -> LogisticsCylinder:
    return LogisticsCylinder(
        tenant_id=tenant_id,
        branch_id=branch_id,
        serial=serial,
        product_id=product_id,
        condition=condition,
        current_state=state,
    )


def _create_customer(
    client: TestClient,
    headers: dict[str, str],
    *,
    name: str,
    document_number: str,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/plugins/crm/customers",
        headers=headers,
        json={
            "legal_name": name,
            "document_type_code": "DNI",
            "document_number": document_number,
            "country_code": "PE",
            "billing_type": "por_operacion",
            "is_exempt": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_customer_cylinder_summary_aggregates_movement_assignment_and_operational_state(
    app,
) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db,
            app.state.settings,
            app.state.plugin_runtime.list_results(),
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = _create_customer(
            client,
            headers,
            name="Cliente Summary SAC",
            document_number="12345678",
        )
        other_customer = _create_customer(
            client,
            headers,
            name="Otro Cliente SAC",
            document_number="87654321",
        )
        product = create_product(client, headers, sku="BOMB-27-SUM", name="Bombona 27kg")

        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Almacen Summary", "code": "ASUM", "address": "Av. Summary 100"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()

    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        contract_a = LogisticsCylinderContract(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            warehouse_id=warehouse["id"],
            contract_type="ANNUAL",
            status="ACTIVE",
            customer_id=customer["id"],
            customer_snapshot={"legal_name": customer["legal_name"]},
            start_date=now.date(),
            renewal_type="MANUAL",
            cylinder_type_id=product["id"],
            cylinder_condition="CILPRO",
            quantity=5,
            unit_price=10,
            created_by=seeded_demo["user_id"],
        )
        contract_b = LogisticsCylinderContract(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            warehouse_id=warehouse["id"],
            contract_type="MONTHLY",
            status="ACTIVE",
            customer_id=customer["id"],
            customer_snapshot={"legal_name": customer["legal_name"]},
            start_date=now.date(),
            renewal_type="MANUAL",
            cylinder_type_id=product["id"],
            cylinder_condition="CILPRO",
            quantity=2,
            unit_price=10,
            created_by=seeded_demo["user_id"],
        )
        db.add_all([contract_a, contract_b])
        db.flush()

        cylinder_at_customer = _build_cylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="SUM-001",
            product_id=product["id"],
            condition="CILPRO",
            state="EN_CLIENTE_LLENO",
        )
        cylinder_pipeline = _build_cylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="SUM-002",
            product_id=product["id"],
            condition="CILPRO",
            state="EN_RUTA",
        )
        cylinder_unknown = _build_cylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="SUM-003",
            product_id=product["id"],
            condition="CILPRO",
            state="EN_CLIENTE_VACIO",
        )
        db.add_all([cylinder_at_customer, cylinder_pipeline, cylinder_unknown])
        db.flush()

        db.add_all(
            [
                LogisticsCylinderStateLog(
                    tenant_id=seeded_demo["tenant_id"],
                    cylinder_id=cylinder_at_customer.id,
                    to_state="EN_CLIENTE_LLENO",
                    changed_by=seeded_demo["user_id"],
                    created_at=now - timedelta(days=1),
                ),
                LogisticsCylinderStateLog(
                    tenant_id=seeded_demo["tenant_id"],
                    cylinder_id=cylinder_pipeline.id,
                    to_state="EN_RUTA",
                    changed_by=seeded_demo["user_id"],
                    created_at=now - timedelta(days=1),
                ),
                LogisticsCylinderStateLog(
                    tenant_id=seeded_demo["tenant_id"],
                    cylinder_id=cylinder_unknown.id,
                    to_state="EN_CLIENTE_VACIO",
                    changed_by=seeded_demo["user_id"],
                    created_at=now - timedelta(days=1),
                ),
            ]
        )
        db.add_all(
            [
                LogisticsCylinderOwnership(
                    cylinder_id=cylinder_at_customer.id,
                    customer_id=customer["id"],
                    customer_name=customer["legal_name"],
                    condition="CILPRO",
                    created_by=seeded_demo["user_id"],
                    change_date=now - timedelta(days=1),
                ),
                LogisticsCylinderOwnership(
                    cylinder_id=cylinder_pipeline.id,
                    customer_id=customer["id"],
                    customer_name=customer["legal_name"],
                    condition="CILPRO",
                    created_by=seeded_demo["user_id"],
                    change_date=now - timedelta(days=1),
                ),
                LogisticsCylinderOwnership(
                    cylinder_id=cylinder_unknown.id,
                    customer_id=other_customer["id"],
                    customer_name=other_customer["legal_name"],
                    condition="CILPRO",
                    created_by=seeded_demo["user_id"],
                    change_date=now - timedelta(days=1),
                ),
            ]
        )

        movement = LogisticsMovement(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            movement_type="SC",
            customer_id=customer["id"],
            customer_name=customer["legal_name"],
            status="COMPLETADO",
            created_by=seeded_demo["user_id"],
            created_at=now - timedelta(days=2),
        )
        db.add(movement)
        db.flush()
        db.add_all(
            [
                LogisticsMovementItem(
                    movement_id=movement.id,
                    cylinder_id=cylinder_at_customer.id,
                    product_id=product["id"],
                    product_name=product["name"],
                    quantity_out=1,
                    quantity=1,
                ),
                LogisticsMovementItem(
                    movement_id=movement.id,
                    cylinder_id=cylinder_pipeline.id,
                    product_id=product["id"],
                    product_name=product["name"],
                    quantity_out=1,
                    quantity=1,
                ),
                LogisticsMovementItem(
                    movement_id=movement.id,
                    cylinder_id=cylinder_unknown.id,
                    product_id=product["id"],
                    product_name=product["name"],
                    quantity_out=1,
                    quantity=1,
                ),
                LogisticsMovementItem(
                    movement_id=movement.id,
                    product_id=product["id"],
                    product_name=product["name"],
                    quantity_out=1,
                    quantity=1,
                ),
            ]
        )
        db.commit()

    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get(
            f"/api/v1/plugins/logistics/customers/{customer['id']}/cylinders/summary",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        payload = response.json()

    assert payload["summary"]["contracted"] == 7
    assert payload["summary"]["assigned"] == 4
    assert payload["summary"]["at_customer"] == 1
    assert payload["summary"]["at_customer_unknown"] == 1
    assert payload["summary"]["pipeline"] == 1
    assert payload["summary"]["lost"] == 1
    assert payload["summary"]["deviation"] == -3
    assert payload["contract"]["active_contract_count"] == 2
    assert payload["by_product"][0]["pipeline"]["in_transit"] == 1
    severities = {item["category"]: item["severity"] for item in payload["alerts"]}
    assert severities["ownership_inconsistent"] == "CRITICAL"
    assert severities["shortage"] == "WARNING"
    assert severities["loss"] == "WARNING"
    assert severities["pipeline"] == "INFO"


def test_customer_cylinder_summary_returns_operational_reality_without_active_contract(
    app,
) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db,
            app.state.settings,
            app.state.plugin_runtime.list_results(),
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = _create_customer(
            client,
            headers,
            name="Cliente Sin Contrato SAC",
            document_number="23456789",
        )
        product = create_product(client, headers, sku="BOMB-10-SIN", name="Bombona 10kg")

    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        cylinder = _build_cylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="SIN-001",
            product_id=product["id"],
            condition="CILCLI",
            state="EN_CLIENTE_LLENO",
        )
        db.add(cylinder)
        db.flush()
        db.add(
            LogisticsCylinderStateLog(
                tenant_id=seeded_demo["tenant_id"],
                cylinder_id=cylinder.id,
                to_state="EN_CLIENTE_LLENO",
                changed_by=seeded_demo["user_id"],
                created_at=now - timedelta(days=1),
            )
        )
        db.add(
            LogisticsCylinderOwnership(
                cylinder_id=cylinder.id,
                customer_id=customer["id"],
                customer_name=customer["legal_name"],
                condition="CILCLI",
                created_by=seeded_demo["user_id"],
                change_date=now - timedelta(days=1),
            )
        )
        db.commit()

    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get(
            f"/api/v1/plugins/logistics/customers/{customer['id']}/cylinders/summary",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        payload = response.json()

    assert payload["summary"]["contracted"] == 0
    assert payload["summary"]["assigned"] == 0
    assert payload["summary"]["at_customer"] == 1
    categories = {item["category"] for item in payload["alerts"]}
    assert "missing_contract" in categories
    assert "transition" in categories
    assert "unassigned_at_customer" not in categories
