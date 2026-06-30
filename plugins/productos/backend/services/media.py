from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.config import PROJECT_ROOT
from plugins.productos.backend.common import ProductosActionContext, audit_productos_action
from plugins.productos.backend.models import Product, ProductMedia

MEDIA_ROOT = PROJECT_ROOT / "data" / "media" / "products"


def list_media(db: Session, *, product_id: str) -> list[ProductMedia]:
    return list(
        db.scalars(
            select(ProductMedia)
            .where(ProductMedia.product_id == product_id)
            .order_by(ProductMedia.is_primary.desc(), ProductMedia.created_at.asc())
        ).all()
    )


def require_media(db: Session, *, product_id: str, media_id: str) -> ProductMedia:
    media = db.scalar(
        select(ProductMedia).where(
            ProductMedia.product_id == product_id, ProductMedia.id == media_id
        )
    )
    if media is None:
        raise ValueError("Media del producto no encontrado")
    return media


def create_media(
    db: Session,
    *,
    product: Product,
    media_type: str,
    is_primary: bool,
    filename: str,
    content: bytes,
    action_context: ProductosActionContext,
) -> ProductMedia:
    product_dir = MEDIA_ROOT / product.id
    product_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_filename(filename)
    media_id = str(uuid4())
    stored_name = f"{media_id}_{safe_name}"
    file_path = product_dir / stored_name
    file_path.write_bytes(content)
    if is_primary:
        _clear_primary_media(db, product_id=product.id)
    url = f"/api/v1/plugins/productos/products/{product.id}/media/{media_id}/download/{stored_name}"
    item = ProductMedia(
        id=media_id,
        tenant_id=product.tenant_id,
        product_id=product.id,
        media_type=media_type.strip().upper(),
        url=url,
        is_primary=is_primary,
    )
    db.add(item)
    db.flush()
    if not _has_primary_media(db, product_id=product.id):
        item.is_primary = True
        db.add(item)
        db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.media.create",
        entity_type="product_media",
        entity_id=item.id,
        details={"product_id": product.id, "media_type": item.media_type, "url": item.url},
    )
    return item


def delete_media(
    db: Session,
    *,
    media: ProductMedia,
    action_context: ProductosActionContext,
) -> None:
    path = resolve_media_path(media)
    if path.exists():
        path.unlink()
    product_id = media.product_id
    was_primary = media.is_primary
    db.delete(media)
    db.flush()
    replacement = db.scalar(
        select(ProductMedia)
        .where(ProductMedia.product_id == product_id)
        .order_by(ProductMedia.created_at.asc())
        .limit(1)
    )
    if was_primary and replacement is not None:
        replacement.is_primary = True
        db.add(replacement)
        db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.media.delete",
        entity_type="product_media",
        entity_id=media.id,
        details={"product_id": product_id},
    )


def set_primary_media(
    db: Session,
    *,
    media: ProductMedia,
    action_context: ProductosActionContext,
) -> ProductMedia:
    _clear_primary_media(db, product_id=media.product_id)
    media.is_primary = True
    db.add(media)
    db.flush()
    audit_productos_action(
        db,
        context=action_context,
        action="product.media.set_primary",
        entity_type="product_media",
        entity_id=media.id,
        details={"product_id": media.product_id},
    )
    return media


def resolve_media_path(media: ProductMedia) -> Path:
    stored_name = media.url.rstrip("/").split("/")[-1]
    return MEDIA_ROOT / media.product_id / stored_name


def _clear_primary_media(db: Session, *, product_id: str) -> None:
    current = list(
        db.scalars(
            select(ProductMedia).where(
                ProductMedia.product_id == product_id,
                ProductMedia.is_primary.is_(True),
            )
        ).all()
    )
    for item in current:
        item.is_primary = False
        db.add(item)
    db.flush()


def _has_primary_media(db: Session, *, product_id: str) -> bool:
    return (
        db.scalar(
            select(ProductMedia.id).where(
                ProductMedia.product_id == product_id,
                ProductMedia.is_primary.is_(True),
            )
        )
        is not None
    )


def _safe_filename(filename: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", filename.strip())
    return cleaned or "archivo"
