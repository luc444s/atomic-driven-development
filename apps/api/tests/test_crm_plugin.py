from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.api.v1.core.common import CoreActionContext
from apps.api.app.api.v1.core.services.plugins import set_core_plugin_enabled
from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.core.lifecycle import bootstrap_app_state
from apps.api.app.kernel.plugins.persistent import sync_plugin_registry_state


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


def test_crm_plugin_customer_flow(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        document_types_response = client.get(
            "/api/v1/plugins/crm/catalog/document-types?country_code=PER",
            headers=headers,
        )
        assert document_types_response.status_code == 200, document_types_response.text
        assert any(item["code"] == "RUC" for item in document_types_response.json())

        payment_terms_response = client.get(
            "/api/v1/plugins/crm/catalog/payment-terms",
            headers=headers,
        )
        assert payment_terms_response.status_code == 200, payment_terms_response.text
        assert any(item["code"] == "CONTADO" for item in payment_terms_response.json())

        customer_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "external_code": "CLI-0001",
                "legal_name": "GLP Norte SAC",
                "commercial_name": "GLP Norte",
                "document_type_code": "RUC",
                "document_number": "20100070970",
                "country_code": "PER",
                "email": "ventas@glpnorte.pe",
                "phone": "014445555",
                "payment_term_code": "CONTADO",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        assert customer_response.status_code == 201, customer_response.text
        customer = customer_response.json()

        duplicate_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "Duplicado SAC",
                "document_type_code": "RUC",
                "document_number": "20100070970",
                "country_code": "PER",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        assert duplicate_response.status_code == 409

        search_response = client.get(
            "/api/v1/plugins/crm/customers/search?query=GLP",
            headers=headers,
        )
        assert search_response.status_code == 200, search_response.text
        assert search_response.json()[0]["id"] == customer["id"]
        assert search_response.json()[0]["commercial_name"] == "GLP Norte"
        assert search_response.json()[0]["display_name"] == "GLP Norte"

        address_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer['id']}/addresses",
            headers=headers,
            json={
                "address_type": "FISCAL",
                "label": "Fiscal",
                "line1": "Av. Peru 123",
                "district": "Lima",
                "country_code": "PER",
                "geocode_source": "MANUAL",
            },
        )
        assert address_response.status_code == 201, address_response.text
        address = address_response.json()

        fiscal_response = client.put(
            f"/api/v1/plugins/crm/customers/{customer['id']}/fiscal-address/{address['id']}",
            headers=headers,
        )
        assert fiscal_response.status_code == 200, fiscal_response.text
        assert fiscal_response.json()["fiscal_address_id"] == address["id"]

        commercial_address_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer['id']}/addresses",
            headers=headers,
            json={
                "address_type": "COMERCIAL",
                "label": "Oficina Madrid",
                "line1": "Calle Mayor 10",
                "city": "Madrid",
                "country_code": "ESP",
                "geocode_source": "MANUAL",
            },
        )
        assert commercial_address_response.status_code == 201, commercial_address_response.text

        locality_search_response = client.get(
            "/api/v1/plugins/crm/customers/search?query=Madrid",
            headers=headers,
        )
        assert locality_search_response.status_code == 200, locality_search_response.text
        assert locality_search_response.json()[0]["id"] == customer["id"]
        assert locality_search_response.json()[0]["locality_summary"] in {"Lima", "Madrid"}

        contact_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer['id']}/contacts",
            headers=headers,
            json={
                "contact_type": "EMAIL",
                "value": "cobranzas@glpnorte.pe",
                "label": "Cobranza",
                "is_primary": True,
            },
        )
        assert contact_response.status_code == 201, contact_response.text

        detail_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer['id']}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        detail = detail_response.json()
        assert detail["fiscal_address_id"] == address["id"]
        assert len(detail["addresses"]) == 2
        assert {item["address_type"] for item in detail["addresses"]} == {"FISCAL", "COMERCIAL"}
        assert len(detail["contacts"]) == 1

        disable_response = client.patch(
            f"/api/v1/plugins/crm/customers/{customer['id']}/toggle-active",
            headers=headers,
            json={"is_active": False, "reason": "Cierre comercial"},
        )
        assert disable_response.status_code == 200, disable_response.text
        assert disable_response.json()["is_active"] is False


def test_crm_plugin_validates_invalid_document(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        invalid_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "Cliente Invalido",
                "document_type_code": "RUC",
                "document_number": "123",
                "country_code": "PER",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        assert invalid_response.status_code == 400
        assert "RUC" in str(invalid_response.json()["detail"])
