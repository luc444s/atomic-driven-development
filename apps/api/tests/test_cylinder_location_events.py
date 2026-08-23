"""Prueba: trazabilidad de cilindros via lg_cylinder_events."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_customer,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
    enable_productos_plugin,
    enable_stock_plugin,
)


@pytest.mark.usefixtures("app")
def test_cylinder_events_endpoint(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    """Verifica que el endpoint GET /cylinders/{id}/events y /location respondan."""
    enable_productos_plugin(app, seeded_demo)
    enable_crm_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)
    enable_stock_plugin(app, seeded_demo)
    headers = auth_headers(client)

    customer = create_customer(client, headers, name="Cliente Traza", document_number="20100070970")

    warehouse_response = client.post(
        "/api/v1/plugins/logistics/warehouses",
        headers=headers,
        json={"name": "Almacen Traza", "code": "ALM-TZ", "address": None, "phone": None},
    )
    assert warehouse_response.status_code == 201, warehouse_response.text
    warehouse = warehouse_response.json()

    vehicle_response = client.post(
        "/api/v1/plugins/logistics/vehicles",
        headers=headers,
        json={
            "plate": "TRK-TZ",
            "vehicle_type": "Camion",
            "brand": "Test",
            "model": "TZ",
            "capacity_weight": 2000,
            "useful_load": 2000,
            "warehouse_id": warehouse["id"],
        },
    )
    assert vehicle_response.status_code == 201, vehicle_response.text
    vehicle = vehicle_response.json()

    product = create_product(client, headers, sku="TZ-CYL-GAS", name="Gas Traza 10kg")

    # Crear cilindro
    cylinder_response = client.post(
        "/api/v1/plugins/logistics/cylinders",
        headers=headers,
        json={
            "serial": "TZ-CYL-001",
            "product_id": product["id"],
            "current_state": "EN_ALMACEN_VACIO",
            "warehouse_id": warehouse["id"],
            "entry_mode": "EMPTY_FROM_CUSTOMER",
            "location": warehouse["name"],
            "customer_id": customer["id"],
        },
    )
    assert cylinder_response.status_code == 201, cylinder_response.text
    cylinder = cylinder_response.json()

    # El alta registra un evento WAREHOUSE_IN (trazabilidad de ubicaciones).
    events_response = client.get(
        f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/events",
        headers=headers,
    )
    assert events_response.status_code == 200, events_response.text
    events = events_response.json()
    assert isinstance(events, list)
    warehouse_in = [e for e in events if e["event_type"] == "WAREHOUSE_IN"]
    assert warehouse_in, "alta de cilindro deberia registrar WAREHOUSE_IN"

    # La ubicacion inicial del cilindro es el almacen de alta.
    location_response = client.get(
        f"/api/v1/plugins/logistics/cylinders/{cylinder['id']}/location",
        headers=headers,
    )
    assert location_response.status_code == 200, location_response.text
    location = location_response.json()
    assert location["location_type"] == "WAREHOUSE"
    assert location["location_id"] == warehouse["id"]
