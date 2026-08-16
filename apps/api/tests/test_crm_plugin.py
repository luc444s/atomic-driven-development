from __future__ import annotations

from fastapi.testclient import TestClient
from systutor.api.v1.core.common import CoreActionContext
from systutor.api.v1.core.services.plugins import set_core_plugin_enabled
from systutor.core.lifecycle import bootstrap_app_state
from systutor.kernel.plugins.persistent import sync_plugin_registry_state

from apps.api.app.commands.seed_demo import seed_demo_data


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
            "/api/v1/plugins/crm/catalog/document-types?country_code=PE",
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
                "country_code": "PE",
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
                "country_code": "PE",
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
                "country_code": "PE",
                "is_operational_site": False,
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
                "is_operational_site": True,
                "geocode_source": "MANUAL",
            },
        )
        assert commercial_address_response.status_code == 201, commercial_address_response.text
        commercial_address = commercial_address_response.json()
        assert commercial_address["is_operational_site"] is True

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
                "full_name": "Maria Cobranza",
                "label": "Cobranza",
                "role": "Responsable de cobranzas",
                "phone": "014448888",
                "email": "cobranzas@glpnorte.pe",
                "address_id": commercial_address["id"],
                "contact_purpose": "COBRANZA",
                "notes": "Atiende pagos y seguimiento",
                "is_primary": True,
            },
        )
        assert contact_response.status_code == 201, contact_response.text
        created_contact = contact_response.json()
        assert created_contact["full_name"] == "Maria Cobranza"
        assert created_contact["email"] == "cobranzas@glpnorte.pe"
        assert created_contact["address_id"] == commercial_address["id"]
        assert created_contact["contact_purpose"] == "COBRANZA"
        assert created_contact["notes"] == "Atiende pagos y seguimiento"

        update_contact_response = client.put(
            f"/api/v1/plugins/crm/contacts/{created_contact['id']}",
            headers=headers,
            json={
                "contact_purpose": "FACTURACION",
                "notes": "Nuevo circuito de facturación",
                "is_primary": True,
            },
        )
        assert update_contact_response.status_code == 200, update_contact_response.text
        assert update_contact_response.json()["contact_purpose"] == "FACTURACION"

        filtered_contacts_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer['id']}/contacts?contact_purpose=FACTURACION",
            headers=headers,
        )
        assert filtered_contacts_response.status_code == 200, filtered_contacts_response.text
        assert len(filtered_contacts_response.json()) == 1

        foreign_contact_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer['id']}/contacts",
            headers=headers,
            json={
                "contact_type": "PHONE",
                "full_name": "Contacto invalido",
                "phone": "999999999",
                "address_id": "direccion-ajena",
                "contact_purpose": "GENERAL",
                "is_primary": False,
            },
        )
        assert foreign_contact_response.status_code == 400

        commercial_users_response = client.get(
            "/api/v1/plugins/crm/commercial/users",
            headers=headers,
        )
        assert commercial_users_response.status_code == 200, commercial_users_response.text
        assert any(
            item["id"] == seeded_demo["user_id"]
            for item in commercial_users_response.json()
        )

        assignment_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer['id']}/commercial-assignments",
            headers=headers,
            json={
                "address_id": commercial_address["id"],
                "user_id": seeded_demo["user_id"],
                "assignment_role": "AGENT",
                "notes": "Cuenta atendida desde oficina central",
                "is_primary": True,
            },
        )
        assert assignment_response.status_code == 201, assignment_response.text
        assignment = assignment_response.json()
        assert assignment["assignment_role"] == "AGENT"
        assert assignment["user_id"] == seeded_demo["user_id"]

        assignment_list_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer['id']}/commercial-assignments?assignment_role=AGENT",
            headers=headers,
        )
        assert assignment_list_response.status_code == 200, assignment_list_response.text
        assert len(assignment_list_response.json()) == 1

        assignment_update_response = client.put(
            f"/api/v1/plugins/crm/commercial-assignments/{assignment['id']}",
            headers=headers,
            json={
                "assignment_role": "SUPERVISOR",
                "notes": "Escalado a supervisor de zona",
            },
        )
        assert assignment_update_response.status_code == 200, assignment_update_response.text
        assert assignment_update_response.json()["assignment_role"] == "SUPERVISOR"

        detail_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer['id']}",
            headers=headers,
        )
        assert detail_response.status_code == 200, detail_response.text
        detail = detail_response.json()
        assert detail["fiscal_address_id"] == address["id"]
        assert len(detail["addresses"]) == 2
        assert {item["address_type"] for item in detail["addresses"]} == {"FISCAL", "COMERCIAL"}
        assert any(item["is_operational_site"] for item in detail["addresses"])
        assert len(detail["contacts"]) == 1
        assert detail["contacts"][0]["full_name"] == "Maria Cobranza"
        assert detail["contacts"][0]["contact_purpose"] == "FACTURACION"

        delete_assignment_response = client.delete(
            f"/api/v1/plugins/crm/commercial-assignments/{assignment['id']}",
            headers=headers,
        )
        assert delete_assignment_response.status_code == 204, delete_assignment_response.text

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
                "country_code": "PE",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        assert invalid_response.status_code == 400
        assert "RUC" in str(invalid_response.json()["detail"])


