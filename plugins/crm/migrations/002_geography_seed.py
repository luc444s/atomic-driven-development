from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select

from plugins.crm.backend.models import CrmGeography
from plugins.crm.backend.services.geography import GEOGRAPHY_SEEDS

revision = "0002"


def _create_table(table: Any, bind) -> None:
    table.create(bind=bind, checkfirst=True)


def _drop_table(table: Any, bind) -> None:
    table.drop(bind=bind, checkfirst=True)


def upgrade(db) -> None:
    bind = db.connection()
    _create_table(CrmGeography.__table__, bind)
    db.flush()
    for country_code in sorted(GEOGRAPHY_SEEDS):
        seed = next(item for item in GEOGRAPHY_SEEDS[country_code] if int(item["level"]) == 1)
        existing = db.execute(
            select(CrmGeography).where(
                CrmGeography.country_code == seed["country_code"],
                CrmGeography.level == seed["level"],
                CrmGeography.code == seed["code"],
            )
        ).scalar_one_or_none()
        if existing:
            continue
        db.add(
            CrmGeography(
                id=str(uuid4()),
                parent_id=None,
                code=seed["code"],
                name=seed["name"],
                level=seed["level"],
                country_code=seed["country_code"],
                ubigeo_code=seed["ubigeo_code"],
                is_active=True,
            )
        )
        db.flush()


def downgrade(db) -> None:
    bind = db.connection()
    _drop_table(CrmGeography.__table__, bind)
