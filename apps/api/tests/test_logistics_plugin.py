# ruff: noqa: E501
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.api.v1.core.common import CoreActionContext
from apps.api.app.api.v1.core.services.plugins import set_core_plugin_enabled
from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.lifecycle import bootstrap_app_state
from apps.api.app.kernel.audit.models import AuditLog
from apps.api.app.kernel.events.models import EventLog
from apps.api.app.kernel.plugins.persistent import (
    get_plugin_registry_record_by_plugin_id,
    sync_plugin_registry_state,
)
from apps.api.tests.test_productos_plugin import enable_productos_plugin
from plugins.logistics.backend.models import (
    LogisticsAgendaTaskType,
    LogisticsCylinderState,
    LogisticsMovementType,
    LogisticsStateTransition,
)
from plugins.logistics.backend.services.catalog import (
    AGENDA_TASK_TYPE_DEFINITIONS,
    MOVEMENT_TYPE_DEFINITIONS,
    STATE_DEFINITIONS,
    TRANSITION_DEFINITIONS,
)


def login(client: TestClient, email: str = "admin@example.com", password: str = "ChangeMe123!"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client: TestClient) -> dict[str, str]:
    response = login(client)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def enable_crm_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        set_core_plugin_enabled(
            db,
            registry=app.state.plugin_registry,
            plugin_id="crm",
            context_builder=app.state.plugin_runtime.context_builder,
            is_enabled=True,
            action_context=CoreActionContext(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                actor_user_id=seeded_demo["user_id"],
                correlation_id="test-crm-enable",
                request_id="test-crm-enable",
            ),
        )
        db.commit()
    bootstrap_app_state(app, app.state.settings)


def enable_logistics_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        record = get_plugin_registry_record_by_plugin_id(db, plugin_id="logistics")
        assert record is not None
        existing_states = set(db.scalars(select(LogisticsCylinderState.code)).all())
        for code, is_final, description in STATE_DEFINITIONS:
            if code in existing_states:
                continue
            db.add(LogisticsCylinderState(code=code, is_final=is_final, description=description))
        existing_transitions = {
            (item.from_state, item.to_state)
            for item in db.scalars(select(LogisticsStateTransition)).all()
        }
        for (
            from_state,
            to_state,
            requires_adr,
            requires_hydrotest,
            description,
        ) in TRANSITION_DEFINITIONS:
            if (from_state, to_state) in existing_transitions:
                continue
            db.add(
                LogisticsStateTransition(
                    from_state=from_state,
                    to_state=to_state,
                    requires_adr=requires_adr,
                    requires_hydrotest=requires_hydrotest,
                    description=description,
                )
            )
        existing_movement_types = set(db.scalars(select(LogisticsMovementType.code)).all())
        for (
            code,
            name,
            category,
            moves_cylinders,
            origin_state,
            target_state,
        ) in MOVEMENT_TYPE_DEFINITIONS:
            if code in existing_movement_types:
                continue
            db.add(
                LogisticsMovementType(
                    code=code,
                    name=name,
                    category=category,
                    moves_cylinders=moves_cylinders,
                    origin_state=origin_state,
                    target_state=target_state,
                )
            )
        existing_task_types = set(db.scalars(select(LogisticsAgendaTaskType.code)).all())
        for code, description in AGENDA_TASK_TYPE_DEFINITIONS:
            if code in existing_task_types:
                continue
            db.add(LogisticsAgendaTaskType(code=code, description=description))
        record.migration_version = "0006"
        db.flush()
        set_core_plugin_enabled(
            db,
            registry=app.state.plugin_registry,
            plugin_id="logistics",
            context_builder=app.state.plugin_runtime.context_builder,
            is_enabled=True,
            action_context=CoreActionContext(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                actor_user_id=seeded_demo["user_id"],
                correlation_id="test-logistics-enable",
                request_id="test-logistics-enable",
            ),
        )
        db.commit()
    bootstrap_app_state(app, app.state.settings)


def enable_stock_plugin(app, seeded_demo: dict[str, str]) -> None:
    with app.state.session_factory() as db:
        app.state.plugin_registry.discover()
        sync_plugin_registry_state(db, registry=app.state.plugin_registry)
        set_core_plugin_enabled(
            db,
            registry=app.state.plugin_registry,
            plugin_id="stock",
            context_builder=app.state.plugin_runtime.context_builder,
            is_enabled=True,
            action_context=CoreActionContext(
                tenant_id=seeded_demo["tenant_id"],
                branch_id=seeded_demo["branch_id"],
                actor_user_id=seeded_demo["user_id"],
                correlation_id="test-stock-enable",
                request_id="test-stock-enable",
            ),
        )
        db.commit()
    bootstrap_app_state(app, app.state.settings)


