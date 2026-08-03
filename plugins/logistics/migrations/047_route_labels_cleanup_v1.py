from __future__ import annotations

import re

from sqlalchemy import text

revision = "0047"

ROUTE_LABEL_PREFIX_RE = re.compile(r"^\d+\s*·\s*")


def _clean(value: object) -> str | None:
    if value is None:
        return None
    normalized = ROUTE_LABEL_PREFIX_RE.sub("", str(value)).strip()
    return normalized or None


def upgrade(db) -> None:
    bind = db.connection()
    routes = bind.execute(
        text("SELECT id, origin_label, destination_label FROM lg_routes")
    ).mappings().all()
    for route in routes:
        bind.execute(
            text(
                """
                UPDATE lg_routes
                SET origin_label = :origin_label,
                    destination_label = :destination_label
                WHERE id = :route_id
                """
            ),
            {
                "route_id": route["id"],
                "origin_label": _clean(route.get("origin_label")),
                "destination_label": _clean(route.get("destination_label")),
            },
        )


def downgrade(db) -> None:
    return None
