from __future__ import annotations

from typing import Any

from sqlalchemy import inspect, text

from apps.api.app.core.database import Base
from plugins.crm.backend.models import CrmCustomerBankAccount, CrmCustomerPricingTerm

revision = "0004"


def _create_table(table: Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    if "crm_customers" in tables:
        columns = {col["name"] for col in inspector.get_columns("crm_customers")}
        statements: list[str] = []

        if "accounting_code" not in columns:
            statements.append(
                "ALTER TABLE crm_customers ADD COLUMN accounting_code VARCHAR(20)"
            )
        if "is_intracommunity" not in columns:
            statements.append(
                "ALTER TABLE crm_customers "
                "ADD COLUMN is_intracommunity BOOLEAN NOT NULL DEFAULT false"
            )
        if "fiscal_operation_key" not in columns:
            statements.append(
                "ALTER TABLE crm_customers ADD COLUMN fiscal_operation_key VARCHAR(20)"
            )
        if "tax_regime_code" not in columns:
            statements.append(
                "ALTER TABLE crm_customers ADD COLUMN tax_regime_code VARCHAR(20)"
            )
        if "equivalence_surcharge_applicable" not in columns:
            statements.append(
                "ALTER TABLE crm_customers "
                "ADD COLUMN equivalence_surcharge_applicable BOOLEAN NOT NULL DEFAULT false"
            )
        if "cash_criterion_applicable" not in columns:
            statements.append(
                "ALTER TABLE crm_customers "
                "ADD COLUMN cash_criterion_applicable BOOLEAN NOT NULL DEFAULT false"
            )
        if "accounting_code" not in columns:
            statements.append(
                "CREATE INDEX IF NOT EXISTS ix_crm_customers_accounting_code "
                "ON crm_customers (accounting_code)"
            )

        for statement in statements:
            bind.execute(text(statement))

    if "crm_payment_terms" in tables:
        columns = {col["name"] for col in inspector.get_columns("crm_payment_terms")}
        if "payment_mode" not in columns:
            bind.execute(
                text(
                    "ALTER TABLE crm_payment_terms "
                    "ADD COLUMN payment_mode VARCHAR(20) NOT NULL DEFAULT 'CONTADO'"
                )
            )

    _create_table(CrmCustomerBankAccount.__table__, bind)
    _create_table(CrmCustomerPricingTerm.__table__, bind)

    if "crm_payment_terms" in tables:
        _seed_payment_modes(bind)
        _seed_remesa_terms(bind)


def downgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())

    drop_tables: list[Any] = []
    if "crm_customer_pricing_terms" in tables:
        drop_tables.append(CrmCustomerPricingTerm.__table__)
    if "crm_customer_bank_accounts" in tables:
        drop_tables.append(CrmCustomerBankAccount.__table__)
    if drop_tables:
        Base.metadata.drop_all(bind=bind, tables=list(reversed(drop_tables)), checkfirst=True)


def _seed_payment_modes(bind) -> None:
    mapping = {
        "CONTADO": "CONTADO",
        "CREDITO_15": "TRANSFERENCIA",
        "CREDITO_30": "TRANSFERENCIA",
        "CREDITO_60": "TRANSFERENCIA",
        "TRANSFERENCIA": "TRANSFERENCIA",
        "CHEQUE": "CHEQUE",
        "TARJETA": "TARJETA",
    }
    for code, payment_mode in mapping.items():
        bind.execute(
            text(
                "UPDATE crm_payment_terms SET payment_mode = :payment_mode "
                "WHERE code = :code AND payment_mode = 'CONTADO'"
            ),
            {"code": code, "payment_mode": payment_mode},
        )


def _seed_remesa_terms(bind) -> None:
    remesa_terms = [
        ("REMESA_15", "Remesa 15 dias", 15),
        ("REMESA_30", "Remesa 30 dias", 30),
        ("REMESA_60", "Remesa 60 dias", 60),
    ]
    for code, name, days in remesa_terms:
        existing = bind.execute(
            text("SELECT 1 FROM crm_payment_terms WHERE code = :code"),
            {"code": code},
        ).scalar()
        if existing is None:
            bind.execute(
                text(
                    "INSERT INTO crm_payment_terms "
                    "(code, name, description, days, operation_type, "
                    "payment_mode, is_active, created_at) "
                    "VALUES (:code, :name, :description, :days, "
                    "'CREDITO', 'REMESA', true, CURRENT_TIMESTAMP)"
                ),
                {
                    "code": code,
                    "name": name,
                    "description": f"Remesa bancaria a {days} dias",
                    "days": days,
                },
            )