def create_customer(
    client: TestClient, headers: dict[str, str], *, name: str, document_number: str
) -> dict[str, str]:
    response = client.post(
        "/api/v1/plugins/crm/customers",
        headers=headers,
        json={
            "legal_name": name,
            "document_type_code": "RUC",
            "document_number": document_number,
            "country_code": "PER",
            "billing_type": "por_operacion",
            "is_exempt": False,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_product(client: TestClient, headers: dict[str, str], *, sku: str, name: str) -> dict[str, str]:
    category = client.post(
        "/api/v1/plugins/productos/catalog/categories",
        headers=headers,
        json={"code": f"CAT-{sku}", "name": f"Categoria {sku}", "description": "Categoria test"},
    ).json()
    line = client.post(
        "/api/v1/plugins/productos/catalog/lines",
        headers=headers,
        json={
            "code": f"LIN-{sku}",
            "name": f"Linea {sku}",
            "category_id": category["id"],
            "description": "Linea test",
        },
    ).json()
    subline = client.post(
        "/api/v1/plugins/productos/catalog/subline",
        headers=headers,
        json={"code": f"SUB-{sku}", "name": f"Sublinea {sku}", "line_id": line["id"]},
    ).json()
    brand = client.post(
        "/api/v1/plugins/productos/catalog/brands",
        headers=headers,
        json={"code": f"BRA-{sku}", "name": f"Marca {sku}", "description": "Marca test"},
    ).json()
    unit = client.post(
        "/api/v1/plugins/productos/catalog/units",
        headers=headers,
        json={
            "code": f"U-{sku}",
            "name": f"Unidad {sku}",
            "equivalencia": 1,
            "m3_factor": 0,
            "liter_factor": 0,
            "kg_factor": 1,
        },
    ).json()
    product = client.post(
        "/api/v1/plugins/productos/products",
        headers=headers,
        json={
            "sku": sku,
            "name": name,
            "description": name,
            "line_id": line["id"],
            "subline_id": subline["id"],
            "brand_id": brand["id"],
            "unit_id": unit["id"],
            "status_code": "ACTIVO",
            "condition_code": "GAS",
            "weight_kg": 10,
        },
    )
    assert product.status_code == 201, product.text
    return product.json()


def test_logistics_plugin_cylinder_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        states_response = client.get(
            "/api/v1/plugins/logistics/catalog/cylinder-states", headers=headers
        )
        assert states_response.status_code == 200
        assert len(states_response.json()) == 18

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "GL-000001",
                "location": "Almacen central",
            },
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()
        assert cylinder["current_state"] == "CREADO_VACIO"
        assert cylinder["serial"] == "GL-000001"

        list_response = client.get("/api/v1/plugins/logistics/cylinders", headers=headers)
        assert list_response.status_code == 200
        assert [item["serial"] for item in list_response.json()] == ["GL-000001"]

        allowed_response = client.get(
            f"/api/v1/plugins/logistics/cylinders/allowed-transitions/{cylinder['id']}",
            headers=headers,
        )
        assert allowed_response.status_code == 200
        assert [item["to_state"] for item in allowed_response.json()] == ["EN_ALMACEN_VACIO"]

        move_to_stock_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "EN_ALMACEN_VACIO", "origin": "ALTA"},
        )
        assert move_to_stock_response.status_code == 200, move_to_stock_response.text
        assert move_to_stock_response.json()["current_state"] == "EN_ALMACEN_VACIO"

        missing_adr_or_ph_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "LLENADO_OK", "origin": "PLANTA"},
        )
        assert missing_adr_or_ph_response.status_code == 400
        assert "ADR" in missing_adr_or_ph_response.json()["detail"] or "hydrotest" in str(
            missing_adr_or_ph_response.json()["detail"]
        )

        valid_create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "GL-000002",
                "location": "Planta norte",
                "next_hydrotest_date": (datetime.now(UTC) + timedelta(days=365)).date().isoformat(),
                "adr_category": "2F",
                "adr_un_number": "1047",
                "adr_label": "GLP",
            },
        )
        assert valid_create_response.status_code == 201, valid_create_response.text
        valid_cylinder = valid_create_response.json()

        client.post(
            f"/api/v1/plugins/logistics/cylinders/{valid_cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "EN_ALMACEN_VACIO", "origin": "ALTA"},
        )

        move_to_loaded_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{valid_cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "LLENADO_OK", "origin": "PLANTA"},
        )
        assert move_to_loaded_response.status_code == 200, move_to_loaded_response.text
        assert move_to_loaded_response.json()["current_state"] == "LLENADO_OK"

        trace_response = client.get(
            f"/api/v1/plugins/logistics/cylinders/{valid_cylinder['id']}/trace",
            headers=headers,
        )
        assert trace_response.status_code == 200
        assert [item["to_state"] for item in trace_response.json()] == [
            "LLENADO_OK",
            "EN_ALMACEN_VACIO",
            "CREADO_VACIO",
        ]

        summary_response = client.get(
            "/api/v1/plugins/logistics/cylinders/summary", headers=headers
        )
        assert summary_response.status_code == 200
        summary = {item["state"]: item["count"] for item in summary_response.json()}
        assert summary["EN_ALMACEN_VACIO"] == 1
        assert summary["LLENADO_OK"] == 1

    with app.state.session_factory() as db:
        audits = list(
            db.scalars(
                select(AuditLog).where(
                    AuditLog.module == "logistics",
                    AuditLog.tenant_id == seeded_demo["tenant_id"],
                )
            ).all()
        )
        events = list(
            db.scalars(
                select(EventLog).where(
                    EventLog.module == "logistics",
                    EventLog.tenant_id == seeded_demo["tenant_id"],
                )
            ).all()
        )

    assert any(audit.action == "cylinder.create" for audit in audits)
    assert any(audit.action == "cylinder.transition" for audit in audits)
    assert any(event.event_name == "logistics.cylinder.created" for event in events)
    assert any(event.event_name == "logistics.cylinder.state_changed" for event in events)


