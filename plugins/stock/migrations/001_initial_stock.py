from __future__ import annotations

from typing import cast

from sqlalchemy.sql.schema import Table
from systutor.core.database import Base

import plugins.logistics.backend.models  # noqa: F401
import plugins.productos.backend.models  # noqa: F401
from plugins.stock.backend.models import StockBalance, StockConfig, StockLedger

revision = "0001"

PLUGIN_TABLES = cast(
    list[Table],
    [
        StockLedger.__table__,
        StockBalance.__table__,
        StockConfig.__table__,
    ],
)


def upgrade(db) -> None:
    bind = db.connection()
    Base.metadata.create_all(bind=bind, tables=PLUGIN_TABLES, checkfirst=True)


def downgrade(db) -> None:
    bind = db.connection()
    Base.metadata.drop_all(bind=bind, tables=list(reversed(PLUGIN_TABLES)), checkfirst=True)
