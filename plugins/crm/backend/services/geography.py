from __future__ import annotations

from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.crm.backend.models import CrmGeography


class GeographySeed(TypedDict):
    code: str
    name: str
    level: int
    country_code: str
    ubigeo_code: str | None
    parent_code: str | None


GEOGRAPHY_SEEDS: dict[str, list[GeographySeed]] = {
    "PER": [
        {
            "code": "PER",
            "name": "Peru",
            "level": 1,
            "country_code": "PER",
            "ubigeo_code": None,
            "parent_code": None,
        },
        {
            "code": "LIM",
            "name": "Lima",
            "level": 2,
            "country_code": "PER",
            "ubigeo_code": None,
            "parent_code": "PER",
        },
        {
            "code": "LIM-LIM",
            "name": "Lima",
            "level": 3,
            "country_code": "PER",
            "ubigeo_code": None,
            "parent_code": "LIM",
        },
        {
            "code": "150101",
            "name": "Lima",
            "level": 4,
            "country_code": "PER",
            "ubigeo_code": "150101",
            "parent_code": "LIM-LIM",
        },
        {
            "code": "AQP",
            "name": "Arequipa",
            "level": 2,
            "country_code": "PER",
            "ubigeo_code": None,
            "parent_code": "PER",
        },
        {
            "code": "AQP-AQP",
            "name": "Arequipa",
            "level": 3,
            "country_code": "PER",
            "ubigeo_code": None,
            "parent_code": "AQP",
        },
        {
            "code": "040101",
            "name": "Arequipa",
            "level": 4,
            "country_code": "PER",
            "ubigeo_code": "040101",
            "parent_code": "AQP-AQP",
        },
    ],
    "CRI": [
        {
            "code": "CRI",
            "name": "Costa Rica",
            "level": 1,
            "country_code": "CRI",
            "ubigeo_code": None,
            "parent_code": None,
        },
        {
            "code": "SJ",
            "name": "San Jose",
            "level": 2,
            "country_code": "CRI",
            "ubigeo_code": None,
            "parent_code": "CRI",
        },
        {
            "code": "SJ-SJ",
            "name": "San Jose",
            "level": 3,
            "country_code": "CRI",
            "ubigeo_code": None,
            "parent_code": "SJ",
        },
        {
            "code": "SJ-CEN",
            "name": "Carmen",
            "level": 4,
            "country_code": "CRI",
            "ubigeo_code": None,
            "parent_code": "SJ-SJ",
        },
    ],
    "ESP": [
        {
            "code": "ESP",
            "name": "Espana",
            "level": 1,
            "country_code": "ESP",
            "ubigeo_code": None,
            "parent_code": None,
        },
        {
            "code": "MD",
            "name": "Madrid",
            "level": 2,
            "country_code": "ESP",
            "ubigeo_code": None,
            "parent_code": "ESP",
        },
        {
            "code": "MD-MD",
            "name": "Madrid",
            "level": 3,
            "country_code": "ESP",
            "ubigeo_code": None,
            "parent_code": "MD",
        },
        {
            "code": "MD-CEN",
            "name": "Centro",
            "level": 4,
            "country_code": "ESP",
            "ubigeo_code": None,
            "parent_code": "MD-MD",
        },
    ],
}


def seed_geography(db: Session, *, country_code: str) -> int:
    normalized = country_code.strip().upper()
    seeds = GEOGRAPHY_SEEDS.get(normalized)
    if seeds is None:
        return 0

    existing_by_code = {
        item.code: item
        for item in db.scalars(
            select(CrmGeography).where(CrmGeography.country_code == normalized)
        ).all()
        if item.code is not None
    }
    inserted = 0
    for seed in seeds:
        code = seed["code"]
        if code in existing_by_code:
            continue
        parent_id = None
        parent_code = seed["parent_code"]
        if isinstance(parent_code, str) and parent_code:
            parent = existing_by_code.get(parent_code)
            if parent is None:
                continue
            parent_id = parent.id
        item = CrmGeography(
            parent_id=parent_id,
            code=str(seed["code"]),
            name=str(seed["name"]),
            level=int(seed["level"]),
            country_code=str(seed["country_code"]),
            ubigeo_code=seed["ubigeo_code"],
            is_active=True,
        )
        db.add(item)
        db.flush()
        existing_by_code[item.code or item.id] = item
        inserted += 1
    return inserted


def list_countries(db: Session) -> list[CrmGeography]:
    return list(
        db.scalars(
            select(CrmGeography)
            .where(CrmGeography.level == 1, CrmGeography.is_active.is_(True))
            .order_by(CrmGeography.name)
        ).all()
    )


def list_departments(db: Session, *, country_code: str) -> list[CrmGeography]:
    return list(
        db.scalars(
            select(CrmGeography)
            .where(
                CrmGeography.country_code == country_code.upper(),
                CrmGeography.level == 2,
                CrmGeography.is_active.is_(True),
            )
            .order_by(CrmGeography.name)
        ).all()
    )


def list_provinces(db: Session, *, department_id: str) -> list[CrmGeography]:
    return list(
        db.scalars(
            select(CrmGeography)
            .where(
                CrmGeography.parent_id == department_id,
                CrmGeography.level == 3,
                CrmGeography.is_active.is_(True),
            )
            .order_by(CrmGeography.name)
        ).all()
    )


def list_districts(db: Session, *, province_id: str) -> list[CrmGeography]:
    return list(
        db.scalars(
            select(CrmGeography)
            .where(
                CrmGeography.parent_id == province_id,
                CrmGeography.level == 4,
                CrmGeography.is_active.is_(True),
            )
            .order_by(CrmGeography.name)
        ).all()
    )


def get_geography(db: Session, *, geography_id: str) -> CrmGeography | None:
    return db.scalar(select(CrmGeography).where(CrmGeography.id == geography_id))
