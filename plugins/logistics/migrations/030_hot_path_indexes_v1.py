from __future__ import annotations

from sqlalchemy import text

revision = "0030"


INDEX_STATEMENTS = [
    (
        "ix_lg_vs_tenant_status_opened",
        "CREATE INDEX IF NOT EXISTS ix_lg_vs_tenant_status_opened "
        "ON lg_vehicle_sessions (tenant_id, status, opened_at DESC)",
    ),
    (
        "ix_lg_vs_tenant_vehicle_active",
        "CREATE INDEX IF NOT EXISTS ix_lg_vs_tenant_vehicle_active "
        "ON lg_vehicle_sessions (tenant_id, vehicle_id) "
        "WHERE status IN ("
        "'DRAFT', 'LOADING', 'READY_TO_DEPART', 'OUTBOUND', "
        "'RETURNING', 'AWAITING_RECONCILIATION'"
        ")",
    ),
    (
        "ix_lg_lp_session_updated",
        "CREATE INDEX IF NOT EXISTS ix_lg_lp_session_updated "
        "ON lg_load_plans (session_id, updated_at DESC)",
    ),
    (
        "ix_lg_lpi_plan_product",
        "CREATE INDEX IF NOT EXISTS ix_lg_lpi_plan_product "
        "ON lg_load_plan_items (load_plan_id, product_id)",
    ),
    (
        "ix_lg_lsa_active_sess_prod_sel",
        "CREATE INDEX IF NOT EXISTS ix_lg_lsa_active_sess_prod_sel "
        "ON lg_load_serial_assignments (session_id, product_id, selected_at ASC) "
        "WHERE assignment_status IN ('SELECTED', 'CONFIRMED')",
    ),
    (
        "ix_lg_lsa_sess_status_sel",
        "CREATE INDEX IF NOT EXISTS ix_lg_lsa_sess_status_sel "
        "ON lg_load_serial_assignments (session_id, assignment_status, selected_at ASC)",
    ),
    (
        "ix_lg_cyl_active_prod_state_ser",
        "CREATE INDEX IF NOT EXISTS ix_lg_cyl_active_prod_state_ser "
        "ON lg_cylinders (tenant_id, product_id, current_state, serial) "
        "WHERE is_active = true",
    ),
    (
        "ix_lg_cyl_active_gas_state_ser",
        "CREATE INDEX IF NOT EXISTS ix_lg_cyl_active_gas_state_ser "
        "ON lg_cylinders (tenant_id, gas_group_id, current_state, serial) "
        "WHERE is_active = true",
    ),
    (
        "ix_lg_cyl_log_cyl_created",
        "CREATE INDEX IF NOT EXISTS ix_lg_cyl_log_cyl_created "
        "ON lg_cylinder_state_log (cylinder_id, created_at DESC)",
    ),
    (
        "ix_lg_ro_sess_created",
        "CREATE INDEX IF NOT EXISTS ix_lg_ro_sess_created "
        "ON lg_route_operations (session_id, created_at DESC)",
    ),
    (
        "ix_lg_ro_sess_stop_status",
        "CREATE INDEX IF NOT EXISTS ix_lg_ro_sess_stop_status "
        "ON lg_route_operations (session_id, route_stop_id, status)",
    ),
    (
        "ix_lg_ro_conf_sess_stop_perf",
        "CREATE INDEX IF NOT EXISTS ix_lg_ro_conf_sess_stop_perf "
        "ON lg_route_operations (session_id, route_stop_id, performed_at DESC) "
        "WHERE status = 'CONFIRMED'",
    ),
    (
        "ix_lg_ri_sess_created",
        "CREATE INDEX IF NOT EXISTS ix_lg_ri_sess_created "
        "ON lg_route_incidents (session_id, created_at DESC)",
    ),
    (
        "ix_lg_ri_sess_stop_status",
        "CREATE INDEX IF NOT EXISTS ix_lg_ri_sess_stop_status "
        "ON lg_route_incidents (session_id, route_stop_id, status)",
    ),
    (
        "ix_lg_ri_sess_updated",
        "CREATE INDEX IF NOT EXISTS ix_lg_ri_sess_updated "
        "ON lg_route_incidents (session_id, updated_at DESC)",
    ),
    (
        "ix_lg_waybill_sess_version",
        "CREATE INDEX IF NOT EXISTS ix_lg_waybill_sess_version "
        "ON lg_session_waybill_versions (session_id, version DESC)",
    ),
    (
        "ix_lg_waybill_active_sess_ver",
        "CREATE INDEX IF NOT EXISTS ix_lg_waybill_active_sess_ver "
        "ON lg_session_waybill_versions (session_id, version DESC) "
        "WHERE status = 'ACTIVE'",
    ),
    (
        "ix_lg_mov_tenant_wh_status_upd",
        "CREATE INDEX IF NOT EXISTS ix_lg_mov_tenant_wh_status_upd "
        "ON lg_movements (tenant_id, warehouse_id, status, updated_at DESC)",
    ),
    (
        "ix_lg_orders_tenant_status_cr",
        "CREATE INDEX IF NOT EXISTS ix_lg_orders_tenant_status_cr "
        "ON lg_orders (tenant_id, status, created_at DESC)",
    ),
    (
        "ix_lg_order_items_order_prod",
        "CREATE INDEX IF NOT EXISTS ix_lg_order_items_order_prod "
        "ON lg_order_items (order_id, product_id)",
    ),
]


def upgrade(db) -> None:
    bind = db.connection()
    for _, statement in INDEX_STATEMENTS:
        bind.execute(text(statement))


def downgrade(db) -> None:
    bind = db.connection()
    for index_name, _ in reversed(INDEX_STATEMENTS):
        bind.execute(text(f"DROP INDEX IF EXISTS {index_name}"))
