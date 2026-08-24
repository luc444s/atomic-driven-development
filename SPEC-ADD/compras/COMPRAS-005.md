# A.SPEC COMPRAS-005 — Despacho de envases por serial y custodia del proveedor

## WHY

El núcleo del módulo para una empresa de gases (VISION §42): enviar cilindros
propios al proveedor para llenado o servicios técnicos, saber **exactamente
qué seriales salieron** (§9: "50 cilindros enviados" no reemplaza el detalle),
registrar que quedan bajo **custodia del proveedor** (§11) y poder consultarlos
en todo momento. Hoy `com_purchase_receipts` registra cantidades sin identidad
de envase y la tarjeta "Envases en custodia" del detalle de proveedor es un
placeholder vacío (COMPRAS-004).

## WHAT

Una sola verdad estructural nueva: **existe un registro comercial por-serial de
los envases enviados a cada proveedor y de su custodia**, consultable, sin que
Compras escriba en Logística.

1. Tablas nuevas (`migrations/003_dispatches.py`):
   - `com_dispatches`: id, tenant_id, supplier_id (FK com_suppliers),
     order_id (FK com_purchase_orders, nullable = despacho suelto),
     warehouse_id origen, dispatch_date, carrier/vehicle/driver (opcionales),
     status (`PREPARADO` | `DESPACHADO` | `CANCELADO`), notes, created_by,
     created_at/updated_at.
   - `com_dispatch_cylinders`: id, tenant_id, dispatch_id (FK CASCADE),
     cylinder_id (FK lg_cylinders — **solo lectura**), product_id (gas
     esperado), service_type (`LLENADO | PH | RETIMBRADO | INSPECCION |
     REPARACION | CAMBIO_VALVULA | ACONDICIONAMIENTO | CERTIFICACION | MIXTO`),
     status (`EN_CUSTODIA` → `DEVUELTO`), returned_at nullable, notes.
2. La **custodia es estado derivado**: un cilindro está "en custodia del
   proveedor X" mientras su fila tenga `status='EN_CUSTODIA'`. Sin tablas ni
   sincronización extra.
3. Transiciones del despacho: `PREPARADO → DESPACHADO` (confirm; aquí nace la
   custodia de todos sus cilindros) · `PREPARADO → CANCELADO`. `DESPACHADO` y
   `CANCELADO` terminales hasta que COMPRAS-006 agregue devoluciones.
4. Validaciones al agregar un serial (§8): existe y pertenece al tenant · no
   está en OTRO despacho `DESPACHADO` con filas `EN_CUSTODIA` · estado activo
   en Logística (no bloqueado/fuera de servicio) · no duplicado dentro del
   mismo despacho.
5. API bajo `/purchase/dispatches`: POST `` (crear PREPARADO con items por
   cylinder_id + service_type), GET `` (filtros supplier_id/status),
   GET `/{id}`, POST `/{id}/confirm`, POST `/{id}/cancel`,
   GET `/suppliers/{supplier_id}/custody` (lista con `days_out` calculado),
   GET `/custody/summary` (por proveedor: cantidad, más antiguo). Filtro
   `days_gt=` en custody para permanencia básica (§12).
6. Permisos nuevos: `compras.dispatch.read`, `compras.dispatch.manage`.
7. Frontend: ruta `commerce/dispatches` ("Despachos") con lista + botón
   "Nuevo despacho" (`DispatchFormModal`: proveedor + orden opcional +
   selección de cilindros con validaciones en vivo); el tile "Envases en
   custodia" del detalle de proveedor pasa de placeholder a real (dialog con
   serial/gas/servicio/días fuera/orden).

## SCOPE

- Backend: `models.py` (+2 clases), `migrations/003_dispatches.py`,
  `schemas/dispatches.py`, `services/dispatches.py`,
  `routers/dispatches.py`, `routers/__init__.py` (+1 include),
  registro de permisos del plugin.
- Frontend: `types.ts`, `api.ts`, `pages/DispatchesPage.tsx`,
  `components/DispatchFormModal.tsx`, tile de custodia en
  `SupplierDetailModal.tsx`, `register.ts`.
- Tests: nuevo `apps/api/tests/test_compras_dispatch.py`.

## OUT OF SCOPE

- **Escritura en Logística**: Compras lee `lg_cylinders` pero NO crea
  movimientos ni cambia ubicación/estado del envase (§32). La salida física
  real se conectará cuando Logística exponga el movimiento correspondiente.
- Retorno/devolución de cilindros y conciliación por serial en recepción
  (COMPRAS-006).
- Alertas automáticas de permanencia (solo consulta `days_gt=`).
- Recepción vinculada al despacho (el despacho convive con los receipts
  actuales sin acoplarse).
