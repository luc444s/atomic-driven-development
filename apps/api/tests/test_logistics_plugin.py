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
