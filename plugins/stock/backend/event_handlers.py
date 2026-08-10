from __future__ import annotations

from packages.contracts.events import EventContract
from packages.sdk import PluginContext
from plugins.stock.backend.services.balances import ensure_balances_for_product


def build_product_created_handler(context: PluginContext):
    def handle_product_created(event: EventContract) -> None:
        product_id = event.payload.get("product_id")
        tenant_id = event.tenant_id
        if not isinstance(product_id, str) or not isinstance(tenant_id, str):
            return
        if context.db_session_provider is None:
            raise RuntimeError("stock product-created handler requires db_session_provider")

        with context.db_session_provider() as db:
            ensure_balances_for_product(db, tenant_id=tenant_id, product_id=product_id)
            db.commit()

    return handle_product_created
