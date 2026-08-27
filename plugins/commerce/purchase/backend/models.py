from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from systutor.core.database import Base


def _new_uuid() -> str:
    return str(uuid4())


def _utc_now() -> datetime:
    return datetime.now(UTC)


class ComSupplier(Base):
    __tablename__ = "com_suppliers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    commercial_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    document_type_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(5), nullable=True, default="PE")
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_term_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    billing_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    accounting_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    fiscal_operation_key: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tax_regime_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    orders: Mapped[list[ComPurchaseOrder]] = relationship(back_populates="supplier")
    addresses: Mapped[list[ComSupplierAddress]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    contacts: Mapped[list[ComSupplierContact]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    bank_accounts: Mapped[list[ComSupplierBankAccount]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )
    payment_terms: Mapped[list[ComSupplierPaymentTerm]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan"
    )


class ComSupplierAddress(Base):
    __tablename__ = "com_supplier_addresses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    line1: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str] = mapped_column(String(5), nullable=False, default="PE")
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    supplier: Mapped[ComSupplier] = relationship(back_populates="addresses")


class ComSupplierContact(Base):
    __tablename__ = "com_supplier_contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    supplier: Mapped[ComSupplier] = relationship(back_populates="contacts")


class ComSupplierBankAccount(Base):
    __tablename__ = "com_supplier_bank_accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_holder: Mapped[str] = mapped_column(String(200), nullable=False)
    iban: Mapped[str] = mapped_column(String(34), nullable=False)
    bic_swift: Mapped[str | None] = mapped_column(String(11), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    supplier: Mapped[ComSupplier] = relationship(back_populates="bank_accounts")


class ComSupplierPaymentTerm(Base):
    __tablename__ = "com_supplier_payment_terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    payment_term_code: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(250), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    supplier: Mapped[ComSupplier] = relationship(back_populates="payment_terms")


class ComPurchaseOrder(Base):
    __tablename__ = "com_purchase_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    branch_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="DRAFT")
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    items: Mapped[list[ComPurchaseItem]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    receipts: Mapped[list[ComPurchaseReceipt]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    events: Mapped[list[ComPurchaseOrderEvent]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    supplier: Mapped[ComSupplier] = relationship(back_populates="orders")


class ComPurchaseOrderEvent(Base):
    __tablename__ = "com_purchase_order_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    order: Mapped[ComPurchaseOrder] = relationship(back_populates="events")


class ComPurchaseItem(Base):
    __tablename__ = "com_purchase_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[str] = mapped_column(
        ForeignKey("prod_products.id"), nullable=False, index=True
    )
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    received_qty: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    order: Mapped[ComPurchaseOrder] = relationship(back_populates="items")


class ComPurchaseReceipt(Base):
    __tablename__ = "com_purchase_receipts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=False, index=True
    )
    warehouse_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    receipt_date: Mapped[date] = mapped_column(Date, nullable=False)
    dispatch_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_dispatches.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    # COMPRAS-009: distinción comercial aceptadas/rechazadas + diferencia
    qty_accepted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    qty_rejected: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difference_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    incidence_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    commercial_closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    commercial_closed_by: Mapped[str | None] = mapped_column(String(36), nullable=True)

    order: Mapped[ComPurchaseOrder] = relationship(back_populates="receipts")
    cost_lines: Mapped[list[ComReceiptCostLine]] = relationship(
        back_populates="receipt", cascade="all, delete-orphan"
    )


class ComReceiptCostLine(Base):
    """COMPRAS-010: costos adicionales de una recepción (flete, arancel, ...)."""

    __tablename__ = "com_receipt_cost_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    receipt_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_receipts.id"), nullable=False, index=True
    )
    cost_type: Mapped[str] = mapped_column(String(20), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    receipt: Mapped[ComPurchaseReceipt] = relationship(back_populates="cost_lines")


class ComSupplierInvoice(Base):
    """COMPRAS-011: factura de proveedor vinculada a una orden."""

    __tablename__ = "com_supplier_invoices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=False, index=True
    )
    invoice_number: Mapped[str] = mapped_column(String(60), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")
    subtotal: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    tax: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="REGISTRADA")

    lines: Mapped[list[ComSupplierInvoiceLine]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )


class ComSupplierInvoiceLine(Base):
    __tablename__ = "com_supplier_invoice_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    invoice_id: Mapped[str] = mapped_column(
        ForeignKey("com_supplier_invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_item_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_purchase_items.id"), nullable=True, index=True
    )
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("prod_products.id"), nullable=True, index=True
    )
    qty: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False)
    line_total: Mapped[float] = mapped_column(Numeric(19, 4), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    invoice: Mapped[ComSupplierInvoice] = relationship(back_populates="lines")


class ComDispatch(Base):
    __tablename__ = "com_dispatches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=True, index=True
    )
    warehouse_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    dispatch_date: Mapped[date] = mapped_column(Date, nullable=False)
    carrier: Mapped[str | None] = mapped_column(String(120), nullable=True)
    vehicle_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    driver_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PREPARADO")
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=True, index=True
    )
    return_session_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=True, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now
    )

    cylinders: Mapped[list[ComDispatchCylinder]] = relationship(
        back_populates="dispatch", cascade="all, delete-orphan"
    )


