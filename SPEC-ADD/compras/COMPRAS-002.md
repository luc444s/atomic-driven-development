# A.SPEC COMPRAS-002 — Ciclo de vida completo de la orden de compra con auditoría

## WHY

La orden de compra (`com_purchase_orders`) tiene una máquina de estados mínima
(`DRAFT → ORDERED → {PARTIAL → RECEIVED} / CANCELLED`) implementada de forma
dispersa, sin auditoría de cambios (violando §36 de COMPRAS-VISION-001), sin
estado de cierre administrativo (§28) y con cancelación permitida incluso
cuando ya hay cantidades recibidas (violando §27). Además existe en
`services/orders.py` un setter genérico `update_order_status` que permitiría
saltear cualquier transición. El ciclo de vida es el esqueleto sobre el que
colgarán despacho por serial y custodia (COMPRAS-003/004): debe estar firme
antes.

## WHAT

Una sola verdad estructural: **todo cambio de estado de una orden pasa por una
única función de transición validada que registra un evento de auditoría**, y la
máquina de estados queda:

```text
DRAFT ──confirm──▶ ORDERED ──recepción parcial──▶ PARTIAL ──resto──▶ RECEIVED
  │                  │                               │                  │
  └──cancel──▶ CANCELLED ◀──cancel (solo si received_qty=0)──┘         ├──close(reason)──▶ CLOSED
                                                            RECEIVED ──┘
```

Comportamientos observables nuevos:

1. `POST /orders/{id}/close` con `reason` obligatorio: `RECEIVED` o `PARTIAL`
   → `CLOSED` (cierre administrativo §28).
2. `POST /orders/{id}/cancel` rechazado con 400 cuando algún item tiene
   `received_qty > 0` (§27).
3. Toda transición exitosa inserta una fila en `com_purchase_order_events`
   (`order_id`, `from_status`, `to_status`, `reason`, `user_id`, `created_at`).
4. `GET /orders/{id}` incluye el historial de eventos.
5. Eliminado el setter genérico `update_order_status` (código muerto, backdoor
   de la máquina de estados).
6. Las recepciones automáticas (`PARTIAL`, `RECEIVED`) también registran evento,
   con `reason="AUTO_RECEIPT"`.

## SCOPE

- Migración `plugins/commerce/migrations/002_purchase_order_events.py`
  (tabla `com_purchase_order_events`, patrón `__table__.create(checkfirst=True)`).
- Modelo `ComPurchaseOrderEvent` + relación `events` en `ComPurchaseOrder`.
- `services/orders.py`: función central `transition(order, target, user_id,
  reason=None)`; reglas de cancelación; eliminación de `update_order_status`.
- `services/receipts.py`: transiciones automáticas pasan por `transition`.
- `router.py`: endpoint `/close`; serialización del historial en detail;
  `CloseOrderRequest(reason: str)`.
- Frontend `PurchaseOrdersPage.tsx`: badge semántico por estado, botones
  contextuales (confirmar/cancelar/cerrar), dialog de cierre con motivo
  obligatorio.

## OUT OF SCOPE

- Estados `PENDING_APPROVAL` / `APPROVED` / `SENT` separados (§7 políticas):
  diferidos; `ORDERED` significa "aprobada y enviada" en un paso.
- Despacho de envases, custodia, conciliación por serial (COMPRAS-003/004).
- Facturas de proveedor y conciliación tres vías (COMPRAS-005).
- Edición de orden en estados ≠ DRAFT.
- Reapertura de órdenes cerradas (forward-only).

## CONTRACT

Precondiciones:

- Plugin `compras` enabled; tablas `com_purchase_*` existen (migración 0001).

Postcondiciones:

- Matriz de transiciones válidas:
  - `DRAFT → {ORDERED, CANCELLED}`
  - `ORDERED → {PARTIAL, RECEIVED, CANCELLED, CLOSED}`
    (PARTIAL/RECEIVED solo vía recepción; CANCELLED solo si `received_qty=0`
    en todos los items)
  - `PARTIAL → {RECEIVED, CLOSED}`
  - `RECEIVED → {CLOSED}`
  - `CLOSED`, `CANCELLED`: terminales.
- Ninguna ruta de código modifica `status` fuera de `transition()`.
- Cada cambio de estado tiene exactamente un evento de auditoría con usuario.

## INVARIANTS

```yaml
invariants:
  - Cancelar una orden no borra su historia ni sus recepciones (§27/§45).
  - Una recepción parcial nunca deja la orden en RECEIVED (§43/§45).
  - El stock solo se mueve vía el conector existente en receipts; el ciclo de
    vida no toca inventario (§33).
  - Los endpoints existentes (list/get/create/update DRAFT/confirm/cancel/
    receive) mantienen su contrato actual salvo las reglas nuevas declaradas.
  - Multi-tenant: toda query sigue filtrando por tenant_id.
```

## VERIFICATION

- Backend: extender `apps/api/tests/test_compras_plugin.py`:
  - `test_order_close_requires_reason_and_terminal_state`
  - `test_cancel_blocked_when_received_qty_positive`
  - `test_every_transition_writes_audit_event`
  - `test_generic_status_setter_removed` (import falla → AttributeError)
  - Tests existentes de lifecycle/receive deben seguir pasando sin cambios.
- Migración: correr plugin runtime y verificar tabla
  `com_purchase_order_events` creada; downgrade la elimina.
- Frontend: `npx tsc --noEmit` limpio; manual: orden DRAFT muestra
  Confirmar/Cancelar; ORDERED muestra Cerrar (deshabilitado hasta RECEIVED/PARTIAL);
  dialog de cierre exige motivo.

## ROLLBACK

Reversible: revertir commit(s); la migración tiene `downgrade` que elimina la
tabla de eventos. La tabla nueva no afecta datos existentes (solo agrega
historial desde su creación). Sin efectos irreversibles.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/002_purchase_order_events.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas.py
    - plugins/commerce/purchase/backend/services/orders.py
    - plugins/commerce/purchase/backend/services/receipts.py
    - plugins/commerce/purchase/backend/router.py
    - plugins/commerce/purchase/frontend/pages/PurchaseOrdersPage.tsx
    - plugins/commerce/purchase/frontend/api.ts
    - plugins/commerce/purchase/frontend/types.ts
    - apps/api/tests/test_compras_plugin.py
  prohibited:
    - plugins/logistics/**
    - plugins/stock/**
    - vendor/**
    - apps/web/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.orders.lifecycle
    - compras.orders.audit
  indirect:
    - compras.receipts # transiciones automáticas pasan por transition()
  must_not_affect:
    - logistics (jornadas, cilindros)
    - stock ledger
    - crm clientes
    - suppliers CRUD existente
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-001 # plugin structure enabled
    - COMPRAS-VISION-001 # baseline normativa (§6, §27, §28, §36)
  must_compose_with:
    - COMPRAS-003 # despacho por serial consumirá ORDERED como precondición
    - COMPRAS-004 # recepción parcial respetará PARTIAL/CLOSED
  systemic_invariants:
    - "Una orden CLOSED o CANCELLED no acepta nuevas recepciones."
  composition_checks:
    - Recibir sobre orden CLOSED debe fallar 400.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: la máquina de estados vive SOLO en services/orders.py
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/orders.py::transition (única puerta de mutación de status)
```

## Traceability

- Requirement: plan aprobado por usuario ("ok asi") tras diagnóstico del
  ciclo de vida; COMPRAS-VISION-001 §6, §27, §28, §36, §45.
- Commit: pendiente.

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
