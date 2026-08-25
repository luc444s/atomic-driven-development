# A.SPEC LOGI-0018 — Visibility of customer address in cylinder traceability

## WHY

LOGI-0017 hace que el sistema *sepa* en qué dirección de cliente quedó un
cilindro, pero esa información no es visible para el operador. El operador debe
poder ver la dirección donde quedó/retiró el cilindro tanto en la confirmación
de la operación de ruta como en el resumen de cilindros en cliente.

## WHAT

Solo lectura (read-side). Se expone `customer_address_id` + etiqueta legible de
la dirección en dos superficies:

1. Confirmación/resultado de operación de ruta (envío y recogida).
2. Resumen de cilindros en cliente (`get_customer_cylinder_summary` /
   `list_cylinders_at_customers`).

Es una sola verdad observable: el operador ve la dirección de cliente donde está
el cilindro, sin pasos extra.

## SCOPE

Backend (read):

- `plugins/logistics/backend/services/cylinders.py`
  (`list_cylinders_at_customers`): añade `customer_address_id` y label de
  dirección a cada dict.
- `plugins/logistics/backend/services/customer_cylinder_summary.py`
  (`get_customer_cylinder_summary`): añade `customer_address_id` + label,
  resolviendo vía join a `crm_customer_addresses` (evitar N+1).
- `plugins/logistics/backend/customer_cylinder_summary_schemas.py`: nuevo campo
  en el schema de lectura.

Frontend (render):

- `plugins/logistics/frontend/api/customer-cylinder-summary.ts`: tipo incluye
  `customer_address_id` + `address_label`.
- `plugins/logistics/frontend/components/vehicle-sessions/RouteOperationForm.tsx`:
  mostrar dirección en el resultado de la operación confirmada.
- Componente que renderiza el resumen de cilindros en cliente (confirmar durante
  implementación; candidatos: `cylinders/components/CylinderSummaryCards.tsx`,
  `components/LogisticsSummaryWidget.tsx` o la vista que consume
  `api/customer-cylinder-summary.ts`): mostrar `address_label`.

## OUT OF SCOPE

- Captura/escritura de `customer_address_id` (LOGI-0017).
- Selección manual de dirección por el operador.
- Cambios en CRM o en la resolución de ubicación.

## CONTRACT

- Postcondición: ambas superficies muestran la dirección del cliente cuando el
  evento trazable tiene `customer_address_id` poblado.
- Si `customer_address_id` es `NULL`, se muestra `"—"` o
  `"sin dirección específica"` (sin romper el render existente).

## INVARIANTS

```yaml
invariants:
  - Sin escrituras: esta A.SPEC no modifica lg_cylinder_events ni genera eventos.
  - Campos existentes del resumen (customer_id, estados, conteos) DEBEN quedar idénticos.
  - Rendimiento: el resumen NO debe introducir N+1 (join o batch lookup de direcciones).
  - UI existente de operación de ruta y resumen NO debe perder información previa.
```

## VERIFICATION

- Test `test_logistics_customer_cylinder_summary.py`: tras entrega a dirección
  `A`, `get_customer_cylinder_summary` devuelve `customer_address_id == A` y
  `address_label` no vacío para ese cilindro.
- Test/frontend: `RouteOperationForm` muestra `address_label` tras confirmar
  operación de entrega con `delivery_point.address_id`.
- e2e: flujo envío y flujo recogida listan la dirección correcta en sus
  respectivas vistas.

## ROLLBACK

- Quitar el campo del schema y del render; seguro (solo lectura). Sin efecto
  irreversible.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/logistics/backend/services/cylinders.py
    - plugins/logistics/backend/services/customer_cylinder_summary.py
    - plugins/logistics/backend/customer_cylinder_summary_schemas.py
    - plugins/logistics/frontend/api/customer-cylinder-summary.ts
    - plugins/logistics/frontend/components/vehicle-sessions/RouteOperationForm.tsx
    - plugins/logistics/frontend/components/cylinders/components/CylinderSummaryCards.tsx
    - plugins/logistics/frontend/components/LogisticsSummaryWidget.tsx
  prohibited:
    - plugins/logistics/backend/services/route_operation_confirmation.py
    - plugins/crm/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - customer cylinder summary payload
    - route operation confirmation view
  indirect:
    - cualquier UI que consuma customer_cylinder_summary
  must_not_affect:
    - event recording
    - cylinder state transitions
    - crm
```

## Composition

```yaml
composition:
  requires_aspecs:
    - LOGI-0017
  must_compose_with: []
  systemic_invariants:
    - visibilidad es degradable: NULL address no rompe UI
  composition_checks:
    - con LOGI-0017 integrado, resumen y confirmación de ruta muestran dirección
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - customer_cylinder_summary.py (join de dirección)
```

## Traceability

- Requirement: refinación trazabilidad cilindro por dirección de cliente (opción A)
- Commit: pendiente (sin commit aún; agregar hash al integrar)
- Deployment: pendiente (backend + frontend)

- Commit: `cdc2291`

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now
- [x] Invariants preserved
- [x] Verification passed
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established (commit pendiente)
