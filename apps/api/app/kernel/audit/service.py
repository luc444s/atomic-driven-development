from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.app.kernel.audit.models import AuditLog


def record_audit(
    db: Session,
    *,
    tenant_id: str | None,
    branch_id: str | None,
    actor_user_id: str | None,
    actor_type: str,
    module: str,
    action: str,
    entity_type: str | None,
    entity_id: str | None,
    result: str,
    correlation_id: str | None,
    request_id: str | None,
    details: dict,
) -> AuditLog:
    audit = AuditLog(
        tenant_id=tenant_id,
        branch_id=branch_id,
        actor_user_id=actor_user_id,
        actor_type=actor_type,
        module=module,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        result=result,
        correlation_id=correlation_id,
        request_id=request_id,
        details=details,
    )
    db.add(audit)
    db.flush()
    return audit
