# A.SPEC TMS-003 — Disparar sync de salidas cada 5 minutos

## WHY
Los borradores de jornada deben mantenerse al día con legacy sin intervención manual y sin acoplar el sync a un request HTTP.

## WHAT
Existe una tarea periódica que ejecuta `sync_salidas_hoy()` cada 5 minutos, desacoplada del request.

## SCOPE
- Actor Dramatiq periódico (5 min) en `plugins/tms/backend/services/sync.py`, o comando + cron de SO.
- Manejo de fallos del API legacy (no crashea el worker).

## OUT OF SCOPE
- La lógica de sync (TMS-002).
- Reintentos con backoff personalizado (fuera de MVP).

## CONTRACT
- La tarea corre cada 5 min mientras el plugin TMS esté habilitado.
- Ante `LegacyAuthError`/`LegacyTimeoutError`: loggear y retornar sin excepción.

## INVARIANTS
```yaml
invariants:
  - "la tarea no lanza excepción no controlada que mate el worker"
  - "el intervalo es 5 min, no bajo demanda"
```

## VERIFICATION
- Correr el actor manualmente → crea borradores en `tms_jornada`.
- Con el API legacy caído (token malo) → la tarea termina sin error visible en worker.

## ROLLBACK
- Desregistrar el actor / deshabilitar plugin detiene la tarea. Reversible.

## Change Surface
```yaml
change_surface:
  allowed:
    - "registrar actor en plugins/tms/backend/services/sync.py"
    - "configurar beat/cron"
  prohibited:
    - "acoplar sync a un endpoint HTTP"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "ejecuciones periódicas de red al API legacy"
  indirect:
    - "carga de red cada 5 min"
  must_not_affect:
    - "disponibilidad de otros plugins"
```

## Composition
```yaml
composition:
  requires_aspecs:
    - "TMS-002"
  must_compose_with:
    - "TMS-005 (el test final valida el pipeline completo)"
  systemic_invariants: []
  composition_checks:
    - "tras N corridas, tms_jornada contiene las salidas del día sin duplicados"
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
- Requirement: sync desacoplado cada 5 min
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
