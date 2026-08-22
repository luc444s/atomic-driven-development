# A.SPEC TMS-005 — Materializar última orden en jornada útil y testeable (TEST FINAL MVP)

## WHY
El MVP TMS se considera validado solo si, dada la última salida/orden a cliente legacy, OSS produce una jornada útil, persistida y verificable, incluyendo el vehículo cuando la salida lo trae.

## WHAT
Existe un test (unitario + integración) que toma la última salida legacy, la materializa en `JornadaTMS` borrador, y — si la salida trae `placa`+`dnichofer` — materializa el vehículo dentro de la jornada.

## SCOPE
- `materialize_salida` sobre la última salida (ej. 42470: `RAM/BEI-793 | 78839842 | 2026-08-20`, cliente M.H. EIRL, pesito 2).
- Upsert en `tms_jornada` vía `sync_salidas_hoy` (mock de `LegacyApiClient`).
- Materialización de vehículo (placa, chofer) linkeado a la jornada cuando aplique.
- `PATCH` de edición sobre la jornada resultante.

## OUT OF SCOPE
- Promoción a `LogisticsVehicleSession` real del core logistics.
- Sincronización de salidas históricas.

## CONTRACT
- `materialize_salida(salida)` es pura y testeable sin red.
- La jornada persistida tiene `estado=draft`, `placa`, `chofer_dni` y `items` correctos.
- Si `placa`+`dnichofer` presentes → existe vehículo linkeado a la jornada.
- Idempotencia: 2 corridas de sync → 1 fila.

## INVARIANTS
```yaml
invariants:
  - "la última salida se materializa en exactamente 1 jornada borrador"
  - "el vehículo se crea/linkea solo si la salida trae placa+chofer"
  - "sync idempotente: 2 corridas = 1 fila"
```

## VERIFICATION
- Unit: `materialize_salida(salida_42470)` → `jornada_key='RAM/BEI-793|78839842|2026-08-20'`, operación `CUSTOMER_DELIVERY`, pesito 2.
- Integración SQLite: `sync_salidas_hoy` con `LegacyApiClient` mock (42470) → `tms_jornada` 1 fila `estado=draft`, `placa='RAM/BEI-793'`, `chofer_dni='78839842'`, `items` pesito 2.
- Vehículo: assert existe vehículo `RAM/BEI-793` linkeado a la jornada.
- Edición: `PATCH` cambia `placa` y `pendiente`→`draft`.
- Idempotencia: 2 corridas → 1 fila.
- Todo corre en `pytest` CI.

## ROLLBACK
- Los borradores son datos locales; borrar filas revierte. El test no muta legacy.

## INVARIANTS ( composición )
```yaml
composition:
  requires_aspecs:
    - "TMS-001"
    - "TMS-002"
    - "TMS-003"
    - "TMS-004"
  must_compose_with: []
  systemic_invariants: []
  composition_checks:
    - "pipeline completo: sync -> materialize -> upsert -> patch sobre la última salida"
```

## Change Surface
```yaml
change_surface:
  allowed:
    - "crear tests en apps/api/tests/test_tms_*.py"
    - "usar modelos y servicios de TMS-001..004"
  prohibited:
    - "modificar el API legacy para este test"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "filas de prueba en tms_jornada (SQLite en test)"
  indirect:
    - "ninguno en prod"
  must_not_affect:
    - "legacy"
    - "otros plugins"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "apps/api/tests/"
```

## Traceability
- Requirement: MVP TMS validado end-to-end
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