- Servicios técnicos: actualización del historial técnico del cilindro (§19/20)
  — Compras solo registra qué servicio se contrató.

## CONTRACT

Precondiciones:

- Plugin compras enabled con migraciones 0001-0002 aplicadas.
- Existen proveedores y cilindros en `lg_cylinders` para operar.

Postcondiciones:

- Confirmar un despacho traslada todas sus filas a `EN_CUSTODIA`; desde ese
  momento `GET /suppliers/{id}/custody` las lista con `days_out >= 0`.
- Ningún cilindro puede figurar `EN_CUSTODIA` en dos despachos simultáneos.
- Cancelar un despacho `PREPARADO` no deja rastro de custodia (nunca llegó a
  existir); cancelar un `DESPACHADO` es rechazado 400.
- Los endpoints respetan tenant_id en toda lectura/escritura.

## INVARIANTS

```yaml
invariants:
  - "§9: el detalle por serial nunca se colapsa a cantidades."
  - "§32: cero escrituras de Compras sobre modelos de Logistics (lg_*):
     solo SELECT para validar identidad/estado."
  - "§45: un cilindro EN_CUSTODIA permanece visible como propiedad en
     custodia del proveedor hasta su devolución (COMPRAS-006)."
  - "La máquina de estados de órdenes (COMPRAS-002) no se toca; un despacho
     puede existir sin orden asociada."
  - "Suite existente 11/11 sigue verde sin modificaciones."
```

## VERIFICATION

- Nuevo `apps/api/tests/test_compras_dispatch.py`:
  - `test_dispatch_create_requires_valid_tenant_cylinders`
  - `test_dispatch_rejects_duplicate_serial_and_cylinders_in_other_custody`
  - `test_confirm_moves_all_items_to_custody_and_cancel_only_in_preparado`
  - `test_custody_listing_with_days_out_and_summary`
- Suite previa: `pytest tests/test_compras_plugin.py -q` → 11 passed intacta.
- Migración: `psql ... "\\d com_dispatch_cylinders"` tras habilitar plugin.
- Frontend: `npx tsc --noEmit` limpio; suite vitest sin fallos nuevos vs
  baseline; manual: crear despacho → confirmar → tile de custodia del
  proveedor lista los seriales con días fuera.

## ROLLBACK

Reversible: revertir commits; migración con `downgrade` que elimina ambas
tablas (solo contienen estado comercial propio, sin efectos externos).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/migrations/003_dispatches.py
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/backend/schemas/dispatches.py
    - plugins/commerce/purchase/backend/schemas/__init__.py
    - plugins/commerce/purchase/backend/services/dispatches.py
    - plugins/commerce/purchase/backend/routers/dispatches.py
    - plugins/commerce/purchase/backend/routers/__init__.py
    - plugins/commerce/purchase/frontend/**
    - apps/api/tests/test_compras_dispatch.py
  prohibited:
    - plugins/logistics/**          # lg_cylinders: solo lectura vía models
    - plugins/stock/**
    - vendor/**
    - plugins/commerce/purchase/backend/services/orders.py
    - plugins/commerce/purchase/backend/services/receipts.py
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.dispatches
    - compras.custody
  indirect:
    - compras.frontend.proveedores # tile de custodia deja de ser placeholder
  must_not_affect:
    - logistics (cilindros, jornadas, movimientos)
    - stock ledger
    - órdenes/recepciones existentes
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002 # ciclo de vida de orden (order_id opcional del despacho)
    - COMPRAS-003 # estructura routers/schemas por dominio
    - COMPRAS-004 # tile placeholder de custodia a reemplazar
  must_compose_with:
    - COMPRAS-006 # recepción parcial conciliada por serial marcará DEVUELTO
  systemic_invariants:
    - "Un serial EN_CUSTODIA es visible exactamente desde un proveedor."
    - "Ningún cilindro desaparece de trazabilidad durante una compra (§45)."
  composition_checks:
    - Tras 006: devolver un serial lo quita de custody listing y queda
      historizado con returned_at y recepción de origen.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: despachos es un dominio más del plugin compras, mismo corte
    routers/services/schemas que suppliers/orders/receipts
  extraction_trigger: si requiere escribir en Logistics o crecer fuera del
    vínculo comercial, se extrae a sub-módulo propio hablando REST
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - services/dispatches.py # validaciones de serial, custodia, transiciones
```

## Traceability

- Requirement: plan aprobado por usuario ("esta excelente") tras diseño de
  custodia derivada, frontera logística read-only y subdominio dentro de
  compras; VISION §8-12, §32, §40, §42.
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
