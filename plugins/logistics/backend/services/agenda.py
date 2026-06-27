from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from plugins.logistics.backend.common import (
    LogisticsActionContext,
    audit_logistics_action,
    emit_logistics_event,
)
from plugins.logistics.backend.models import LogisticsAgendaTask
from plugins.logistics.backend.schemas import AgendaTaskCreateRequest, AgendaTaskUpdateRequest


def list_agenda_tasks(
    db: Session,
    *,
    tenant_id: str,
    driver_id: str | None = None,
    status: str | None = None,
    task_type: str | None = None,
    scheduled_date: date | None = None,
) -> list[LogisticsAgendaTask]:
    stmt = select(LogisticsAgendaTask).where(LogisticsAgendaTask.tenant_id == tenant_id)
    if driver_id:
        stmt = stmt.where(LogisticsAgendaTask.driver_id == driver_id)
    if status:
        stmt = stmt.where(LogisticsAgendaTask.status == status)
    if task_type:
        stmt = stmt.where(LogisticsAgendaTask.task_type == task_type)
    if scheduled_date:
        stmt = stmt.where(LogisticsAgendaTask.scheduled_date == scheduled_date)
    stmt = stmt.order_by(
        LogisticsAgendaTask.scheduled_date.desc(),
        LogisticsAgendaTask.scheduled_time.asc().nulls_last(),
        LogisticsAgendaTask.priority.asc(),
    )
    return list(db.scalars(stmt).all())


def get_agenda_task(db: Session, *, tenant_id: str, task_id: str) -> LogisticsAgendaTask | None:
    return db.scalar(
        select(LogisticsAgendaTask).where(
            LogisticsAgendaTask.id == task_id,
            LogisticsAgendaTask.tenant_id == tenant_id,
        )
    )


def create_agenda_task(
    db: Session,
    *,
    tenant_id: str,
    payload: AgendaTaskCreateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsAgendaTask:
    task = LogisticsAgendaTask(
        tenant_id=tenant_id,
        route_id=payload.route_id,
        driver_id=payload.driver_id or action_context.actor_user_id,
        customer_id=payload.customer_id,
        customer_name=payload.customer_name,
        delivery_point_id=payload.delivery_point_id,
        task_type=payload.task_type,
        description=payload.description,
        scheduled_date=payload.scheduled_date,
        scheduled_time=payload.scheduled_time,
        priority=payload.priority,
        order_id=payload.order_id,
        quantity_requested=payload.quantity_requested,
        quantity_served=payload.quantity_served,
        cylinder_serial=payload.cylinder_serial,
        customer_confirmed=payload.customer_confirmed,
        requires_signature=payload.requires_signature,
        evidence_url=payload.evidence_url,
        delivery_location=payload.delivery_location,
        gps_coordinates=payload.gps_coordinates,
    )
    db.add(task)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="agenda_task.create",
        entity_type="agenda_task",
        entity_id=task.id,
        details={"task_type": task.task_type, "driver_id": task.driver_id, "status": task.status},
    )
    return task


def update_agenda_task(
    db: Session,
    *,
    task: LogisticsAgendaTask,
    payload: AgendaTaskUpdateRequest,
    action_context: LogisticsActionContext,
) -> LogisticsAgendaTask:
    if payload.status is not None:
        task.status = payload.status
    if payload.description is not None:
        task.description = payload.description
    if payload.scheduled_time is not None:
        task.scheduled_time = payload.scheduled_time
    if payload.priority is not None:
        task.priority = payload.priority
    if payload.quantity_served is not None:
        task.quantity_served = payload.quantity_served
    if payload.customer_confirmed is not None:
        task.customer_confirmed = payload.customer_confirmed
    if payload.evidence_url is not None:
        task.evidence_url = payload.evidence_url
    if payload.delivery_location is not None:
        task.delivery_location = payload.delivery_location
    if payload.gps_coordinates is not None:
        task.gps_coordinates = payload.gps_coordinates
    db.add(task)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="agenda_task.update",
        entity_type="agenda_task",
        entity_id=task.id,
        details={"task_type": task.task_type, "status": task.status},
    )
    return task


def complete_agenda_task(
    db: Session,
    *,
    task: LogisticsAgendaTask,
    action_context: LogisticsActionContext,
) -> LogisticsAgendaTask:
    task.status = "REALIZADO"
    task.completed_at = datetime.now(UTC)
    db.add(task)
    db.flush()
    emit_logistics_event(
        db,
        context=action_context,
        event_name="logistics.agenda.task_completed",
        entity_type="agenda_task",
        entity_id=task.id,
        payload={"task_type": task.task_type, "driver_id": task.driver_id, "status": task.status},
    )
    return task


def cancel_agenda_task(
    db: Session,
    *,
    task: LogisticsAgendaTask,
    action_context: LogisticsActionContext,
) -> LogisticsAgendaTask:
    task.status = "CANCELADO"
    db.add(task)
    db.flush()
    audit_logistics_action(
        db,
        context=action_context,
        action="agenda_task.cancel",
        entity_type="agenda_task",
        entity_id=task.id,
        details={"task_type": task.task_type, "status": task.status},
    )
    return task
