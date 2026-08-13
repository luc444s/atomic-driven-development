from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from apps.api.app.kernel.auth.models import User
from apps.api.app.kernel.tenants.models import Branch, Tenant
from plugins.logistics.backend.common import LogisticsActionContext
from plugins.logistics.backend.dto.sessions import SessionWaybillTotalsRead
from plugins.logistics.backend.models import (
    LogisticsDeliveryPoint,
    LogisticsLoadPlan,
    LogisticsLoadPlanItem,
    LogisticsMovementItem,
    LogisticsOperation,
    LogisticsRoute,
    LogisticsRouteStop,
    LogisticsSessionWaybillVersion,
    LogisticsVehicle,
    LogisticsVehicleSession,
    LogisticsWarehouse,
)
from plugins.logistics.backend.services.session_waybills import (
    build_waybill_official_snapshot,
    emit_session_waybill_document,
    get_session_waybill_document_version,
    get_session_waybill_state,
    render_waybill_html,
)
from plugins.productos.backend.models import (
    Product,
    ProductAdr,
    ProductCategory,
    ProductCondition,
    ProductLine,
    ProductStatus,
    ProductUnit,
)


def _seed_base_graph(db_session) -> dict[str, str]:
    tenant = Tenant(name="Tenant Test", slug="tenant-test")
    db_session.add(tenant)
    db_session.flush()

    branch = Branch(tenant_id=tenant.id, name="Branch Test", code="MAIN")
    db_session.add(branch)
    db_session.flush()

    user = User(
        tenant_id=tenant.id,
        branch_id=branch.id,
        email="driver@example.com",
        full_name="Driver Test",
        password_hash="x",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    warehouse = LogisticsWarehouse(
        tenant_id=tenant.id,
        branch_id=branch.id,
        name="Warehouse Test",
        code="WH-1",
    )
    db_session.add(warehouse)
    db_session.flush()

    vehicle = LogisticsVehicle(
        tenant_id=tenant.id,
        plate="TRK-UNIT",
        vehicle_type="Camion",
        warehouse_id=warehouse.id,
        mobile_warehouse_id=warehouse.id,
    )
    db_session.add(vehicle)
    db_session.flush()

    route = LogisticsRoute(
        tenant_id=tenant.id,
        branch_id=branch.id,
        route_date=datetime.now(UTC).date(),
        driver_id=user.id,
        vehicle_id=vehicle.id,
        created_by=user.id,
    )
    db_session.add(route)
    db_session.flush()

    delivery_point = LogisticsDeliveryPoint(
        tenant_id=tenant.id,
        customer_id="customer-1",
        customer_name="Cliente Unico",
        address="Calle Unica 123",
        warehouse_id=warehouse.id,
        is_primary=True,
    )
    db_session.add(delivery_point)
    db_session.flush()

    db_session.add(
        LogisticsRouteStop(
            route_id=route.id,
            delivery_point_id=delivery_point.id,
            customer_id=delivery_point.customer_id,
            customer_name_snapshot=delivery_point.customer_name,
            stop_order=1,
            notes=delivery_point.address,
        )
    )

    db_session.add_all(
        [
            ProductStatus(code="ACTIVE", name="Activo", is_active=True),
            ProductCondition(code="NEW", name="Nuevo", is_active=True),
        ]
    )
    db_session.flush()

    category = ProductCategory(
        tenant_id=tenant.id,
        code="CAT-UNIT",
        name="Categoria Test",
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()

    line = ProductLine(
        tenant_id=tenant.id,
        code="LIN-UNIT",
        name="Linea Test",
        category_id=category.id,
        is_active=True,
    )
    db_session.add(line)
    db_session.flush()

    unit = ProductUnit(
        tenant_id=tenant.id,
        code="KG",
        name="Kilogramo",
        is_active=True,
    )
    db_session.add(unit)
    db_session.flush()

    product = Product(
        tenant_id=tenant.id,
        sku="P-UNIT",
        name="Oxigeno 10kg",
        line_id=line.id,
        unit_id=unit.id,
        status_code="ACTIVE",
        condition_code="NEW",
        weight_kg=10,
        is_service=False,
        is_active=True,
        created_by=user.id,
    )
    db_session.add(product)
    db_session.flush()

    db_session.add(
        ProductAdr(
            tenant_id=tenant.id,
            product_id=product.id,
            category="2.2",
            packaging_type="CILINDRO",
            net_weight_kg=10,
            un_number="1072",
            cargo_description="OXIGENO COMPRIMIDO",
            unit_measure="kg",
            points=1,
            valid_from=datetime.now(UTC).date(),
            created_by=user.id,
        )
    )

    session = LogisticsVehicleSession(
        tenant_id=tenant.id,
        branch_id=branch.id,
        vehicle_id=vehicle.id,
        driver_id=user.id,
        origin_warehouse_id=warehouse.id,
        mobile_warehouse_id=warehouse.id,
        route_id=route.id,
        status="OUTBOUND",
        created_by=user.id,
        updated_by=user.id,
    )
    db_session.add(session)
    db_session.commit()

    return {
        "tenant_id": tenant.id,
        "branch_id": branch.id,
        "user_id": user.id,
        "route_id": route.id,
        "session_id": session.id,
        "product_id": product.id,
    }


def _settings(test_settings):
    return test_settings.model_copy(
        update={
            "logistics_waybill_issuer_legal_name": "Transportes Demo SL",
            "logistics_waybill_issuer_address_line": "Calle Ruta 100",
            "logistics_waybill_issuer_postal_city_line": "47001 Valladolid",
        }
    )


def _action_context(seed: dict[str, str]) -> LogisticsActionContext:
    return LogisticsActionContext(
        tenant_id=seed["tenant_id"],
        branch_id=seed["branch_id"],
        actor_user_id=seed["user_id"],
        correlation_id="test-waybill-official",
        request_id="test-waybill-official",
    )


def _mock_preview(seed: dict[str, str]):
    return SimpleNamespace(
        movement_ids=["mov-1"],
        operational_hash="hash-1",
        snapshot=SimpleNamespace(
            vehicle=SimpleNamespace(plate="TRK-UNIT"),
            driver=SimpleNamespace(name="Driver Test"),
            destination=SimpleNamespace(name="Cliente Unico", address="Calle Unica 123"),
            totals=SessionWaybillTotalsRead(
                total_packages=5,
                total_weight_kg=50,
                total_adr_points=5,
            ),
            transported_items=[],
        ),
    )


def _mock_composition(seed: dict[str, str]):
    return SimpleNamespace(
        product_lines=[
            SimpleNamespace(
                product_id=seed["product_id"],
                product_name="Oxigeno 10kg",
                quantity=5.0,
                weight_kg=50.0,
                adr_points=5.0,
            )
        ],
        totals=SimpleNamespace(total_packages=5, total_weight_kg=50, total_adr_points=5),
    )


def _preview_snapshot_json() -> str:
    return (
        "{"
        '"vehicle": {"id": "v", "plate": "TRK-UNIT", "kind": "Camion"}, '
        '"driver": {"id": "u", "name": "Driver Test", "license": null}, '
        '"destination": {"id": "d", "name": "Cliente Unico", "address": "Calle Unica 123"}, '
        '"transported_items": [], '
        '"totals": {"total_packages": 5, "total_weight_kg": 50, "total_adr_points": 5}'
        "}"
    )


def test_build_official_snapshot_single_stop_sqlite(
    db_session, test_settings, monkeypatch
) -> None:
    seed = _seed_base_graph(db_session)
    session = db_session.get(LogisticsVehicleSession, seed["session_id"])
    assert session is not None

    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_session_waybill",
        lambda db, session: _mock_preview(seed),
    )
    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_composition",
        lambda db, session: _mock_composition(seed),
    )

    snapshot = build_waybill_official_snapshot(
        db_session,
        session=session,
        settings=_settings(test_settings),
    )
    assert snapshot.issuer.legal_name == "Transportes Demo SL"
    assert snapshot.consignee.mode == "SINGLE_DESTINATION"
    assert snapshot.regulatory_lines[0].adr_goods_description == "UN 1072 OXIGENO COMPRIMIDO"


