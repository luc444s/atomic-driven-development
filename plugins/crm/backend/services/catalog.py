from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.models import CrmDocumentType, CrmPaymentTerm

DOCUMENT_TYPE_SEEDS: tuple[dict[str, object], ...] = (
    {
        "code": "RUC",
        "name": "RUC",
        "country_code": "PER",
        "description": "Registro Unico de Contribuyentes",
        "is_person": False,
        "is_company": True,
        "validation_pattern": r"\d{11}",
    },
    {
        "code": "DNI",
        "name": "DNI",
        "country_code": "PER",
        "description": "Documento Nacional de Identidad",
        "is_person": True,
        "is_company": False,
        "validation_pattern": r"\d{8}",
    },
    {
        "code": "CEDULA_FISICA",
        "name": "Cedula Fisica",
        "country_code": "CRI",
        "description": "Cedula fisica de Costa Rica",
        "is_person": True,
        "is_company": False,
        "validation_pattern": r"\d-\d{4}-\d{4}",
    },
    {
        "code": "CEDULA_JURIDICA",
        "name": "Cedula Juridica",
        "country_code": "CRI",
        "description": "Cedula juridica de Costa Rica",
        "is_person": False,
        "is_company": True,
        "validation_pattern": r"\d-\d{3}-\d{6}",
    },
    {
        "code": "NIF",
        "name": "NIF",
        "country_code": "ESP",
        "description": "Numero de Identificacion Fiscal",
        "is_person": False,
        "is_company": True,
        "validation_pattern": r"\d{8}[A-Z]",
    },
    {
        "code": "NIE",
        "name": "NIE",
        "country_code": "ESP",
        "description": "Numero de Identidad de Extranjero",
        "is_person": True,
        "is_company": False,
        "validation_pattern": r"[XYZ]\d{7}[A-Z]",
    },
    {
        "code": "DIMEX",
        "name": "DIMEX",
        "country_code": "CRI",
        "description": "Documento de Identidad Migratorio para Extranjeros",
        "is_person": True,
        "is_company": False,
        "validation_pattern": r"\d{9}",
    },
    {
        "code": "NITE",
        "name": "NITE",
        "country_code": "CRI",
        "description": "Numero de Identificacion Tributaria Especial",
        "is_person": False,
        "is_company": True,
        "validation_pattern": r"\d{10}",
    },
    {
        "code": "PASAPORTE",
        "name": "Pasaporte",
        "country_code": "INT",
        "description": "Pasaporte internacional",
        "is_person": True,
        "is_company": False,
        "validation_pattern": None,
    },
    {
        "code": "OTRO",
        "name": "Otro",
        "country_code": "INT",
        "description": "Documento no catalogado",
        "is_person": True,
        "is_company": True,
        "validation_pattern": None,
    },
)

PAYMENT_TERM_SEEDS: tuple[dict[str, object], ...] = (
    {
        "code": "CONTADO",
        "name": "Contado",
        "description": None,
        "days": 0,
        "operation_type": "CONTADO",
    },
    {
        "code": "CREDITO_15",
        "name": "Credito 15 dias",
        "description": None,
        "days": 15,
        "operation_type": "CREDITO",
    },
    {
        "code": "CREDITO_30",
        "name": "Credito 30 dias",
        "description": None,
        "days": 30,
        "operation_type": "CREDITO",
    },
    {
        "code": "CREDITO_60",
        "name": "Credito 60 dias",
        "description": None,
        "days": 60,
        "operation_type": "CREDITO",
    },
    {
        "code": "TARJETA",
        "name": "Tarjeta",
        "description": None,
        "days": 0,
        "operation_type": "TARJETA",
    },
    {
        "code": "TRANSFERENCIA",
        "name": "Transferencia",
        "description": None,
        "days": 0,
        "operation_type": "TRANSFERENCIA",
    },
    {
        "code": "CHEQUE",
        "name": "Cheque",
        "description": None,
        "days": 0,
        "operation_type": "CHEQUE",
    },
)


def ensure_catalogs_seeded(db: Session) -> None:
    has_documents = db.scalar(select(CrmDocumentType.code).limit(1))
    if has_documents is None:
        for seed in DOCUMENT_TYPE_SEEDS:
            db.add(CrmDocumentType(**seed))

    has_payment_terms = db.scalar(select(CrmPaymentTerm.code).limit(1))
    if has_payment_terms is None:
        for seed in PAYMENT_TERM_SEEDS:
            db.add(CrmPaymentTerm(**seed))
    db.flush()


def list_document_types(
    db: Session, *, country_code: str | None = None, active: bool = True
) -> list[CrmDocumentType]:
    ensure_catalogs_seeded(db)
    stmt = select(CrmDocumentType)
    if country_code:
        stmt = stmt.where(CrmDocumentType.country_code.in_([country_code.upper(), "INT"]))
    if active:
        stmt = stmt.where(CrmDocumentType.is_active.is_(True))
    stmt = stmt.order_by(CrmDocumentType.country_code, CrmDocumentType.code)
    return list(db.scalars(stmt).all())


def list_payment_terms(db: Session) -> list[CrmPaymentTerm]:
    ensure_catalogs_seeded(db)
    return list(
        db.scalars(
            select(CrmPaymentTerm)
            .where(CrmPaymentTerm.is_active.is_(True))
            .order_by(CrmPaymentTerm.days.asc(), CrmPaymentTerm.code.asc())
        ).all()
    )
