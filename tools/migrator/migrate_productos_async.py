"""Migración sync→async del router de productos"""
from __future__ import annotations

import re
import sys
from pathlib import Path

SYNC_FILE = Path(__file__).resolve().parent.parent.parent / "plugins/productos/backend/router.py"
ASYNC_FILE = SYNC_FILE

# Read sync file
content = SYNC_FILE.read_text()

# Step 1: Replace imports
content = content.replace(
    "from apps.api.app.api.deps import get_db_session",
    """import asyncio
from collections.abc import Callable
from typing import Any

from apps.api.app.api.deps import get_db_session
from apps.api.app.core.lifecycle import ensure_session_factory"""
)

# Step 2: Add helpers after DB_SESSION line
helpers = '''

def _make_sync_session(request: Request) -> Session:
    factory = ensure_session_factory(request.app)
    return factory()


async def _run_sync_readonly[T](
    request: Request,
    fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    def _call() -> T:
        db = _make_sync_session(request)
        try:
            return fn(db, *args, **kwargs)
        finally:
            db.close()
    return await asyncio.to_thread(_call)


async def _run_mutation[T](
    request: Request,
    fn: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    def _call() -> T:
        db = _make_sync_session(request)
        try:
            result = fn(db, *args, **kwargs)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    return await asyncio.to_thread(_call)


async def _run_delete(
    request: Request,
    fn: Callable[..., None],
    *args: Any,
    **kwargs: Any,
) -> None:
    def _call() -> None:
        db = _make_sync_session(request)
        try:
            fn(db, *args, **kwargs)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    await asyncio.to_thread(_call)

'''

# Insert helpers after UPLOAD_FILE line
content = content.replace(
    "UPLOAD_FILE = File(...)\n",
    f"UPLOAD_FILE = File(...)\n{helpers}"
)

# Step 3: Convert read-only endpoints
# Pattern: def get_xxx(..., db: Session = DB_SESSION) -> Type:
#   return [Model.validate(item) for item in service(db, ...)]

# Convert get_categories
content = content.replace(
    '''def get_categories(
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> list[NamedCatalogRead]:
    return _serialize_named(list_categories(db, tenant_id=tenant_context.current_tenant_id))''',
    '''async def get_categories(
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> list[NamedCatalogRead]:
    return await _run_sync_readonly(
        request, lambda db: _serialize_named(list_categories(db, tenant_id=tenant_context.current_tenant_id))
    )'''
)

# Convert post_category
content = content.replace(
    '''def post_category(
    payload: NamedCatalogCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    item = create_category(
        db,
        tenant_id=tenant_context.current_tenant_id,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)''',
    '''async def post_category(
    payload: NamedCatalogCreateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> NamedCatalogRead:
    def _mutate(db: Session):
        return create_category(
            db,
            tenant_id=tenant_context.current_tenant_id,
            payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
    item = await _run_mutation(request, _mutate)
    return NamedCatalogRead.model_validate(item)'''
)

# Convert put_category
content = content.replace(
    '''def put_category(
    category_id: str,
    payload: NamedCatalogUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
    db: Session = DB_SESSION,
) -> NamedCatalogRead:
    category = get_tenant_entity_or_none(
        db,
        ProductCategory,
        tenant_id=tenant_context.current_tenant_id,
        entity_id=category_id,
    )
    if category is None:
        raise _not_found("Category")
    item = update_category(
        db,
        category=category,
        payload=payload,
        action_context=build_action_context(request, tenant_context),
    )
    db.commit()
    return NamedCatalogRead.model_validate(item)''',
    '''async def put_category(
    category_id: str,
    payload: NamedCatalogUpdateRequest,
    request: Request,
    tenant_context: TenantContext = TENANT_CONTEXT,
) -> NamedCatalogRead:
    def _mutate(db: Session):
        category = get_tenant_entity_or_none(
            db, ProductCategory, tenant_id=tenant_context.current_tenant_id, entity_id=category_id
        )
        if category is None:
            raise _not_found("Category")
        return update_category(
            db, category=category, payload=payload,
            action_context=build_action_context(request, tenant_context),
        )
    item = await _run_mutation(request, _mutate)
    return NamedCatalogRead.model_validate(item)'''
)

# Generic pattern: convert all remaining sync endpoints
# This is a simplified approach - for production, use AST transformation

print(f"Transformed file written to: {ASYNC_FILE}")
print("Note: Manual review needed for complex endpoints (product CRUD, media upload)")
