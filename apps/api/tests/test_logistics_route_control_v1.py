from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from apps.api.tests.test_logistics_route_operation_effects import _create_outbound_session_context


def test_vehicle_session_location_tracking_updates_control_state(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="CTRL-GLP10",
        name="Bombona 10kg Control",
    )
    headers = ctx["headers"]
    session = ctx["session"]
    stop = ctx["stop"]

    location_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/location",
        headers=headers,
        json={
            "lat": -12.0464,
            "lng": -77.0428,
            "speed": 18.5,
            "heading": 180,
            "accuracy_meters": 8,
            "recorded_at": datetime.now(UTC).isoformat(),
            "source": "WEB",
        },
    )
    assert location_response.status_code == 201, location_response.text
    location_event = location_response.json()
    assert location_event["session_id"] == session["id"]

    control_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/control-state",
        headers=headers,
    )
    assert control_response.status_code == 200, control_response.text
    control_state = control_response.json()
    assert control_state["status"] == "EN_RUTA"
    assert control_state["current_stop_id"] == stop["id"]
    assert control_state["total_stops"] == 1

    arrive_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/stops/{stop['id']}/arrive",
        headers=headers,
    )
    assert arrive_response.status_code == 200, arrive_response.text
    assert arrive_response.json()["status"] == "EN_PARADA"
    assert arrive_response.json()["active_stop_id"] == stop["id"]

    history_response = client.get(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/location-history",
        headers=headers,
    )
    assert history_response.status_code == 200, history_response.text
    assert len(history_response.json()) == 1


def test_confirm_route_event_captures_latest_location_snapshot(
    client: TestClient, app, seeded_demo: dict[str, str]
) -> None:
    ctx = _create_outbound_session_context(
        client,
        app,
        seeded_demo,
        sku="SNAP-GLP10",
        name="Bombona 10kg Snapshot",
    )
    headers = ctx["headers"]
    product = ctx["product"]
    session = ctx["session"]
    stop = ctx["stop"]

    waybill_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/carta-porte/regenerate",
        headers=headers,
        json={
            "reason": "Generación inicial en ruta",
            "event": "INITIAL_GENERATION",
            "idempotency_key": "route-control-snapshot-waybill",
        },
    )
    assert waybill_response.status_code == 200, waybill_response.text

    location_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/location",
        headers=headers,
        json={
            "lat": -12.05,
            "lng": -77.03,
            "speed": 4.5,
            "heading": 90,
            "accuracy_meters": 5,
            "recorded_at": datetime.now(UTC).isoformat(),
            "source": "WEB",
        },
    )
    assert location_response.status_code == 201, location_response.text
    location_event = location_response.json()

    confirm_response = client.post(
        f"/api/v1/plugins/logistics/vehicle-sessions/{session['id']}/route-events/confirm",
        headers=headers,
        json={
            "route_stop_id": stop["id"],
            "context_type": "STOP",
            "customer_id": None,
            "warehouse_id": None,
            "operation_type": "DELIVERY",
            "notes": "Entrega con snapshot espacial",
            "idempotency_key": "route-control-snapshot-confirm",
            "items": [
                {
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "quantity": 1,
                    "direction": "OUT",
                }
            ],
            "incident_mode": "NONE",
            "type": None,
            "related_operation_id": None,
            "target_incident_id": None,
            "incident_notes": None,
        },
    )
    assert confirm_response.status_code == 200, confirm_response.text
    operation = confirm_response.json()
    assert operation["location_event_id"] == location_event["id"]
    assert operation["location_lat"] == -12.05
    assert operation["location_lng"] == -77.03