def test_logistics_plugin_operations_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = create_customer(
            client,
            headers,
            name="GLP Norte SAC",
            document_number="20100070970",
        )

        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Planta Norte", "code": "PN", "address": "Av. Norte 123"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()

        zone_response = client.post(
            "/api/v1/plugins/logistics/zones",
            headers=headers,
            json={"name": "Zona Centro", "code": "CENTRO"},
        )
        assert zone_response.status_code == 201, zone_response.text
        zone = zone_response.json()

        vehicle_response = client.post(
            "/api/v1/plugins/logistics/vehicles",
            headers=headers,
            json={
                "plate": "ABC-123",
                "vehicle_type": "Camion",
                "capacity_weight": 1200,
                "warehouse_id": warehouse["id"],
            },
        )
        assert vehicle_response.status_code == 201, vehicle_response.text
        vehicle = vehicle_response.json()

        delivery_point_response = client.post(
            "/api/v1/plugins/logistics/delivery-points",
            headers=headers,
            json={
                "customer_id": customer["id"],
                "contact_name": "Ana Lopez",
                "address": "Calle 1 #123",
                "zone_id": zone["id"],
                "is_primary": True,
            },
        )
        assert delivery_point_response.status_code == 201, delivery_point_response.text
        delivery_point = delivery_point_response.json()

        order_response = client.post(
            "/api/v1/plugins/logistics/orders",
            headers=headers,
            json={
                "customer_id": customer["id"],
                "movement_type": "SC",
                "warehouse_id": warehouse["id"],
                "notes": "Pedido de prueba",
            },
        )
        assert order_response.status_code == 201, order_response.text
        order = order_response.json()

        order_item_response = client.post(
            f"/api/v1/plugins/logistics/orders/{order['id']}/items",
            headers=headers,
            json={
                "product_name": "Envase 10kg",
                "quantity_requested": 2,
                "quantity_planned": 2,
                "location": "ALMACEN",
            },
        )
        assert order_item_response.status_code == 201, order_item_response.text

        cylinder_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "GL-100001",
                "location": "Planta Norte",
                "next_hydrotest_date": (datetime.now(UTC) + timedelta(days=365)).date().isoformat(),
                "adr_category": "2F",
                "adr_un_number": "1047",
                "adr_label": "GLP",
            },
        )
        assert cylinder_response.status_code == 201, cylinder_response.text
        cylinder = cylinder_response.json()

        client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "EN_ALMACEN_VACIO", "origin": "ALTA"},
        )
        client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "LLENADO_OK", "origin": "PLANTA"},
        )

        route_response = client.post(
            "/api/v1/plugins/logistics/routes",
            headers=headers,
            json={
                "route_date": datetime.now(UTC).date().isoformat(),
                "vehicle_id": vehicle["id"],
                "notes": "Ruta centro",
            },
        )
        assert route_response.status_code == 201, route_response.text
        route = route_response.json()

        stop_response = client.post(
            f"/api/v1/plugins/logistics/routes/{route['id']}/stops",
            headers=headers,
            json={"delivery_point_id": delivery_point["id"], "stop_order": 1},
        )
        assert stop_response.status_code == 201, stop_response.text
        stop = stop_response.json()

        bulk_load_response = client.post(
            "/api/v1/plugins/logistics/loads/bulk",
            headers=headers,
            json={"route_id": route["id"], "cylinder_ids": [cylinder["id"]], "stop_id": stop["id"]},
        )
        assert bulk_load_response.status_code == 201, bulk_load_response.text

        confirm_load_response = client.post(
            "/api/v1/plugins/logistics/loads/confirm",
            headers=headers,
            json={"route_id": route["id"]},
        )
        assert confirm_load_response.status_code == 200, confirm_load_response.text
        assert confirm_load_response.json()[0]["status"] == "CARGADO"

        cylinder_after_load = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
        ).json()
        assert cylinder_after_load["current_state"] == "CARGA_EN_VEHICULO"

        agenda_from_route_response = client.post(
            f"/api/v1/plugins/logistics/routes/{route['id']}/agenda-tasks",
            headers=headers,
        )
        assert agenda_from_route_response.status_code == 200, agenda_from_route_response.text
        assert len(agenda_from_route_response.json()) == 1

        route_start_response = client.post(
            f"/api/v1/plugins/logistics/routes/{route['id']}/start",
            headers=headers,
        )
        assert route_start_response.status_code == 200, route_start_response.text

        cylinder_on_route = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
        ).json()
        assert cylinder_on_route["current_state"] == "EN_RUTA"

        deliver_response = client.post(
            f"/api/v1/plugins/logistics/routes/{route['id']}/stops/{stop['id']}/deliver",
            headers=headers,
        )
        assert deliver_response.status_code == 200, deliver_response.text
        assert deliver_response.json()["status"] == "ENTREGADO"

        delivered_cylinder = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
        ).json()
        assert delivered_cylinder["current_state"] == "EN_CLIENTE_LLENO"

        client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "EN_CLIENTE_VACIO", "origin": "CLIENTE"},
        )

        movement_response = client.post(
            "/api/v1/plugins/logistics/movements",
            headers=headers,
            json={
                "movement_type": "IC",
                "customer_id": customer["id"],
                "warehouse_id": warehouse["id"],
                "items": [{"cylinder_id": cylinder["id"], "quantity": 1, "quantity_in": 1}],
            },
        )
        assert movement_response.status_code == 201, movement_response.text
        movement = movement_response.json()

        confirm_movement_response = client.post(
            f"/api/v1/plugins/logistics/movements/{movement['id']}/confirm",
            headers=headers,
        )
        assert confirm_movement_response.status_code == 200, confirm_movement_response.text
        assert confirm_movement_response.json()["status"] == "COMPLETADO"

        returned_cylinder = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
        ).json()
        assert returned_cylinder["current_state"] == "EN_ALMACEN_VACIO"

        task_response = client.post(
            "/api/v1/plugins/logistics/agenda/tasks",
            headers=headers,
            json={
                "task_type": "VISITA",
                "scheduled_date": datetime.now(UTC).date().isoformat(),
                "customer_id": customer["id"],
                "description": "Revision general",
            },
        )
        assert task_response.status_code == 201, task_response.text
        task = task_response.json()

        task_complete_response = client.post(
            f"/api/v1/plugins/logistics/agenda/tasks/{task['id']}/complete",
            headers=headers,
        )
        assert task_complete_response.status_code == 200, task_complete_response.text
        assert task_complete_response.json()["status"] == "REALIZADO"

        agenda_list_response = client.get("/api/v1/plugins/logistics/agenda/tasks", headers=headers)
        assert agenda_list_response.status_code == 200
        assert len(agenda_list_response.json()) >= 2


