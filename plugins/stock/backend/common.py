from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request
from sqlalchemy.orm import Session
from systutor.contracts.events import EventContract
from systutor.kernel.audit.service import record_audit
from systutor.kernel.events.service import emit_event
from systutor.kernel.tenants.context import TenantContext


@dataclass(slots=True)
class StockActionContext:
    tenant_id: str
    branch_id: str | None
    actor_user_id: str
    correlation_id: str | None
    request_id: str | None


def build_action_context(request: Request, tenant_context: TenantContext) -> StockActionContext:
    return StockActionContext(
        tenant_id=tenant_context.current_tenant_id,
        branch_id=tenant_context.current_branch_id,
        actor_user_id=tenant_context.current_user_id,
        correlation_id=getattr(request.state, "correlation_id", None),
        request_id=getattr(request.state, "request_id", None),
    )


def audit_stock_action(
    db: Session,
    *,
    context: StockActionContext,
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
        module="stock",
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        result=result,
        correlation_id=context.correlation_id,
        request_id=context.request_id,
        details=details,
    )


def emit_stock_event(
    db: Session,
    *,
    context: StockActionContext,
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
            module="stock",
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