def test_crm_customer_fiscal_fields(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        customer_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "FiscalTest SL",
                "document_type_code": "NIF",
                "document_number": "B12345678",
                "country_code": "ESP",
                "billing_type": "mensual",
                "accounting_code": "43000001",
                "is_intracommunity": True,
                "fiscal_operation_key": "E",
                "tax_regime_code": "GENERAL",
                "equivalence_surcharge_applicable": True,
                "cash_criterion_applicable": False,
                "is_exempt": True,
            },
        )
        assert customer_response.status_code == 201, customer_response.text
        customer = customer_response.json()
        assert customer["accounting_code"] == "43000001"
        assert customer["is_intracommunity"] is True
        assert customer["fiscal_operation_key"] == "E"
        assert customer["tax_regime_code"] == "GENERAL"
        assert customer["equivalence_surcharge_applicable"] is True
        assert customer["cash_criterion_applicable"] is False
        assert customer["is_exempt"] is True
        assert customer["billing_type"] == "mensual"

        update_response = client.put(
            f"/api/v1/plugins/crm/customers/{customer['id']}",
            headers=headers,
            json={
                "accounting_code": "43000002",
                "is_intracommunity": False,
                "fiscal_operation_key": "S",
                "equivalence_surcharge_applicable": False,
                "cash_criterion_applicable": True,
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["accounting_code"] == "43000002"
        assert updated["is_intracommunity"] is False
        assert updated["fiscal_operation_key"] == "S"
        assert updated["equivalence_surcharge_applicable"] is False
        assert updated["cash_criterion_applicable"] is True


def test_crm_billing_type_validation(app) -> None:
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
                "legal_name": "BadBilling SL",
                "document_type_code": "NIF",
                "document_number": "A12345678",
                "country_code": "ESP",
                "billing_type": "trimestral",
                "is_exempt": False,
            },
        )
        assert invalid_response.status_code == 422


def test_crm_payment_terms_have_payment_mode(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        response = client.get(
            "/api/v1/plugins/crm/catalog/payment-terms",
            headers=headers,
        )
        assert response.status_code == 200, response.text
        terms = response.json()
        assert len(terms) >= 10

        term_codes = {item["code"] for item in terms}
        assert "REMESA_15" in term_codes
        assert "REMESA_30" in term_codes
        assert "REMESA_60" in term_codes

        for term in terms:
            assert "payment_mode" in term
            assert term["payment_mode"] in {
                "CONTADO", "TRANSFERENCIA", "REMESA", "CHEQUE", "TARJETA",
            }


def test_crm_bank_accounts_crud(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        customer_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "BancoTest SL",
                "document_type_code": "NIF",
                "document_number": "C12345678",
                "country_code": "ESP",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        customer_id = customer_response.json()["id"]

        account_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/bank-accounts",
            headers=headers,
            json={
                "bank_name": "BBVA",
                "account_holder": "BancoTest SL",
                "iban": "ES9121000418450200051332",
                "bic_swift": "BBVAESMM",
                "is_primary": True,
                "notes": "Cuenta principal",
            },
        )
        assert account_response.status_code == 201, account_response.text
        account = account_response.json()
        assert account["bank_name"] == "BBVA"
        assert account["iban"] == "ES9121000418450200051332"
        assert account["is_primary"] is True

        second_account_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/bank-accounts",
            headers=headers,
            json={
                "bank_name": "Santander",
                "account_holder": "BancoTest SL",
                "iban": "ES4500493492412322413742",
                "is_primary": True,
            },
        )
        assert second_account_response.status_code == 201

        list_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer_id}/bank-accounts",
            headers=headers,
        )
        assert list_response.status_code == 200, list_response.text
        accounts = list_response.json()
        assert len(accounts) == 2
        primary_accounts = [a for a in accounts if a["is_primary"]]
        assert len(primary_accounts) == 1
        assert primary_accounts[0]["bank_name"] == "Santander"

        update_response = client.put(
            f"/api/v1/plugins/crm/bank-accounts/{account['id']}",
            headers=headers,
            json={
                "bank_name": "BBVA Updated",
                "notes": "Nota actualizada",
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["bank_name"] == "BBVA Updated"
        assert updated["notes"] == "Nota actualizada"

        delete_response = client.delete(
            f"/api/v1/plugins/crm/bank-accounts/{account['id']}",
            headers=headers,
        )
        assert delete_response.status_code == 204, delete_response.text

        final_list_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer_id}/bank-accounts",
            headers=headers,
        )
        assert len(final_list_response.json()) == 1