def test_emit_official_waybill_uses_route_distribution_sqlite(
    db_session, test_settings, monkeypatch
) -> None:
    seed = _seed_base_graph(db_session)
    session = db_session.get(LogisticsVehicleSession, seed["session_id"])
    assert session is not None
    db_session.add(
        LogisticsRouteStop(
            route_id=seed["route_id"],
            delivery_point_id=None,
            customer_id="customer-2",
            customer_name_snapshot="Cliente Secundario",
            stop_order=2,
            notes="Calle Secundaria 456",
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_session_waybill",
        lambda db, session: _mock_preview(seed),
    )
    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_composition",
        lambda db, session: _mock_composition(seed),
    )

    preview_version = LogisticsSessionWaybillVersion(
        tenant_id=seed["tenant_id"],
        session_id=seed["session_id"],
        version=1,
        status="ACTIVE_PREVIEW",
        regulatory_context="ES_HACIENDA",
        generated_by=seed["user_id"],
        operational_hash="hash-1",
        snapshot_schema_version=1,
        movement_ids_json='["mov-1"]',
        snapshot_json=_preview_snapshot_json(),
        change_event="INITIAL_GENERATION",
        change_reason="preview",
    )
    db_session.add(preview_version)
    db_session.commit()

    state = emit_session_waybill_document(
        db_session,
        session=session,
        settings=_settings(test_settings),
        reason="emit",
        idempotency_key="emit-1",
        action_context=_action_context(seed),
    )
    db_session.commit()

    assert state.issued is not None
    assert state.issued.snapshot.consignee.mode == "ROUTE_DISTRIBUTION"
    assert state.issued.snapshot.consignee.legal_name == "REPARTO EN RUTA"

    version = get_session_waybill_document_version(
        db_session,
        session_id=seed["session_id"],
    )
    assert version is not None
    html = render_waybill_html(version)
    assert "Transportes Demo SL" in html
    assert "UN 1072 OXIGENO COMPRIMIDO" in html


