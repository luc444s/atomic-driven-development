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
from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.models import (
    LogisticsCylinder,
    LogisticsCylinderContract,
    LogisticsCylinderOwnership,
    LogisticsCylinderStateLog,
    LogisticsMovement,
    LogisticsMovementItem,
    LogisticsVehicle,
    LogisticsVehicleSession,
)
from plugins.logistics.backend.services.cylinders import record_cylinder_event


def _build_cylinder(
    *,
    tenant_id: str,
    branch_id: str,
    serial: str,
    product_id: str,
    condition: str,
    state: str,
    session_id: str | None = None,
) -> LogisticsCylinder:
    return LogisticsCylinder(
        tenant_id=tenant_id,
        branch_id=branch_id,
        serial=serial,
        product_id=product_id,
        condition=condition,
        current_state=state,
        session_id=session_id,
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

        # CHECK ck_cylinder_transit_requires_session (migration 035): un cilindro
        # EN_RUTA exige session_id que referencie una lg_vehicle_sessions real.
        transit_vehicle = LogisticsVehicle(
            tenant_id=seeded_demo["tenant_id"],
            plate="SUM-TRK-1",
            warehouse_id=warehouse["id"],
        )
        db.add(transit_vehicle)
        db.flush()
        transit_session = LogisticsVehicleSession(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            vehicle_id=transit_vehicle.id,
            driver_id=seeded_demo["user_id"],
            origin_warehouse_id=warehouse["id"],
            mobile_warehouse_id=warehouse["id"],
            status="DRAFT",
            created_by=seeded_demo["user_id"],
            updated_by=seeded_demo["user_id"],
        )
        db.add(transit_session)
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
            session_id=transit_session.id,
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


def test_customer_cylinder_summary_exposes_traceable_customer_address(app) -> None:
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
            name="Cliente Direccion SAC",
            document_number="34567890",
        )
        product = create_product(client, headers, sku="BOMB-27-ADDR", name="Bombona 27kg Direccion")
        address_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer['id']}/addresses",
            headers=headers,
            json={
                "line1": "Av. Siempre Viva 742",
                "city": "Lima",
                "country_code": "PE",
                "address_type": "ENTREGA",
            },
        )
        assert address_response.status_code == 201, address_response.text
        address = address_response.json()

    now = datetime.now(UTC)
    with app.state.session_factory() as db:
        cylinder = _build_cylinder(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            serial="SUM-ADDR-001",
            product_id=product["id"],
            condition="CILPRO",
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
                condition="CILPRO",
                created_by=seeded_demo["user_id"],
                change_date=now - timedelta(days=1),
            )
        )

        action_context = LogisticsActionContext(
            tenant_id=seeded_demo["tenant_id"],
            branch_id=seeded_demo["branch_id"],
            actor_user_id=seeded_demo["user_id"],
            correlation_id=None,
            request_id=None,
        )
        base = now - timedelta(hours=3)
        record_cylinder_event(
            db,
            cylinder_id=cylinder.id,
            tenant_id=seeded_demo["tenant_id"],
            event_type="WAREHOUSE_IN",
            location_type="WAREHOUSE",
            location_id="wh-1",
            warehouse_id="wh-1",
            session_id=None,
            customer_id=None,
            source_type="TEST",
            source_id="sum-addr-wh",
            occurred_at=base,
            action_context=action_context,
        )
        record_cylinder_event(
            db,
            cylinder_id=cylinder.id,
            tenant_id=seeded_demo["tenant_id"],
            event_type="VEHICLE_LOAD",
            location_type="VEHICLE",
            location_id="sess-1",
            warehouse_id=None,
            session_id="sess-1",
            customer_id=None,
            source_type="TEST",
            source_id="sum-addr-load",
            occurred_at=base + timedelta(hours=1),
            action_context=action_context,
        )
        record_cylinder_event(
            db,
            cylinder_id=cylinder.id,
            tenant_id=seeded_demo["tenant_id"],
            event_type="CUSTOMER_DELIVERY",
            location_type="CUSTOMER",
            location_id=customer["id"],
            warehouse_id=None,
            session_id="sess-1",
            customer_id=customer["id"],
            customer_address_id=address["id"],
            source_type="TEST",
            source_id="sum-addr-delivery",
            occurred_at=base + timedelta(hours=2),
            action_context=action_context,
        )
        db.commit()
        cylinder_id = cylinder.id

    with TestClient(app) as client:
        headers = auth_headers(client)
        response = client.get(
            f"/api/v1/plugins/logistics/customers/{customer['id']}/cylinders/summary",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        payload = response.json()

    row = next(r for r in payload["by_product"] if r["product_id"] == product["id"])
    assert row["at_customer"] == 1
    assert row["customer_address_id"] == address["id"]
    assert row["address_label"] and "Siempre Viva" in row["address_label"]

    # list_cylinders_at_customers también expone la dirección trazable.
    with TestClient(app) as client:
        headers = auth_headers(client)
        at_customers = client.get(
            "/api/v1/plugins/logistics/cylinders/at-customers",
            headers=headers,
        )
        assert at_customers.status_code == 200, at_customers.text
        entry = next(
            item for item in at_customers.json() if item["cylinder_id"] == cylinder_id
        )
        assert entry["customer_address_id"] == address["id"]
        assert entry["address_label"] and "Siempre Viva" in entry["address_label"]