class ComDispatchCylinder(Base):
    __tablename__ = "com_dispatch_cylinders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    dispatch_id: Mapped[str] = mapped_column(
        ForeignKey("com_dispatches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    product_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    service_type: Mapped[str] = mapped_column(String(30), nullable=False, default="LLENADO")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDIENTE")
    returned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    dispatch: Mapped[ComDispatch] = relationship(back_populates="cylinders")


class ComSupplierClaim(Base):
    """COMPRAS-012: reclamación al proveedor sobre una orden."""

    __tablename__ = "com_supplier_claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    order_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=False, index=True
    )
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    receipt_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_purchase_receipts.id"), nullable=True, index=True
    )
    invoice_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_supplier_invoices.id"), nullable=True, index=True
    )
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ABIERTA")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="MANUAL")
    opened_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    resolved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ComReceiptServiceLine(Base):
    """COMPRAS-014: servicio realizado por el proveedor a un serial en recepción.

    El costo es descriptivo: NO alimenta conciliación (011) ni costos (010).
    Referencia a lg_cylinders es de solo lectura (snapshot `serial` guardado).
    COMPRAS-015: datos legales de PH/retimbrado (fecha, resultado, vigencia,
    referencia documental) viven SOLO aquí — nunca en lg_cylinders.
    """

    __tablename__ = "com_receipt_service_lines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    receipt_id: Mapped[str] = mapped_column(
        ForeignKey("com_purchase_receipts.id"), nullable=False, index=True
    )
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    serial: Mapped[str] = mapped_column(String(50), nullable=False)
    service_type: Mapped[str] = mapped_column(String(30), nullable=False)
    cost: Mapped[float | None] = mapped_column(Numeric(19, 4), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_test_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    document_ref: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class ComSupplierClaimEvent(Base):
    """COMPRAS-012: timeline auditable de una reclamación."""

    __tablename__ = "com_supplier_claim_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    claim_id: Mapped[str] = mapped_column(
        ForeignKey("com_supplier_claims.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


class ComPhysicalCount(Base):
    """COMPRAS-017: sesión de conteo físico serial-by-serial de la custodia.

    El snapshot de custodia se PERSISTE al crear (expected_serials) y es la
    base inmutable del diff al cerrar. La custodia (005) NUNCA se muta desde
    un conteo: las discrepancias se resuelven por decisión registrada (§45).
    """

    __tablename__ = "com_physical_counts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_id: Mapped[str] = mapped_column(
        ForeignKey("com_suppliers.id"), nullable=False, index=True
    )
    order_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_purchase_orders.id"), nullable=True, index=True
    )
    dispatch_id: Mapped[str | None] = mapped_column(
        ForeignKey("com_dispatches.id"), nullable=True, index=True
    )
    expected_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    found_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="EN_CURSO")
    counted_by: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    counted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    expected_serials: Mapped[list[ComPhysicalCountExpectedSerial]] = relationship(
        back_populates="count", cascade="all, delete-orphan"
    )
    items: Mapped[list[ComPhysicalCountItem]] = relationship(
        back_populates="count", cascade="all, delete-orphan"
    )
    events: Mapped[list[ComPhysicalCountEvent]] = relationship(
        back_populates="count", cascade="all, delete-orphan"
    )


class ComPhysicalCountExpectedSerial(Base):
    """COMPRAS-017: snapshot persistido e inmutable de la custodia al crear.

    Sobrevive reinicios y cierre: es la base del diff serial-by-serial y de
    la auditoría (append-only tras creación, nunca se edita ni borra).
    """

    __tablename__ = "com_physical_count_expected_serials"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    count_id: Mapped[str] = mapped_column(
        ForeignKey("com_physical_counts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    serial: Mapped[str] = mapped_column(String(50), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    count: Mapped[ComPhysicalCount] = relationship(back_populates="expected_serials")


class ComPhysicalCountItem(Base):
    """COMPRAS-017: discrepancia del diff (FALTANTE | NO_DECLARADO | CONDICION).

    Append-only tras creación: la resolución solo estampa quién/cuándo/cómo.
    NO_DECLARADO precede sobre CONDICION (serial no esperado es NO_DECLARADO
    aunque traiga condition_note, que se conserva en `notes`).
    """

    __tablename__ = "com_physical_count_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    count_id: Mapped[str] = mapped_column(
        ForeignKey("com_physical_counts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    cylinder_id: Mapped[str] = mapped_column(
        ForeignKey("lg_cylinders.id"), nullable=False, index=True
    )
    serial: Mapped[str] = mapped_column(String(50), nullable=False)
    expected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    found: Mapped[bool] = mapped_column(Boolean, nullable=False)
    discrepancy_type: Mapped[str] = mapped_column(String(30), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolution: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resolved_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    count: Mapped[ComPhysicalCount] = relationship(back_populates="items")


class ComPhysicalCountEvent(Base):
    """COMPRAS-017: timeline auditable de la sesión de conteo."""

    __tablename__ = "com_physical_count_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    count_id: Mapped[str] = mapped_column(
        ForeignKey("com_physical_counts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)

    count: Mapped[ComPhysicalCount] = relationship(back_populates="events")
