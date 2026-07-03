---
name: api-rest-connector
description: API REST, inter-plugin, inter-module, logistics, crm, productos, stock. Use when connecting two modules or plugins through public REST endpoints instead of direct imports, shared table assumptions, or ad-hoc frontend calls.
---

# API REST Connector

Use this skill when implementing or refactoring communication between modules through REST.

Typical triggers:

- "conectar crm con logistics"
- "usar puntos de entrega desde el modal de cliente"
- "consumir catalogos de productos desde logistics"
- "interconectar modulos por api rest"
- "evitar import directo entre plugins"

## Goal

Connect modules through explicit REST contracts without breaking ownership boundaries.

## Core rules

1. The owner module exposes data; the consumer module reads it.
2. Do not move business ownership just to simplify a screen.
3. Prefer REST over direct frontend imports between domains when the integration is domain-to-domain.
4. Do not read another module's tables directly from a consumer frontend.
5. Do not introduce hidden coupling through ad-hoc response shapes.
6. If the consumer needs historical stability, keep snapshot fields in the consumer transaction tables.
7. Respect tenant, branch, warehouse, and permission scope on every endpoint.

## Ownership checklist

Before writing code, identify:

- which module owns the source data;
- whether the consumer needs live read or stored snapshot;
- whether the interaction is read-only or write-capable;
- whether the integration is synchronous REST or better modeled as event-driven.

## When REST is the right tool

Use REST when:

- one module needs to read operational or catalog data from another;
- the consumer needs explicit request/response behavior;
- the flow is user-driven and immediate;
- the data should stay owned by the source module.

Prefer events when:

- the goal is notification, propagation, or audit trail;
- the consumer does not need immediate request-time data;
- the integration should be loosely coupled.

## Required implementation steps

### 1. Confirm the source contract

- Reuse an existing endpoint if it already matches the need.
- If not, add the smallest new endpoint in the owner module.
- Keep request and response schemas explicit.

### 2. Preserve module boundaries

- Backend consumer code should not depend on internal services of another plugin unless there is an already-accepted project pattern for same-process shared DB reads.
- Frontend consumer code should prefer API calls, not importing another module's private page logic.

### 3. Handle names vs IDs correctly

- Do not show raw UUIDs to users.
- If the source returns only IDs, either:
  - extend the source endpoint with resolved labels; or
  - resolve them from the correct catalog in the consumer.
- Use `-` or `Sin asignar` instead of raw IDs when resolution fails.

### 4. Decide live read vs snapshot

- Live read for catalogs, customer detail, delivery points, current config.
- Snapshot for transactional history, generated documents, or audit-sensitive flows.

### 5. Add permission and scope checks

- Validate the endpoint in the owner module with the proper permission.
- Enforce tenant isolation.
- Enforce branch or warehouse scope when applicable.

### 6. Update the consumer API client

- Add typed client function.
- Add query keys.
- Keep naming aligned with the owner module endpoint.

### 7. Update docs and tests

- Update the relevant spec or progress doc if behavior changes.
- Add or update tests for:
  - happy path;
  - empty state;
  - permission denial if relevant;
  - missing related data;
  - scope filtering.

## Recommended patterns

### Read-only catalog integration

- Owner exposes `/catalog/...` or `/search/...`
- Consumer fetches through its API layer
- Consumer stores selected `id`
- Consumer optionally stores label snapshot only if the record is transactional

### Embedded operational section

Example: CRM customer detail embedding delivery points from logistics.

- Logistics remains owner of delivery points.
- CRM calls logistics REST.
- CRM renders summarized data.
- Editing should deep-link or open the logistics editor unless CRM is explicitly allowed to manage that data.

### Cross-module create/update flow

- Consumer should submit to the owner endpoint.
- Do not duplicate create/update logic in the consumer.
- If the owner requires IDs from another module, resolve them in the owner service, not in scattered frontend code.

## Anti-patterns

- Importing another plugin's internal page component just to access its state logic.
- Reading another module's DB tables directly from the consumer frontend.
- Returning raw foreign keys without labels and expecting the UI to guess.
- Copying catalog tables into the consumer module without an explicit migration strategy.
- Letting the consumer become the new source of truth for another module's data.

## Minimal delivery checklist

- owner endpoint exists;
- consumer API client exists;
- types are explicit;
- UUIDs are not shown as user-facing fallback;
- scope and permissions are enforced;
- docs updated;
- build/tests pass.

## Project-specific notes

- In this repo, `productos` owns product master data and brands.
- `crm` owns customers.
- `logistics` owns delivery points, routes, movements, and cylinder operations.
- `stock` owns balances, ledger, and min/max config.
- If a module only needs another module's operational data, keep that read through REST unless an accepted spec says otherwise.
