from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.app.commands.seed_demo import seed_demo_data
from apps.api.app.kernel.documents.models import CoreDocumentVersion
from apps.api.app.kernel.signatures.models import CoreSignatureEvidence, CoreSignatureSession
from apps.api.tests.test_logistics_plugin import (
    auth_headers,
    create_customer,
    create_product,
    enable_crm_plugin,
    enable_logistics_plugin,
)
from apps.api.tests.test_productos_plugin import enable_productos_plugin
from plugins.logistics.backend.models.contracts import LogisticsContractType


def test_contract_issue_generates_pdf_and_completes_digital_signature(app) -> None:
    with app.state.session_factory() as db:
        seeded_demo = seed_demo_data(
            db, app.state.settings, app.state.plugin_runtime.list_results()
        )
        db.add(
            LogisticsContractType(
                code="ANNUAL",
                name="Anual",
                duration_unit="YEAR",
                duration_value=1,
                is_active=True,
            )
        )
        db.commit()

    enable_crm_plugin(app, seeded_demo)
    enable_productos_plugin(app, seeded_demo)
    enable_logistics_plugin(app, seeded_demo)

    with TestClient(app) as client:
        headers = auth_headers(client)
        customer = create_customer(
            client,
            headers,
            name="Cliente Contrato PDF SAC",
            document_number="20100070970",
        )
        warehouse_response = client.post(
            "/api/v1/plugins/logistics/warehouses",
            headers=headers,
            json={"name": "Almacen Contratos", "code": "AC", "address": "Av. Firma 100"},
        )
        assert warehouse_response.status_code == 201, warehouse_response.text
        warehouse = warehouse_response.json()
        product = create_product(
            client,
            headers,
            sku="ENV-CONTRACT-PDF",
            name="Envase Contrato 45kg",
        )

        create_response = client.post(
            "/api/v1/plugins/logistics/cylinders/contracts",
            headers=headers,
            json={
                "contract_type": "ANNUAL",
                "customer_id": customer["id"],
                "warehouse_id": warehouse["id"],
                "start_date": date.today().isoformat(),
                "cylinder_type_id": product["id"],
                "quantity": 1,
                "unit_price": 50,
            },
        )
        assert create_response.status_code == 201, create_response.text
        contract = create_response.json()
        assert contract["status"] == "DRAFT"

        issue_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/contracts/{contract['id']}/issue",
            headers=headers,
            json={},
        )
        assert issue_response.status_code == 200, issue_response.text
        issued = issue_response.json()
        assert issued["status"] == "PENDING_SIGNATURE"
        assert issued["contract_number"]
        assert issued["contract_file_path"].startswith("/api/v1/core/documents/")

        draft_pdf_response = client.get(issued["contract_file_path"], headers=headers)
        assert draft_pdf_response.status_code == 200, draft_pdf_response.text
        assert draft_pdf_response.content.startswith(b"%PDF")
        assert product["id"].encode() not in draft_pdf_response.content
        assert b"Producto/envase: Envase Contrato 45kg" in draft_pdf_response.content

        draft_document_id = issued["contract_file_path"].split("/")[-2]
        signed_url_response = client.get(
            f"/api/v1/core/documents/{draft_document_id}/signed-url",
            headers=headers,
        )
        assert signed_url_response.status_code == 200, signed_url_response.text
        signed_url_payload = signed_url_response.json()
        assert signed_url_payload["url"].startswith(
            f"/api/v1/core/documents/{draft_document_id}/signed-download?"
        )

        signed_download_response = client.get(signed_url_payload["url"])
        assert signed_download_response.status_code == 200, signed_download_response.text
        assert signed_download_response.content.startswith(b"%PDF")

        sign_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/contracts/{contract['id']}/sign",
            headers=headers,
            json={},
        )
        assert sign_response.status_code == 200, sign_response.text
        signed = sign_response.json()
        assert signed["status"] == "ACTIVE"
        assert signed["signed_flag"] is True
        assert signed["signature_type"] == "DIGITAL"
        assert signed["signed_by"] == "Cliente Contrato PDF SAC"
        assert signed["contract_file_path"].startswith("/api/v1/core/documents/")
        assert signed["contract_file_path"] != issued["contract_file_path"]

        signed_pdf_response = client.get(signed["contract_file_path"], headers=headers)
        assert signed_pdf_response.status_code == 200, signed_pdf_response.text
        assert signed_pdf_response.content.startswith(b"%PDF")
        assert product["id"].encode() not in signed_pdf_response.content
        assert seeded_demo["user_id"].encode() not in signed_pdf_response.content
        assert b"Producto/envase: Envase Contrato 45kg" in signed_pdf_response.content
        assert b"Firmante: Cliente Contrato PDF SAC" in signed_pdf_response.content

        renew_response = client.post(
            f"/api/v1/plugins/logistics/cylinders/contracts/{contract['id']}/renew",
            headers=headers,
            json={"end_date": "2028-08-31", "renewal_type": "MANUAL"},
        )
        assert renew_response.status_code == 200, renew_response.text
        renewed = renew_response.json()
        assert renewed["contract_file_path"].startswith("/api/v1/core/documents/")
        assert renewed["contract_file_path"] != signed["contract_file_path"]

        renewed_pdf_response = client.get(renewed["contract_file_path"], headers=headers)
        assert renewed_pdf_response.status_code == 200, renewed_pdf_response.text
        assert renewed_pdf_response.content.startswith(b"%PDF")
        assert product["id"].encode() not in renewed_pdf_response.content
        assert seeded_demo["user_id"].encode() not in renewed_pdf_response.content
        assert b"Producto/envase: Envase Contrato 45kg" in renewed_pdf_response.content
        assert b"Firmante: Cliente Contrato PDF SAC" in renewed_pdf_response.content

    with app.state.session_factory() as db:
        documents = list(
            db.scalars(
                select(CoreDocumentVersion).where(
                    CoreDocumentVersion.entity_type == "cylinder_contract",
                    CoreDocumentVersion.entity_id == contract["id"],
                )
            ).all()
        )
        sessions = list(
            db.scalars(
                select(CoreSignatureSession).where(
                    CoreSignatureSession.tenant_id == seeded_demo["tenant_id"]
                )
            ).all()
        )
        evidence = list(
            db.scalars(
                select(CoreSignatureEvidence).where(
                    CoreSignatureEvidence.tenant_id == seeded_demo["tenant_id"]
                )
            ).all()
        )

    assert len(documents) == 3
    assert {document.status for document in documents} == {
        "PENDING_SIGNATURE",
        "SIGNED",
        "RENEWED",
    }
    assert len(sessions) == 1
    assert sessions[0].status == "COMPLETED"
    assert len(evidence) == 1