def test_logistics_plugin_envase_complete_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = create_customer(
            client,
            headers,
            name="GLP Campo SAC",
            document_number="10467793549",
        )

        gas_products_response = client.get(
            "/api/v1/plugins/logistics/catalog/gas-products", headers=headers
        )
        assert gas_products_response.status_code == 200, gas_products_response.text
        gas_product = gas_products_response.json()[0]

        brands_response = client.get("/api/v1/plugins/logistics/catalog/brands", headers=headers)
        assert brands_response.status_code == 200, brands_response.text
        brand = brands_response.json()[0]

        service_types_response = client.get(
            "/api/v1/plugins/logistics/catalog/service-types", headers=headers
        )
        assert service_types_response.status_code == 200, service_types_response.text
        service_type = service_types_response.json()[0]

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "GL-200001",
                "description": "Envase piloto 10kg",
                "barcode1": "BC-200001",
                "barcode2": "MAT-200001",
                "gas_group_id": gas_product["id"],
                "content_kg": 10,
                "volume_m3": 1.2,
                "condition": "NUEVO",
                "brand_id": brand["id"],
                "cost": 120,
                "price": 170,
                "country_code": "PE",
                "box_number": "LOTE-1",
                "manufacturer_code": "FAB-01",
                "manufacture_year": 2025,
                "weight_origin": 12.5,
                "weight_current": 12.4,
                "next_hydrotest_date": (datetime.now(UTC) + timedelta(days=365)).date().isoformat(),
                "adr_category": "2F",
                "adr_un_number": "1047",
                "adr_label": "GLP",
                "adr_package_type": "CIL",
                "adr_weight_kg": 22.5,
                "adr_merchandise": "Gas licuado de petroleo",
                "adr_tunnel": "B/D",
                "adr_subline": "GLP",
                "adr_factor": 1.0,
                "adr_points": 3,
                "adr_unit_measure": "KG",
                "location": "Patio norte",
            },
        )
        assert create_response.status_code == 201, create_response.text
        cylinder = create_response.json()
        assert cylinder["barcode2"] == "MAT-200001"
        assert cylinder["brand_id"] == brand["id"]

        update_response = client.patch(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
            json={"description": "Envase piloto 10kg revisado", "price": 175},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["description"] == "Envase piloto 10kg revisado"
        assert update_response.json()["price"] == 175

        by_serial_response = client.get(
            "/api/v1/plugins/logistics/cylinders/by-serial/MAT-200001",
            headers=headers,
        )
        assert by_serial_response.status_code == 200, by_serial_response.text
        assert by_serial_response.json()["id"] == cylinder["id"]

        retimbrado_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/retimbrados",
            headers=headers,
            json={
                "retimbrado_date": datetime.now(UTC).date().isoformat(),
                "manufacture_code": "FAB-01",
                "manufacture_year": 2025,
                "serial_number": "NB-200001",
                "test_pressure": 30,
                "approval_number": "APR-001",
                "danger_class": "2",
                "adr_label": "GLP",
                "un_number": "1047",
            },
        )
        assert retimbrado_response.status_code == 201, retimbrado_response.text
        assert retimbrado_response.json()["approval_number"] == "APR-001"

        label_data_response = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/label-data",
            headers=headers,
        )
        assert label_data_response.status_code == 200, label_data_response.text
        assert label_data_response.json()["approval_number"] == "APR-001"

        label_print_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/print-label",
            headers=headers,
            json={"origin": "ALTA", "printer_name": "Zebra 01", "copies": 1},
        )
        assert label_print_response.status_code == 201, label_print_response.text
        assert label_print_response.json()["origin"] == "ALTA"

        invalid_reprint_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/print-label",
            headers=headers,
            json={"origin": "REIMPRESION", "copies": 1},
        )
        assert invalid_reprint_response.status_code == 400

        client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "EN_ALMACEN_VACIO", "origin": "ALTA"},
        )
        client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/transition",
            headers=headers,
            json={"to_state": "LLENADO_OK", "origin": "PLANTA"},
        )

        movement_response = client.post(
            "/api/v1/plugins/logistics/movements",
            headers=headers,
            json={
                "movement_type": "SC",
                "customer_id": customer["id"],
                "items": [{"cylinder_id": cylinder["id"], "quantity": 1, "quantity_out": 1}],
            },
        )
        assert movement_response.status_code == 201, movement_response.text
        movement = movement_response.json()

        scan_response = client.post(
            "/api/v1/plugins/logistics/scan",
            headers=headers,
            json={
                "movement_id": movement["id"],
                "barcode_serial": "MAT-200001",
                "service_type": "VENTA",
                "gps_lat": -12.04318,
                "gps_lng": -77.02824,
            },
        )
        assert scan_response.status_code == 201, scan_response.text
        assert scan_response.json()["result"] == "OK"
        assert scan_response.json()["gps_lat"] == -12.04318

        cylinder_after_scan = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}",
            headers=headers,
        )
        assert cylinder_after_scan.status_code == 200
        assert cylinder_after_scan.json()["current_state"] == "EN_CLIENTE_LLENO"

        confirm_response = client.post(
            f"/api/v1/plugins/logistics/movements/{movement['id']}/confirm",
            headers=headers,
        )
        assert confirm_response.status_code == 200, confirm_response.text
        assert confirm_response.json()["status"] == "COMPLETADO"

        ownership_response = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/ownership",
            headers=headers,
        )
        assert ownership_response.status_code == 200, ownership_response.text
        assert ownership_response.json()[0]["customer_name"] == "GLP Campo SAC"

        service_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/services",
            headers=headers,
            json={
                "service_type_id": service_type["id"],
                "status": "PENDIENTE",
                "total_amount": 55,
            },
        )
        assert service_response.status_code == 201, service_response.text
        service = service_response.json()

        service_update_response = client.patch(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/services/{service['id']}",
            headers=headers,
            json={"status": "REALIZADO"},
        )
        assert service_update_response.status_code == 200, service_update_response.text
        assert service_update_response.json()["status"] == "REALIZADO"

        scan_log_response = client.get(
            f"/api/v1/plugins/logistics/scan/log/{movement['id']}",
            headers=headers,
        )
        assert scan_log_response.status_code == 200, scan_log_response.text
        assert len(scan_log_response.json()) == 1

        service_delete_response = client.delete(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/services/{service['id']}",
            headers=headers,
        )
        assert service_delete_response.status_code == 204, service_delete_response.text

    with app.state.session_factory() as db:
        events = list(
            db.scalars(
                select(EventLog).where(
                    EventLog.module == "logistics",
                    EventLog.tenant_id == seeded_demo["tenant_id"],
                )
            ).all()
        )

    event_names = {event.event_name for event in events}
    assert "logistics.cylinder.updated" in event_names
    assert "logistics.cylinder.retimbrado_registered" in event_names
    assert "logistics.cylinder.label_printed" in event_names
    assert "logistics.cylinder.scanned" in event_names
    assert "logistics.cylinder.service_registered" in event_names


