# A.SPEC TMS-002 — Sincronizar salidas del día a borradores de jornada

## WHY
Las salidas a cliente se registran en legacy; OSS necesita reflejarlas como borradores de jornada para que el operador las confirme, pero solo las del día (no el histórico de 11.348 salidas).

## WHAT
Existe un servicio `sync_salidas_hoy()` que, cada ejecución, trae las salidas del día desde legacy, las materializa y crea/actualiza `JornadaTMS` como `draft` o `pendiente`, idempotentemente.

## SCOPE
- `get_salidas(desde=inicio_día, hasta=ahora)`.
- `materialize_salida()` (pura, ya existe).
- Upsert por `cod_movimiento_legacy`.
- Resolución de `direccion_llegada` vía `/clientes/{cod_cliente}` cuando `LugarDestino` vacío.

## OUT OF SCOPE
- Programación cada 5 min (TMS-003).
- Edición por API (TMS-004).
- Promoción a `LogisticsVehicleSession`.

## CONTRACT
- Regla "suficiente info": `placa` Y `dnichofer` presentes → `estado=draft`; falta alguno → `estado=pendiente`.
- No sincroniza salidas de días anteriores (filtro `desde` = inicio del día).
- Idempotente: múltiples corridas no duplican filas.

## INVARIANTS
```yaml
invariants:
  - "solo salidas con fecha >= inicio del día local se sincronizan"
  - "cod_movimiento_legacy ya existente no crea fila nueva"
  - "borrador confirmado no es sobrescrito por sync"
```

## VERIFICATION
- Test puro: `materialize_salida(salida_con_placa)` → draft; `salida_sin_placa` → pendiente.
- Test integración SQLite: upsert mismo `cod_movimiento_legacy` 2 veces → 1 fila.
- Test integración: salida 42470 (mock) → `tms_jornada` 1 fila `estado=draft`, `placa='RAM/BEI-793'`.

## ROLLBACK
- El servicio solo escribe borradores; borrar filas de `tms_jornada` revierte. No afecta legacy.

## Change Surface
```yaml
change_surface:
  allowed:
    - "crear plugins/tms/backend/services/sync.py"
    - "usar LegacyApiClient.get_salidas y materialize_salida"
  prohibited:
    - "escribir en BD legacy"
    - "modificar el API legacy"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "inserciones/updates en tms_jornada"
  indirect:
    - "llamadas de red al API legacy cada corrida"
  must_not_affect:
    - "estado de salidas en legacy"
    - "otros plugins"
```

## Composition
```yaml
composition:
  requires_aspecs:
    - "TMS-001"
  must_compose_with:
    - "TMS-003 (la tarea dispara este servicio)"
    - "TMS-005 (test final lo valida)"
  systemic_invariants: []
  composition_checks:
    - "sync_salidas_hoy produce exactamente las jornadas del día"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/services/sync.py"
```

## Traceability
- Requirement: reflejar salidas del día como borradores
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
