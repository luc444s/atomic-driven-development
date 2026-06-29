from __future__ import annotations

from typing import Any

from sqlalchemy import inspect, text

from plugins.crm.backend.models import (
    CrmCustomer,
    CrmCustomerAddress,
    CrmCustomerContact,
    CrmDocumentType,
    CrmPaymentTerm,
)
from plugins.crm.backend.services.catalog import DOCUMENT_TYPE_SEEDS, PAYMENT_TERM_SEEDS

revision = "0001"


def _create_table(table: Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table: Any, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.connection()
    _create_table(CrmDocumentType.__table__, bind)
    _create_table(CrmPaymentTerm.__table__, bind)
    _create_table(CrmCustomer.__table__, bind)
    _create_table(CrmCustomerAddress.__table__, bind)
    _create_table(CrmCustomerContact.__table__, bind)

    for seed in DOCUMENT_TYPE_SEEDS:
        bind.execute(
            text(
                """
                INSERT INTO crm_document_types
                    (
                        code,
                        name,
                        country_code,
                        description,
                        is_person,
                        is_company,
                        validation_pattern,
                        is_active,
                        created_at
                    )
                VALUES
                    (
                        :code,
                        :name,
                        :country_code,
                        :description,
                        :is_person,
                        :is_company,
                        :validation_pattern,
                        true,
                        CURRENT_TIMESTAMP
                    )
                ON CONFLICT (code) DO NOTHING
                """
            ),
            seed,
        )
    for seed in PAYMENT_TERM_SEEDS:
        bind.execute(
            text(
                """
                INSERT INTO crm_payment_terms
                    (code, name, description, days, operation_type, is_active, created_at)
                VALUES
                    (:code, :name, :description, :days, :operation_type, true, CURRENT_TIMESTAMP)
                ON CONFLICT (code) DO NOTHING
                """
            ),
            seed,
        )

    if bind.dialect.name != "sqlite":
        inspector = inspect(bind)
        foreign_keys = {
            fk["name"] for fk in inspector.get_foreign_keys("crm_customers") if fk.get("name")
        }
        if "fk_crm_customer_fiscal_address" not in foreign_keys:
            bind.execute(
                text(
                    "ALTER TABLE crm_customers ADD CONSTRAINT fk_crm_customer_fiscal_address "
                    "FOREIGN KEY (fiscal_address_id) REFERENCES crm_customer_addresses(id)"
                )
            )


def downgrade(db) -> None:
    bind = db.connection()
    if bind.dialect.name != "sqlite":
        bind.execute(
            text(
                "ALTER TABLE crm_customers DROP CONSTRAINT IF EXISTS fk_crm_customer_fiscal_address"
            )
        )
    _drop_table(CrmCustomerContact.__table__, bind)
    _drop_table(CrmCustomerAddress.__table__, bind)
    _drop_table(CrmCustomer.__table__, bind)
    _drop_table(CrmPaymentTerm.__table__, bind)
    _drop_table(CrmDocumentType.__table__, bind)