def test_emit_official_waybill_requires_adr_data_sqlite(
    db_session, test_settings, monkeypatch
) -> None:
    seed = _seed_base_graph(db_session)
    session = db_session.get(LogisticsVehicleSession, seed["session_id"])
    assert session is not None

    db_session.query(ProductAdr).filter(ProductAdr.product_id == seed["product_id"]).delete()
    db_session.commit()

    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_session_waybill",
        lambda db, session: _mock_preview(seed),
    )
    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_composition",
        lambda db, session: _mock_composition(seed),
    )

    preview_version = LogisticsSessionWaybillVersion(
        tenant_id=seed["tenant_id"],
        session_id=seed["session_id"],
        version=1,
        status="ACTIVE_PREVIEW",
        regulatory_context="ES_HACIENDA",
        generated_by=seed["user_id"],
        operational_hash="hash-1",
        snapshot_schema_version=1,
        movement_ids_json='["mov-1"]',
        snapshot_json=_preview_snapshot_json(),
        change_event="INITIAL_GENERATION",
        change_reason="preview",
    )
    db_session.add(preview_version)
    db_session.commit()

    try:
        emit_session_waybill_document(
            db_session,
            session=session,
            settings=_settings(test_settings),
            reason="emit",
            idempotency_key="emit-2",
            action_context=_action_context(seed),
        )
    except ValueError as exc:
        assert "Faltan datos ADR minimos" in str(exc)
    else:
        raise AssertionError("Expected ADR validation error")


