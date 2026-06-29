from __future__ import annotations

from sqlalchemy import inspect, text

revision = "0003"


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)
    tables = set(inspector.get_table_names())
    if "crm_customers" not in tables:
        return

    _backfill_placeholder_customers(bind, inspector)


def downgrade(db) -> None:
    # No rollback automatico para placeholder customers o relinks.
    return None


def _backfill_placeholder_customers(bind, inspector) -> None:
    mappings = {
        "lg_delivery_points": "customer_id",
        "lg_orders": "customer_id",
        "lg_movements": "customer_id",
        "lg_agenda_tasks": "customer_id",
        "lg_cylinder_warranties": "customer_id",
        "lg_cylinder_ownership": "customer_id",
    }
    for table_name, customer_id_column in mappings.items():
        if table_name not in inspector.get_table_names():
            continue
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if (
            "tenant_id" not in columns
            or "customer_name" not in columns
            or customer_id_column not in columns
        ):
            continue
        rows = bind.execute(
            text(
                f"""
                SELECT tenant_id, TRIM(customer_name) AS customer_name
                FROM {table_name}
                WHERE {customer_id_column} IS NULL
                  AND customer_name IS NOT NULL
                  AND TRIM(customer_name) <> ''
                """
            )
        ).mappings()
        for row in rows:
            customer_id = _ensure_placeholder_customer(bind, row["tenant_id"], row["customer_name"])
            bind.execute(
                text(
                    f"""
                    UPDATE {table_name}
                    SET {customer_id_column} = :customer_id
                    WHERE tenant_id = :tenant_id
                      AND {customer_id_column} IS NULL
                      AND TRIM(customer_name) = :customer_name
                    """
                ),
                {
                    "customer_id": customer_id,
                    "tenant_id": row["tenant_id"],
                    "customer_name": row["customer_name"],
                },
            )


def _ensure_placeholder_customer(bind, tenant_id: str, customer_name: str) -> str:
    existing = bind.execute(
        text(
            "SELECT id FROM crm_customers "
            "WHERE tenant_id = :tenant_id AND legal_name = :legal_name LIMIT 1"
        ),
        {"tenant_id": tenant_id, "legal_name": customer_name},
    ).scalar_one_or_none()
    if existing is not None:
        return str(existing)
    new_id = (
        bind.execute(text("SELECT lower(hex(randomblob(16)))")).scalar_one()
        if bind.dialect.name == "sqlite"
        else None
    )
    if new_id is None:
        new_id = bind.execute(text("SELECT gen_random_uuid()::text")).scalar_one()
    document_number = f"AUTO-{str(new_id)[:12].upper()}"
    bind.execute(
        text(
            """
            INSERT INTO crm_customers
                (
                    id,
                    tenant_id,
                    external_code,
                    legal_name,
                    document_type_code,
                    document_number,
                    country_code,
                    notes,
                    is_active,
                    is_exempt,
                    activity_validated,
                    created_by,
                    created_at,
                    updated_at
                )
            VALUES
                (
                    :id,
                    :tenant_id,
                    :external_code,
                    :legal_name,
                    'OTRO',
                    :document_number,
                    'PER',
                    :notes,
                    true,
                    false,
                    false,
                    :created_by,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
            """
        ),
        {
            "id": new_id,
            "tenant_id": tenant_id,
            "external_code": f"AUTO-{str(new_id)[:8].upper()}",
            "legal_name": customer_name,
            "document_number": document_number,
            "notes": "autogenerado_por_migracion_logistics",
            "created_by": _first_user_id(bind, tenant_id),
        },
    )
    return str(new_id)


def _first_user_id(bind, tenant_id: str) -> str:
    user_id = bind.execute(
        text("SELECT id FROM users WHERE tenant_id = :tenant_id ORDER BY created_at ASC LIMIT 1"),
        {"tenant_id": tenant_id},
    ).scalar_one_or_none()
    if user_id is not None:
        return str(user_id)
    fallback = bind.execute(
        text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")
    ).scalar_one()
    return str(fallback)
