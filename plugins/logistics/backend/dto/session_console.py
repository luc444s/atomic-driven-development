from __future__ import annotations

from pydantic import BaseModel, Field

from plugins.logistics.backend.dto.load_plans import LoadPlanRead
from plugins.logistics.backend.dto.operational_summary import SessionOperationalSummaryRead
from plugins.logistics.backend.dto.reconciliation import SessionReconciliationRead
from plugins.logistics.backend.dto.sessions import VehicleSessionDetailRead
from plugins.logistics.backend.schemas import WarehouseSerializedCylinderSummaryItem
from plugins.stock.backend.schemas import StockBalancePageRead


class SessionConsoleContextRead(BaseModel):
    session: VehicleSessionDetailRead
    load_plan: LoadPlanRead
    reconciliation: SessionReconciliationRead
    operational_summary: SessionOperationalSummaryRead | None = None
    origin_balances: StockBalancePageRead
    mobile_balances: StockBalancePageRead
    origin_serialized: list[WarehouseSerializedCylinderSummaryItem] = Field(
        default_factory=list
    )
