from __future__ import annotations

from typing import cast

from sqlalchemy.sql.schema import Table

import plugins.tms.backend.models  # noqa: F401
from plugins.tms.backend.models import JornadaTMS, TmsBase

revision = "0001"

PLUGIN_TABLES = cast(
    list[Table],
    [
        JornadaTMS.__table__,
    ],
)


def upgrade(db) -> None:
    bind = db.connection()
    TmsBase.metadata.create_all(bind=bind, tables=PLUGIN_TABLES, checkfirst=True)


def downgrade(db) -> None:
    bind = db.connection()
    TmsBase.metadata.drop_all(bind=bind, tables=list(reversed(PLUGIN_TABLES)), checkfirst=True)