def test_crm_pricing_terms_product_scope(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        customer_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "PricingTest SL",
                "document_type_code": "NIF",
                "document_number": "D12345678",
                "country_code": "ESP",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        customer_id = customer_response.json()["id"]

        term_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
            json={
                "scope_type": "PRODUCT",
                "product_id": "prod-uuid-test-001",
                "pricing_mode": "FIXED_PRICE",
                "fixed_amount": "45.5000",
                "currency": "EUR",
                "valid_from": "2026-01-01T00:00:00Z",
                "source_quote_ref": "COT-2026-001",
                "notes": "Precio especial GLP industrial",
            },
        )
        assert term_response.status_code == 201, term_response.text
        term = term_response.json()
        assert term["scope_type"] == "PRODUCT"
        assert term["product_id"] == "prod-uuid-test-001"
        assert term["pricing_mode"] == "FIXED_PRICE"
        assert term["fixed_amount"] == "45.5000"
        assert term["currency"] == "EUR"
        assert term["source_quote_ref"] == "COT-2026-001"

        update_response = client.put(
            f"/api/v1/plugins/crm/pricing-terms/{term['id']}",
            headers=headers,
            json={
                "fixed_amount": "42.0000",
                "notes": "Renegociado",
            },
        )
        assert update_response.status_code == 200, update_response.text
        updated = update_response.json()
        assert updated["fixed_amount"] == "42.0000"
        assert updated["notes"] == "Renegociado"

        delete_response = client.delete(
            f"/api/v1/plugins/crm/pricing-terms/{term['id']}",
            headers=headers,
        )
        assert delete_response.status_code == 204, delete_response.text


def test_crm_pricing_terms_global_discount(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        customer_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "DiscountTest SL",
                "document_type_code": "NIF",
                "document_number": "E12345678",
                "country_code": "ESP",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        customer_id = customer_response.json()["id"]

        term_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
            json={
                "scope_type": "GLOBAL",
                "pricing_mode": "PERCENT_DISCOUNT",
                "discount_percent": "12.500",
                "currency": "EUR",
                "valid_from": "2026-01-01T00:00:00Z",
            },
        )
        assert term_response.status_code == 201, term_response.text
        term = term_response.json()
        assert term["scope_type"] == "GLOBAL"
        assert term["product_id"] is None
        assert term["pricing_mode"] == "PERCENT_DISCOUNT"
        assert term["discount_percent"] == "12.500"

        list_response = client.get(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
        )
        assert list_response.status_code == 200, list_response.text
        assert len(list_response.json()) == 1


def test_crm_pricing_term_validation_errors(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
    enable_crm_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)

        customer_response = client.post(
            "/api/v1/plugins/crm/customers",
            headers=headers,
            json={
                "legal_name": "ValidationTest SL",
                "document_type_code": "NIF",
                "document_number": "F12345678",
                "country_code": "ESP",
                "billing_type": "por_operacion",
                "is_exempt": False,
            },
        )
        customer_id = customer_response.json()["id"]

        no_product_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
            json={
                "scope_type": "PRODUCT",
                "pricing_mode": "FIXED_PRICE",
                "fixed_amount": "50.0000",
                "valid_from": "2026-01-01T00:00:00Z",
            },
        )
        assert no_product_response.status_code == 400

        no_fixed_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
            json={
                "scope_type": "GLOBAL",
                "pricing_mode": "FIXED_PRICE",
                "valid_from": "2026-01-01T00:00:00Z",
            },
        )
        assert no_fixed_response.status_code == 400

        no_discount_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
            json={
                "scope_type": "GLOBAL",
                "pricing_mode": "PERCENT_DISCOUNT",
                "valid_from": "2026-01-01T00:00:00Z",
            },
        )
        assert no_discount_response.status_code == 400

        global_with_product_response = client.post(
            f"/api/v1/plugins/crm/customers/{customer_id}/pricing-terms",
            headers=headers,
            json={
                "scope_type": "GLOBAL",
                "product_id": "prod-123",
                "pricing_mode": "FIXED_PRICE",
                "fixed_amount": "50.0000",
                "valid_from": "2026-01-01T00:00:00Z",
            },
        )
        assert global_with_product_response.status_code == 400
