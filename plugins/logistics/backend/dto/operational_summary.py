from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

BlockingReason = Literal["FAILED_STOP", "WAYBILL_MISSING", "NO_ROUTE_ASSIGNED"]
AttentionReason = Literal["PARTIAL_STOP", "OPEN_INCIDENT", "WAYBILL_OUTDATED"]
DataCompleteness = Literal["FULL", "PARTIAL"]
HealthStatus = Literal["HEALTHY", "ATTENTION", "BLOCKED"]
LastActivityType = Literal["OPERATION", "INCIDENT", "DOCUMENT"]
WaybillSyncStatus = Literal["SYNCED", "OUTDATED", "MISSING"]


class SessionOperationalSummaryLastActivityRead(BaseModel):
    type: LastActivityType
    label: str
    at: datetime


class SessionOperationalSummaryStopCountersRead(BaseModel):
    total: int = 0
    pending: int = 0
    in_progress: int = 0
    partial: int = 0
    completed: int = 0
    failed: int = 0


class SessionOperationalSummaryIncidentsRead(BaseModel):
    open_total: int = 0
    corrected_total: int = 0
    resolved_total: int = 0


class SessionOperationalSummaryRouteActivityRead(BaseModel):
    confirmed_operations: int = 0
    last_activity: SessionOperationalSummaryLastActivityRead | None = None


class SessionOperationalSummaryCompositionRead(BaseModel):
    total_products: int = 0
    total_units: float = 0
    total_weight_kg: float | None = None
    total_adr_points: float = 0


class SessionOperationalSummaryWaybillRead(BaseModel):
    has_active_version: bool = False
    sync_status: WaybillSyncStatus
    active_version: int | None = None


class SessionOperationalSummaryStopIssueRead(BaseModel):
    route_stop_id: str
    stop_order: int
    label: str
    progress_status: str
    open_incidents: int = 0
    last_operation_at: datetime | None = None
    completion_percent: float | None = None
    outcome_type: str | None = None
    driver_note: str | None = None


class SessionOperationalSummaryIncidentIssueRead(BaseModel):
    id: str
    type: str
    status: str
    route_stop_id: str | None = None
    stop_label: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class SessionOperationalSummaryRead(BaseModel):
    session_id: str
    session_status: str
    data_completeness: DataCompleteness
    health_status: HealthStatus
    stop_counters: SessionOperationalSummaryStopCountersRead
    incidents: SessionOperationalSummaryIncidentsRead
    route_activity: SessionOperationalSummaryRouteActivityRead
    composition: SessionOperationalSummaryCompositionRead
    waybill: SessionOperationalSummaryWaybillRead
    blocking_reasons: list[BlockingReason] = Field(default_factory=list)
    attention_reasons: list[AttentionReason] = Field(default_factory=list)
    problematic_stops: list[SessionOperationalSummaryStopIssueRead] = Field(default_factory=list)
    open_incidents: list[SessionOperationalSummaryIncidentIssueRead] = Field(default_factory=list)
