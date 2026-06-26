from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CoreUserRead(BaseModel):
    id: str
    tenant_id: str
    branch_id: str | None
    name: str
    email: str
    active: bool
    roles: list[str]
    created_at: datetime
    updated_at: datetime


class CoreUserCreateRequest(BaseModel):
    name: str
    email: str
    password: str
    branch_id: str | None = None
    role_ids: list[str] = []


class CoreUserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None
    branch_id: str | None = None
    role_ids: list[str] | None = None


class CoreRoleRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    permissions: list[str]
    active: bool
    created_at: datetime
    updated_at: datetime


class CoreRoleCreateRequest(BaseModel):
    name: str
    permission_names: list[str] = []


class CoreRoleUpdateRequest(BaseModel):
    name: str | None = None
    permission_names: list[str] | None = None


class CoreBranchRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    code: str
    active: bool
    created_at: datetime
    updated_at: datetime


class CoreBranchCreateRequest(BaseModel):
    name: str
    code: str


class CoreBranchUpdateRequest(BaseModel):
    name: str | None = None
    code: str | None = None


class CorePermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    created_at: datetime


class CorePluginMigrateRequest(BaseModel):
    target_revision: str | None = None
