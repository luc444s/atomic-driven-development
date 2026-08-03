from __future__ import annotations

import re

from sqlalchemy import inspect, text

revision = "0046"

ROUTE_LABEL_PREFIX_RE = re.compile(r"^\d+\s*·\s*")


def _clean(value: object) -> str | None:
    if value is None:
        return None
    normalized = ROUTE_LABEL_PREFIX_RE.sub("", str(value)).strip()
    return normalized or None


def _split_notes(notes: object) -> tuple[str | None, str | None]:
    text_value = _clean(notes)
    if text_value is None or "→" not in text_value:
        return None, None
    origin, destination = text_value.split("→", 1)
    return _clean(origin), _clean(destination)


def _build_destination_label(row: dict[str, object] | None) -> str | None:
    if row is None:
        return None
    customer_name = (
        _clean(row.get("customer_name_snapshot"))
        or _clean(row.get("legal_name"))
        or _clean(row.get("dp_customer_name"))
    )
    location = _clean(row.get("notes")) or _clean(row.get("address"))
    if customer_name and location and customer_name != location:
        return f"{customer_name} - {location}"
    return customer_name or location


def upgrade(db) -> None:
    bind = db.connection()
    inspector = inspect(bind)

    columns = {col["name"] for col in inspector.get_columns("lg_routes")}
    for column in ["origin_label", "destination_label"]:
        if column not in columns:
            bind.execute(text(f"ALTER TABLE lg_routes ADD COLUMN {column} VARCHAR(200)"))

    routes = bind.execute(text("SELECT id, notes FROM lg_routes")).mappings().all()
    for route in routes:
        origin_label, destination_label = _split_notes(route.get("notes"))

        if origin_label is None:
            session_row = bind.execute(
                text(
                    """
                    SELECT w.name
                    FROM lg_vehicle_sessions s
                    JOIN lg_warehouses w ON w.id = s.origin_warehouse_id
                    WHERE s.route_id = :route_id
                    ORDER BY s.opened_at DESC, s.created_at DESC
                    LIMIT 1
                    """
                ),
                {"route_id": route["id"]},
            ).mappings().first()
            origin_label = _clean(session_row.get("name") if session_row else None)

        stop_row = bind.execute(
            text(
                """
                SELECT
                    rs.customer_name_snapshot,
                    rs.notes,
                    c.legal_name,
                    dp.customer_name AS dp_customer_name,
                    dp.address
                FROM lg_route_stops rs
                LEFT JOIN crm_customers c ON c.id = rs.customer_id
                LEFT JOIN lg_delivery_points dp ON dp.id = rs.delivery_point_id
                WHERE rs.route_id = :route_id
                ORDER BY rs.stop_order DESC, rs.created_at DESC
                LIMIT 1
                """
            ),
            {"route_id": route["id"]},
        ).mappings().first()
        destination_label = _build_destination_label(stop_row) or destination_label

        bind.execute(
            text(
                """
                UPDATE lg_routes
                SET origin_label = COALESCE(origin_label, :origin_label),
                    destination_label = COALESCE(destination_label, :destination_label)
                WHERE id = :route_id
                """
            ),
            {
                "route_id": route["id"],
                "origin_label": origin_label,
                "destination_label": destination_label,
            },
        )


def downgrade(db) -> None:
    bind = db.connection()
    bind.execute(text("ALTER TABLE lg_routes DROP COLUMN IF EXISTS destination_label"))
    bind.execute(text("ALTER TABLE lg_routes DROP COLUMN IF EXISTS origin_label"))