def test_logistics_plugin_spec_0014_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = create_customer(
            client,
            headers,
            name="Operaciones GLP SAC",
            document_number="20100070970",
        )
        warehouse = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Planta Central", "code": "PC", "address": "Av. Central 100"},
        ).json()
        zone = client.post(
            "/api/v1/plugins/logistics/zones",
            headers=headers,
            json={"name": "Zona Norte", "code": "ZNORTE"},
        ).json()
        vehicle = client.post(
            "/api/v1/plugins/logistics/vehicles",
            headers=headers,
            json={
                "plate": "PLN-001",
                "vehicle_type": "Camion",
                "capacity_weight": 2000,
                "useful_load": 2000,
                "warehouse_id": warehouse["id"],
            },
        ).json()
        delivery_point = client.post(
            "/api/v1/plugins/logistics/delivery-points",
            headers=headers,
            json={
                "customer_id": customer["id"],
                "contact_name": "Jose Perez",
                "address": "Calle Norte 123",
                "zone_id": zone["id"],
                "warehouse_id": warehouse["id"],
                "is_primary": True,
            },
        ).json()
        route = client.post(
            "/api/v1/plugins/logistics/routes",
            headers=headers,
            json={
                "route_date": datetime.now(UTC).date().isoformat(),
                "vehicle_id": vehicle["id"],
            },
        ).json()
        stop = client.post(
            f"/api/v1/plugins/logistics/routes/{route['id']}/stops",
            headers=headers,
            json={"delivery_point_id": delivery_point["id"], "stop_order": 1},
        ).json()

        weekdays_response = client.patch(
            f"/api/v1/plugins/logistics/routes/{route['id']}/weekly-schedule",
            headers=headers,
            json={"weekdays": [1, 3, 5]},
        )
        assert weekdays_response.status_code == 200, weekdays_response.text

        filtered_routes = client.get(
            "/api/v1/plugins/logistics/routes",
            headers=headers,
            params={"weekday": 1},
        )
        assert filtered_routes.status_code == 200
        assert any(item["id"] == route["id"] for item in filtered_routes.json())

        product = create_product(client, headers, sku="GLP10", name="GLP 10KG")

        stock_config_response = client.put(
            "/api/v1/plugins/stock/config",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "min_quantity": 5,
                "max_quantity": 100,
                "is_active": True,
            },
        )
        assert stock_config_response.status_code == 200, stock_config_response.text

        stock_adjust_response = client.post(
            "/api/v1/plugins/stock/adjust",
            headers=headers,
            json={
                "product_id": product["id"],
                "warehouse_id": warehouse["id"],
                "quantity": 25,
                "reason": "Stock inicial test logistics 0014",
                "idempotency_key": "logistics-0014-initial",
            },
        )
        assert stock_adjust_response.status_code == 201, stock_adjust_response.text

        order = client.post(
            "/api/v1/plugins/logistics/orders",
            headers=headers,
            json={
                "customer_id": customer["id"],
                "movement_type": "SC",
                "warehouse_id": warehouse["id"],
            },
        ).json()
        order_item = client.post(
            f"/api/v1/plugins/logistics/orders/{order['id']}/items",
            headers=headers,
            json={
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity_requested": 6,
            },
        ).json()

        planning_stock = client.get(
            "/api/v1/plugins/logistics/planning/stock",
            headers=headers,
            params={"warehouse_id": warehouse["id"], "product_ids": product["id"]},
        )
        assert planning_stock.status_code == 200, planning_stock.text
        assert planning_stock.json()[0]["stock_actual"] == 25

        plan_order_response = client.post(
            f"/api/v1/plugins/logistics/planning/plan-order/{order['id']}",
            headers=headers,
            json={"mode": "full", "permit_without_stock": False},
        )
        assert plan_order_response.status_code == 200, plan_order_response.text
        assert plan_order_response.json()["updated_items"][0]["quantity_planned"] == 6

        pending_orders = client.get(
            "/api/v1/plugins/logistics/planning/pending-orders",
            headers=headers,
            params={"warehouse_id": warehouse["id"]},
        )
        assert pending_orders.status_code == 200
        assert pending_orders.json()[0]["coverage_status"] == "green"

        preload = client.post(
            "/api/v1/plugins/logistics/planning/generate-preload",
            headers=headers,
            json={
                "warehouse_id": warehouse["id"],
                "preload_date": datetime.now(UTC).date().isoformat(),
                "order_ids": [order["id"]],
                "notes": "Preload test",
            },
        )
        assert preload.status_code == 201, preload.text
        preload_data = preload.json()

        preload_detail = client.get(
            f"/api/v1/plugins/logistics/planning/preloads/{preload_data['id']}",
            headers=headers,
        )
        assert preload_detail.status_code == 200
        assert preload_detail.json()["items"][0]["order_item_id"] == order_item["id"]

        accepted_preload = client.post(
            f"/api/v1/plugins/logistics/planning/preloads/{preload_data['id']}/accept",
            headers=headers,
        )
        assert accepted_preload.status_code == 200, accepted_preload.text
        preload_result = accepted_preload.json()
        dispatch_movement = preload_result["movement"]

        waybill_response = client.get(
            f"/api/v1/plugins/logistics/waybill/{dispatch_movement['id']}",
            headers=headers,
        )
        assert waybill_response.status_code == 200, waybill_response.text
        assert waybill_response.json()["items"][0]["product_id"] == product["id"]

        guide_response = client.patch(
            f"/api/v1/plugins/logistics/movements/{dispatch_movement['id']}/guide",
            headers=headers,
            json={"document_series": "G001"},
        )
        assert guide_response.status_code == 200, guide_response.text
        assert guide_response.json()["full_document"].startswith("G001-")

        dispatch_close = client.post(
            f"/api/v1/plugins/logistics/movements/{dispatch_movement['id']}/close-dispatch",
            headers=headers,
        )
        assert dispatch_close.status_code == 200, dispatch_close.text
        assert dispatch_close.json()["status"] == "DESPACHADO"

        stock_after_dispatch = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert stock_after_dispatch.status_code == 200, stock_after_dispatch.text
        assert stock_after_dispatch.json()["quantity"] == 19

        dispatch_ticket = client.get(
            f"/api/v1/plugins/logistics/reports/dispatch-ticket/{dispatch_movement['id']}",
            headers=headers,
        )
        assert dispatch_ticket.status_code == 200

        albaran = client.get(
            f"/api/v1/plugins/logistics/reports/transfer-albaran/{dispatch_movement['id']}",
            headers=headers,
        )
        assert albaran.status_code == 200

        equipment = client.post(
            "/api/v1/plugins/logistics/equipment",
            headers=headers,
            json={"name": "Manguera GLP", "equipment_type": "MANGUERA", "is_active": True},
        )
        assert equipment.status_code == 201, equipment.text
        equipment_data = equipment.json()

        assignment = client.post(
            f"/api/v1/plugins/logistics/movements/{dispatch_movement['id']}/equipment",
            headers=headers,
            json={"equipment_id": equipment_data['id'], "notes": "Asignacion test"},
        )
        assert assignment.status_code == 201, assignment.text
        assignment_data = assignment.json()

        assignment_return = client.patch(
            f"/api/v1/plugins/logistics/movements/{dispatch_movement['id']}/equipment/{assignment_data['id']}/return",
            headers=headers,
            json={"notes": "Devuelto"},
        )
        assert assignment_return.status_code == 200, assignment_return.text

        restrictions = client.post(
            f"/api/v1/plugins/logistics/vehicles/{vehicle['id']}/route-restrictions",
            headers=headers,
            json={"restrictions": [{"route_id": route['id'], "restriction_type": "ALLOW"}]},
        )
        assert restrictions.status_code == 200, restrictions.text

        eligible_route_vehicles = client.get(
            f"/api/v1/plugins/logistics/routes/{route['id']}/eligible-vehicles",
            headers=headers,
        )
        assert eligible_route_vehicles.status_code == 200
        assert any(item["vehicle_id"] == vehicle["id"] and item["eligible"] for item in eligible_route_vehicles.json())

        driver_params = client.put(
            f"/api/v1/plugins/logistics/drivers/{seeded_demo['user_id']}/parameters",
            headers=headers,
            json={"parameters": {"max_weight_kg": "2500", "turno": "manana"}},
        )
        assert driver_params.status_code == 200, driver_params.text

        linked_dp = client.post(
            f"/api/v1/plugins/logistics/vehicles/{vehicle['id']}/delivery-points",
            headers=headers,
            json={"delivery_point_id": delivery_point['id']},
        )
        assert linked_dp.status_code == 201, linked_dp.text

        route_agenda_tasks = client.post(
            f"/api/v1/plugins/logistics/routes/{route['id']}/agenda-tasks",
            headers=headers,
        )
        assert route_agenda_tasks.status_code == 200, route_agenda_tasks.text
        agenda_task = route_agenda_tasks.json()[0]

        agenda_summary = client.get(
            "/api/v1/plugins/logistics/agenda/daily-summary",
            headers=headers,
            params={"date": datetime.now(UTC).date().isoformat()},
        )
        assert agenda_summary.status_code == 200, agenda_summary.text
        assert len(agenda_summary.json()) >= 1

        adr_config = client.put(
            f"/api/v1/plugins/logistics/adr/product-config/{product['id']}",
            headers=headers,
            json={
                "adr_class": "2F",
                "adr_points": 3,
                "adr_tunnel": "B/D",
                "max_quantity": 100,
                "valid_from": datetime.now(UTC).date().isoformat(),
            },
        )
        assert adr_config.status_code == 200, adr_config.text

        adr_incompatibility = client.post(
            "/api/v1/plugins/logistics/adr/incompatibilities",
            headers=headers,
            json={"product_id_1": product["id"], "product_id_2": product["id"] + "-X"},
        )
        assert adr_incompatibility.status_code == 201, adr_incompatibility.text

        adr_points = client.get(
            f"/api/v1/plugins/logistics/adr/points/{dispatch_movement['id']}",
            headers=headers,
        )
        assert adr_points.status_code == 200, adr_points.text
        assert adr_points.json()["total_adr_points"] >= 18

        adr_eligible_vehicles = client.get(
            f"/api/v1/plugins/logistics/adr/eligible-vehicles/{dispatch_movement['id']}",
            headers=headers,
        )
        assert adr_eligible_vehicles.status_code == 200, adr_eligible_vehicles.text

        route_gps = client.patch(
            f"/api/v1/plugins/logistics/routes/{route['id']}/gps-start",
            headers=headers,
            json={"gps_coordinates": {"lat": -12.04, "lng": -77.03}},
        )
        assert route_gps.status_code == 200, route_gps.text

        stop_gps = client.patch(
            f"/api/v1/plugins/logistics/routes/{route['id']}/stops/{stop['id']}/gps",
            headers=headers,
            json={"gps_coordinates": {"lat": -12.05, "lng": -77.02}},
        )
        assert stop_gps.status_code == 200, stop_gps.text

        task_gps = client.patch(
            f"/api/v1/plugins/logistics/agenda/tasks/{agenda_task['id']}/gps",
            headers=headers,
            json={"gps_coordinates": {"lat": -12.06, "lng": -77.01}},
        )
        assert task_gps.status_code == 200, task_gps.text

        cylinder = client.post(
            "/api/v1/plugins/logistics/cylinders",
            headers=headers,
            json={
                "serial": "GLP-WEIGHT-01",
                "location": "Planta Central",
                "weight_origin": 12.5,
                "weight_current": 22.5,
                "content_kg": 10,
            },
        ).json()

        available_with_weight = client.get(
            "/api/v1/plugins/logistics/cylinders/available-with-weight",
            headers=headers,
            params={"warehouse_id": warehouse["id"]},
        )
        assert available_with_weight.status_code == 200, available_with_weight.text

        cylinder_weight = client.get(
            f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/weight",
            headers=headers,
        )
        assert cylinder_weight.status_code == 200, cylinder_weight.text
        assert cylinder_weight.json()["tara_weight_kg"] == 12.5

        load = client.post(
            "/api/v1/plugins/logistics/loads",
            headers=headers,
            json={"route_id": route["id"], "cylinder_id": cylinder["id"], "stop_id": stop["id"]},
        )
        assert load.status_code == 201, load.text

        load_weight = client.get(
            "/api/v1/plugins/logistics/loads/weight-summary",
            headers=headers,
            params={"route_id": route["id"]},
        )
        assert load_weight.status_code == 200, load_weight.text
        assert load_weight.json()["total_weight_kg"] >= 22.5

        route_agenda_report = client.get(
            f"/api/v1/plugins/logistics/reports/route-agenda/{route['id']}",
            headers=headers,
        )
        assert route_agenda_report.status_code == 200, route_agenda_report.text

        load_summary_report = client.get(
            f"/api/v1/plugins/logistics/reports/load-summary/{route['id']}",
            headers=headers,
        )
        assert load_summary_report.status_code == 200, load_summary_report.text

        product_content = client.get(
            f"/api/v1/plugins/logistics/products/{product['id']}/content",
            headers=headers,
        )
        assert product_content.status_code == 200, product_content.text
        assert product_content.json()["content_kg"] == 10

        reception_movement = client.post(
            "/api/v1/plugins/logistics/movements",
            headers=headers,
            json={
                "movement_type": "TR",
                "warehouse_id": warehouse["id"],
                "items": [
                    {
                        "product_id": product["id"],
                        "product_name": product["name"],
                        "quantity_in": 2,
                    }
                ],
            },
        )
        assert reception_movement.status_code == 201, reception_movement.text
        reception_movement_data = reception_movement.json()

        movement_status_update = client.patch(
            f"/api/v1/plugins/logistics/movements/{reception_movement_data['id']}",
            headers=headers,
            json={"status": "DESCARGADO_POR_RECEPCIONAR"},
        )
        assert movement_status_update.status_code == 200, movement_status_update.text

        reception_pending = client.get(
            "/api/v1/plugins/logistics/reception/pending",
            headers=headers,
            params={"warehouse_id": warehouse["id"]},
        )
        assert reception_pending.status_code == 200, reception_pending.text
        assert any(item["id"] == reception_movement_data["id"] for item in reception_pending.json())

        reception_items = client.get(
            f"/api/v1/plugins/logistics/movements/{reception_movement_data['id']}/items",
            headers=headers,
        ).json()
        reception_item = reception_items[0]

        incident_reasons = client.get(
            "/api/v1/plugins/logistics/reception/incident-reasons",
            headers=headers,
        )
        assert incident_reasons.status_code == 200, incident_reasons.text

        incident = client.post(
            f"/api/v1/plugins/logistics/reception/{reception_movement_data['id']}/incident",
            headers=headers,
            json={"reason_code": "FALTANTE", "description": "Bulto incompleto"},
        )
        assert incident.status_code == 201, incident.text

        receive = client.post(
            f"/api/v1/plugins/logistics/reception/{reception_movement_data['id']}/receive",
            headers=headers,
            json={"items": [{"movement_item_id": reception_item['id'], "quantity_received": 1}]},
        )
        assert receive.status_code == 200, receive.text
        assert receive.json()["movement"]["status"] == "RECEPCIONADO"
        assert len(receive.json()["shortage_items"]) == 1

        stock_after_reception = client.get(
            f"/api/v1/plugins/stock/balance/{product['id']}/{warehouse['id']}",
            headers=headers,
        )
        assert stock_after_reception.status_code == 200, stock_after_reception.text
        assert stock_after_reception.json()["quantity"] == 20

        unlink_delivery_point = client.delete(
            f"/api/v1/plugins/logistics/vehicles/{vehicle['id']}/delivery-points/{delivery_point['id']}",
            headers=headers,
        )
        assert unlink_delivery_point.status_code == 204, unlink_delivery_point.text
