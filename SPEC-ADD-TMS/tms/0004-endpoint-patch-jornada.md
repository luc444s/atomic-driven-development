# A.SPEC TMS-004 — Editar borrador de jornada vía PATCH

## WHY
El borrador debe ser fácilmente modificable por el operador (corregir placa, chofer, dirección, ítems) antes de confirmarlo.

## WHAT
Existe `PATCH /api/tms/jornadas/{id}` que actualiza campos editables de un borrador y transiciona `pendiente`→`draft` al completar placa+chofer.

## SCOPE
- Endpoint `PATCH /api/tms/jornadas/{id}`.
- Campos editables: `placa`, `chofer_dni`, `direccion_llegada`, `observacion`, `items`, `tipo_transaccion`.
- Permiso `tms.jornada.edit` (registrar en `plugin.py`).

## OUT OF SCOPE
- Confirmar/promover a `LogisticsVehicleSession` (fuera de MVP).
- Edición de salidas ya `confirmed`.

## CONTRACT
- Solo editable si `estado` ∈ {`draft`, `pendiente`}; si `confirmed` → 409.
- Al editar `placa`+`dnichofer` en jornada `pendiente` → `estado=draft`.
- Actualiza solo campos enviados; refresca `updated_at`.

## INVARIANTS
```yaml
invariants:
  - "jornada confirmed no es editable (409)"
  - "PATCH no cambia cod_movimiento_legacy ni fecha"
  - "items se validan (cod_producto entero >=0, pesito/cantidad numéricos)"
```

## VERIFICATION
- Test: PATCH `placa` en jornada pendiente → `estado` pasa a `draft`.
- Test: PATCH sobre jornada `confirmed` → 409.
- Test: PATCH solo `observacion` → otros campos intactos.

## ROLLBACK
- El PATCH es sobre borrador; revertir consiste en otro PATCH. Sin efectos irreversibles.

## Change Surface
```yaml
change_surface:
  allowed:
    - "crear router PATCH en plugins/tms/backend"
    - "registrar permiso tms.jornada.edit en plugin.py"
  prohibited:
    - "editar salidas confirmed"
    - "escribir en BD legacy"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "updates en tms_jornada"
  indirect:
    - "nuevo permiso en el sistema de permisos"
  must_not_affect:
    - "tabla tms_jornada de otros tenants"
    - "estado de legacy"
```

## Composition
```yaml
composition:
  requires_aspecs:
    - "TMS-001"
  must_compose_with:
    - "TMS-005 (el test final incluye edición)"
  systemic_invariants: []
  composition_checks:
    - "PATCH sobre jornada del test final es idempotente y auditable"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/routers/jornadas.py"
```

## Traceability
- Requirement: borrador editable
- Commit: pendiente
- Deployment: rama TMS

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
