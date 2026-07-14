from __future__ import annotations

from pydantic import BaseModel, Field


class CustomerCylinderPipelineRead(BaseModel):
    total: int = 0
    in_vehicle: int = 0
    in_transit: int = 0
    in_warehouse: int = 0
    unknown: int = 0


class CustomerCylinderConditionSummaryRead(BaseModel):
    assigned: int = 0
    at_customer: int = 0
    pipeline: int = 0
    lost: int = 0


class CustomerCylinderProductSummaryRead(BaseModel):
    product_id: str | None = None
    product_name: str
    contracted: int = 0
    assigned: int = 0
    at_customer: int = 0
    at_customer_unknown: int = 0
    pipeline: CustomerCylinderPipelineRead = Field(default_factory=CustomerCylinderPipelineRead)
    lost: int = 0
    deviation: int = 0
    by_condition: dict[str, CustomerCylinderConditionSummaryRead] = Field(default_factory=dict)


class CustomerCylinderAlertRead(BaseModel):
    severity: str
    category: str
    message: str


class CustomerCylinderContractSnapshotRead(BaseModel):
    contract_id: str | None = None
    status: str
    active_contract_count: int = 0
    contract_ids: list[str] = Field(default_factory=list)


class CustomerCylinderTotalsRead(BaseModel):
    contracted: int = 0
    assigned: int = 0
    at_customer: int = 0
    at_customer_unknown: int = 0
    pipeline: int = 0
    lost: int = 0
    deviation: int = 0


class CustomerCylinderSummaryRead(BaseModel):
    customer_id: str
    customer_name: str
    contract: CustomerCylinderContractSnapshotRead
    summary: CustomerCylinderTotalsRead
    by_product: list[CustomerCylinderProductSummaryRead] = Field(default_factory=list)
    alerts: list[CustomerCylinderAlertRead] = Field(default_factory=list)
