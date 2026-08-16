from __future__ import annotations

from typing import cast

from sqlalchemy.sql.schema import Table
from systutor.core.database import Base

from plugins.productos.backend.models import (
    Product,
    ProductAdr,
    ProductBarcode,
    ProductBrand,
    ProductCategory,
    ProductCondition,
    ProductCost,
    ProductGroup,
    ProductInsumoType,
    ProductLine,
    ProductMedia,
    ProductPrice,
    ProductPromotion,
    ProductStatus,
    ProductSubcategory,
    ProductSubline,
    ProductTaxConfig,
    ProductUnit,
)
from plugins.productos.backend.services.catalog import ensure_static_catalogs_seeded

revision = "0001"

PLUGIN_TABLES = cast(
    list[Table],
    [
        ProductCondition.__table__,
        ProductStatus.__table__,
        ProductCategory.__table__,
    ProductLine.__table__,
    ProductSubline.__table__,
    ProductBrand.__table__,
    ProductInsumoType.__table__,
    ProductUnit.__table__,
    ProductSubcategory.__table__,
    ProductGroup.__table__,
    Product.__table__,
    ProductBarcode.__table__,
    ProductPrice.__table__,
    ProductCost.__table__,
    ProductTaxConfig.__table__,
    ProductAdr.__table__,
        ProductMedia.__table__,
        ProductPromotion.__table__,
    ],
)


def upgrade(db) -> None:
    bind = db.connection()
    Base.metadata.create_all(bind=bind, tables=PLUGIN_TABLES, checkfirst=True)
    ensure_static_catalogs_seeded(db)


def downgrade(db) -> None:
    bind = db.connection()
    Base.metadata.drop_all(bind=bind, tables=list(reversed(PLUGIN_TABLES)), checkfirst=True)
