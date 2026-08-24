# A.SPEC COMPRAS-007 — Retorno de cilindros por serial, cierre de custodia y vínculo opcional a jornadas

## WHY

La custodia del proveedor (COMPRAS-005) no tiene salida: los cilindros quedan
`EN_CUSTODIA` para siempre y nadie registra qué volvió ni cuándo (VISION
§13/§14/§26 incompletas; flujo 42 detenido en el paso 13). Además, cuando el
transporte lo hace un camión propio no hay forma de relacionar el despacho con
la jornada que lo ejecutó — sin ser obligatorio, porque muchas veces lleva el
transportista externo.

## WHAT

Tres verdades nuevas:

1. **Retorno por serial**: `POST /dispatches/{id}/return` recibe la lista
   explícita de `cylinder_id`s que volvieron → cada fila pasa a
   `status='DEVUELTO'` con `returned_at`. Retornos parciales permitidos e
   ilimitados (§43): cada llamada registra solo los que efectivamente
   regresaron.
2. **Cierre de custodia**: nuevo estado de despacho `RETORNADO`, alcanzable
   desde `DESPACHADO` únicamente cuando TODOS sus cilindros están `DEVUELTO`.
   Mientras haya alguno `EN_CUSTODIA`, el despacho sigue `DESPACHADO` y el
   saldo sigue visible como custodia (§45).
3. **Vínculo opcional a jornadas** (§9/§32): columnas `session_id`
   (traslado de ida) y `return_session_id` (recojo) sobre `com_dispatches`,
   ambas NULLABLE con endpoint `PATCH /dispatches/{id}/session-link`.
   Referencia pura: jamás modifica estados de Logística. Validaciones al
   asignar: sesión existe, mismo tenant, estado operativo
   (`READY_TO_DEPART|OUTBOUND|RETURNING`). Desvinculable mientras el despacho
   esté `PREPARADO`; tras `DESPACHADO` queda como registro histórico.

## SCOPE

- `migrations/004_dispatch_return_sessions.py`: +3 columnas
  (`session_id`, `return_session_id` FK lg_vehicle_sessions nullable;
  `returned_notes` no — se usa notes por item) y estado `RETORNado` es solo
  lógico (sin tabla nueva).
- `models.py`: columnas + `RETORNADO` en constantes.
- `services/dispatches.py`: matriz ampliada (`DESPACHADO → {RETORNADO}`),
  `register_return()`, validaciones de sesión.
- `routers/dispatches.py`: `/return`, `/session-link`; serialización con
  sesiones.
- Frontend: dialog "Registrar retorno" (lista de `EN_CUSTODIA` con checkbox),
  campos de jornada opcional en alta, badges de sesión en la lista.
- Permisos: reutiliza `compras.dispatch.manage`.

## OUT OF SCOPE

- Generación automática de paradas/movimientos en la jornada vinculada
  (escritura en Logística — prohibida hasta acuerdo inter-plugin).
- Conciliación contra `com_purchase_receipts` / cantidades comerciales (§17):
  el retorno concilia por serial de custodia, no por cantidad facturada.
- Actualización técnica del cilindro (PH/retimbrado → historial Logística).
- Devoluciones al proveedor de mercadería no conforme (§26 general).

## CONTRACT

Precondiciones:

- Despacho en `DESPACHADO` con al menos un ítem `EN_CUSTODIA`.

Postcondiciones:

- `/return` exitoso: cada serial listado pasa a `DEVUELTO` con `returned_at`
  exacto; los no listados permanecen `EN_CUSTODIA`; si ya no queda ninguno
  `EN_CUSTODIA`, el despacho transiciona a `RETORNADO` automáticamente.
- Serial ajeno al despacho o ya devuelto → 400 con detalle.
- `/session-link`: asigna/desasigna `session_id` o `return_session_id`
  según `kind` (`outbound`/`return`), validando tenant + estado operativo;
  rechazado si el despacho está `CANCELADO`.
- Consultas de custodia existentes no cambian de semántica (siguen filtrando
  `EN_CUSTODIA`; un despacho `RETORNADO` no aporta filas).

## INVARIANTS

```yaml
invariants:
  - "§45: el retorno nombra seriales, nunca cantidades."
  - "§45: una recepción/retorno parcial nunca cierra nada automáticamente
     salvo la custodia completa."
  - "§45: los seriales devueltos quedan historizados (returned_at) — no se
     borran filas."
  - "§32: cero escrituras en modelos lg_*; la sesión es referencia nullable."
  - "Suite previa (15 tests compras) sigue verde."
```

## VERIFICATION

- Nuevos tests `test_compras_dispatch.py`:
  - `test_return_marks_serials_devuelto_and_keeps_others_in_custody`
  - `test_return_rejects_foreign_or_already_returned_serial`
  - `test_all_returned_moves_dispatch_to_retornado`
  - `test_session_link_validates_tenant_and_operational_state`
  - `test_despachado_cannot_unlink_sessions`
- Suite previa compras 15/15 intacta; tsc limpio; vitest sin fallos nuevos.
- Manual: despacho con 3 seriales → retorno de 2 → custodia muestra 1 →
  retorno del último → despacho RETORNADO, custodia vacía.

## ROLLBACK

Reversible: revertir commits; migración 004 con downgrade que elimina las 2
columnas (datos de retorno se perderían — aceptable, son demo; backup previo).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/004_dispatch_return_sessions.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/dispatches.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/dispatches.py
    - plugins/commerce/purchase/backend/routers/dispatches.py
    - plugins/commerce/purchase/frontend/pages/DispatchesPage.tsx
    - plugins/commerce/purchase/frontend/components/DispatchFormModal.tsx
    - plugins/commerce/purchase/frontend/components/SupplierDetailModal.tsx
    - plugins/commerce/purchase/frontend/api.ts
    - plugins/commerce/purchase/frontend/types.ts
    - apps/api/tests/test_compras_dispatch.py
  prohibited:
    - plugins/logistics/**          # lg_vehicle_sessions: FK nullable + SELECT
    - plugins/stock/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.dispatches.retorno
    - compras.custody.cierre
  indirect:
    - compras.ui.despachos # acciones nuevas por estado
  must_not_affect:
    - jornadas operativas (solo lectura de validez)
    - órdenes/recepciones/stock
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-005 # despacho + custodia
    - COMPRAS-003 # estructura por dominio
  must_compose_with:
    - COMPRAS-008 # futura recepción comercial referenciará estos retornos
  systemic_invariants:
    - "Un serial DEVUELTO no vuelve a aparecer como custodia del proveedor."
  composition_checks:
    - Ciclo completo: crear → confirmar → retornar todos → RETORNADO y
      custodia vacía en detalle de proveedor.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: retorno y sesiones viven en el dominio dispatches existente
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/dispatches.py
```

## Traceability

- Requirement: usuario — "envío y retorno de cilindros a proveedor tendrá una
  conexión a jornadas… no obligatorio porque no siempre se lleva con camión de
  la empresa" (aprobado); VISION §13-15, §26, §32, §42-45.
- Commits: pendientes.

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
