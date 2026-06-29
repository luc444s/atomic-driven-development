from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session

from apps.api.app.kernel.audit.service import record_audit
from apps.api.app.kernel.events.service import emit_event
from apps.api.app.kernel.tenants.context import TenantContext
from packages.contracts.events import EventContract


@dataclass(slots=True)
class LogisticsActionContext:
    tenant_id: str
    branch_id: str | None
    actor_user_id: str
    correlation_id: str | None
    request_id: str | None


def build_action_context(
    request: Request,
    tenant_context: TenantContext,
) -> LogisticsActionContext:
    return LogisticsActionContext(
        tenant_id=tenant_context.current_tenant_id,
        branch_id=tenant_context.current_branch_id,
        actor_user_id=tenant_context.current_user_id,
        correlation_id=getattr(request.state, "correlation_id", None),
        request_id=getattr(request.state, "request_id", None),
    )


def audit_logistics_action(
    db: Session,
    *,
    context: LogisticsActionContext,
    branch_id: str | None = None,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, object],
    result: str = "success",
) -> None:
    record_audit(
        db,
        tenant_id=context.tenant_id,
        branch_id=branch_id if branch_id is not None else context.branch_id,
        actor_user_id=context.actor_user_id,
        actor_type="user",
        module="logistics",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        result=result,
        correlation_id=context.correlation_id,
        request_id=context.request_id,
        details=details,
    )


def emit_logistics_event(
    db: Session,
    *,
    context: LogisticsActionContext,
    branch_id: str | None = None,
    event_name: str,
    entity_type: str,
    entity_id: str,
    payload: dict[str, object],
) -> None:
    emit_event(
        db,
        event=EventContract(
            event_name=event_name,
            module="logistics",
            tenant_id=context.tenant_id,
            branch_id=branch_id if branch_id is not None else context.branch_id,
            actor_user_id=context.actor_user_id,
            actor_type="user",
            entity_type=entity_type,
            entity_id=entity_id,
            correlation_id=context.correlation_id,
            payload=payload,
            metadata={"request_id": context.request_id} if context.request_id else {},
        ),
    )