def test_build_official_snapshot_falls_back_to_load_plan_when_composition_is_empty(
    db_session, test_settings, monkeypatch
) -> None:
    seed = _seed_base_graph(db_session)
    session = db_session.get(LogisticsVehicleSession, seed["session_id"])
    assert session is not None

    load_plan = LogisticsLoadPlan(
        tenant_id=seed["tenant_id"],
        session_id=seed["session_id"],
        status="DRAFT",
        created_by=seed["user_id"],
    )
    db_session.add(load_plan)
    db_session.flush()
    db_session.add(
        LogisticsLoadPlanItem(
            load_plan_id=load_plan.id,
            product_id=seed["product_id"],
            product_name="Oxigeno 10kg",
            planned_quantity=5,
            planned_weight_kg=50,
            source_warehouse_id=session.origin_warehouse_id,
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_session_waybill",
        lambda db, session: _mock_preview(seed),
    )
    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_composition",
        lambda db, session: SimpleNamespace(
            product_lines=[],
            totals=SessionWaybillTotalsRead(
                total_packages=5,
                total_weight_kg=50,
                total_adr_points=5,
            ),
        ),
    )

    snapshot = build_waybill_official_snapshot(
        db_session,
        session=session,
        settings=_settings(test_settings),
    )
    assert snapshot.regulatory_lines[0].product_name == "Oxigeno 10kg"
    assert snapshot.regulatory_lines[0].package_count == 5


def test_build_official_snapshot_falls_back_to_confirmed_movement_items(
    db_session, test_settings, monkeypatch
) -> None:
    seed = _seed_base_graph(db_session)
    session = db_session.get(LogisticsVehicleSession, seed["session_id"])
    assert session is not None

    db_session.add(
        LogisticsOperation(
            tenant_id=seed["tenant_id"],
            session_id=seed["session_id"],
            movement_type="TRANSFER_OUT",
            status="CONFIRMED",
            external_movement_id="mov-1",
            idempotency_key="op-mov-1",
            performed_by=seed["user_id"],
        )
    )
    db_session.add(
        LogisticsMovementItem(
            movement_id="mov-1",
            product_id=seed["product_id"],
            product_name="Oxigeno 10kg",
            quantity_out=5,
            quantity=5,
            quantity_planned=5,
        )
    )
    db_session.commit()

    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_session_waybill",
        lambda db, session: _mock_preview(seed),
    )
    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_composition",
        lambda db, session: SimpleNamespace(
            product_lines=[],
            totals=SessionWaybillTotalsRead(
                total_packages=5,
                total_weight_kg=50,
                total_adr_points=5,
            ),
        ),
    )

    snapshot = build_waybill_official_snapshot(
        db_session,
        session=session,
        settings=_settings(test_settings),
    )
    assert snapshot.regulatory_lines[0].product_name == "Oxigeno 10kg"
    assert snapshot.regulatory_lines[0].package_count == 5


def test_waybill_state_disables_emit_when_vehicle_has_no_operational_load(
    db_session, test_settings, monkeypatch
) -> None:
    seed = _seed_base_graph(db_session)
    session = db_session.get(LogisticsVehicleSession, seed["session_id"])
    assert session is not None

    preview_version = LogisticsSessionWaybillVersion(
        tenant_id=seed["tenant_id"],
        session_id=seed["session_id"],
        version=1,
        status="ACTIVE_PREVIEW",
        regulatory_context="ES_HACIENDA",
        generated_by=seed["user_id"],
        operational_hash="hash-1",
        snapshot_schema_version=1,
        movement_ids_json='["mov-1"]',
        snapshot_json=_preview_snapshot_json(),
        change_event="INITIAL_GENERATION",
        change_reason="preview",
    )
    db_session.add(preview_version)
    db_session.commit()

    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_session_waybill",
        lambda db, session: _mock_preview(seed),
    )
    monkeypatch.setattr(
        "plugins.logistics.backend.services.session_waybills.build_current_composition",
        lambda db, session: SimpleNamespace(
            product_lines=[],
            totals=SessionWaybillTotalsRead(
                total_packages=0,
                total_weight_kg=0,
                total_adr_points=0,
            ),
        ),
    )

    state = get_session_waybill_state(db_session, session=session)
    assert state.can_emit is False
    assert state.emit_block_reason is not None
    assert "vehiculo no tiene carga operativa" in state.emit_block_reason.lower()

    try:
        build_waybill_official_snapshot(
            db_session,
            session=session,
            settings=_settings(test_settings),
        )
    except ValueError as exc:
        assert "No hay carga operativa en el vehiculo" in str(exc)
    else:
        raise AssertionError("Expected empty-vehicle validation error")
