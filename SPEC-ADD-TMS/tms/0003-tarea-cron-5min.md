# A.SPEC TMS-003 — Disparar sync de salidas cada 5 minutos

## WHY
Los borradores de jornada deben mantenerse al día con legacy sin intervención manual y sin acoplar el sync a un request HTTP.

## WHAT
Existe un daemon OSS (`python -m plugins.tms.backend.commands.run_sync_daemon`) que ejecuta
`sync_salidas_hoy()` cada 5 minutos, desacoplado del request, en segundo plano permanente
(`nohup setsid` + log en `logs/tms_sync_daemon.log`).

> Nota de diseño: se eligió un daemon loop propio en lugar de actor Dramatiq periódico porque
> Dramatiq 1.18 (el exigido por el core, `<2.0`) NO incluye `PeriodicMiddleware`/`periodic`
> (llegó en 2.x). El actor `@dramatiq.actor(periodic=...)` fallaba al registrarse con
> "undefined options: periodic".

## SCOPE
- `run_scheduler()` en `plugins/tms/backend/services/cron.py` (loop 5 min + try/except).
- Comando `plugins/tms/backend/commands/run_sync_daemon.py`.
- Manejo de fallos del API legacy (no crashea el daemon: `logger.exception` + sigue).

## OUT OF SCOPE
- La lógica de sync (TMS-002).
- Reintentos con backoff personalizado (fuera de MVP).

## CONTRACT
- La tarea corre cada 5 min mientras el daemon esté vivo.
- Ante `LegacyAuthError`/`LegacyTimeoutError`: loggear y continuar sin salir del loop.

## INVARIANTS
```yaml
invariants:
  - "el daemon no muere por excepciones: try/except en cada corrida"
  - "el intervalo es 5 min, no bajo demanda"
```

## VERIFICATION
- Correr `python -m plugins.tms.backend.commands.run_sync_daemon` → corrida inicial contra
  API legacy real y log en `logs/tms_sync_daemon.log`.
- Con el API legacy caído (token malo) → el daemon loggea y continúa (no sale del loop).

## ROLLBACK
- Detener el proceso daemon (kill) detiene la tarea. Reversible; no afecta BD ni legacy.

## Change Surface
```yaml
change_surface:
  allowed:
    - "crear plugins/tms/backend/services/cron.py (run_scheduler)"
    - "crear plugins/tms/backend/commands/run_sync_daemon.py"
  prohibited:
    - "acoplar sync a un endpoint HTTP"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "ejecuciones periódicas de red al API legacy cada 5 min"
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

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (daemon corriendo, corrida real contra API legacy)
- [x] Invariants preserved
- [x] Verification passed (daemon lanzado; log `logs/tms_sync_daemon.log`)
- [x] Rollback / compensation honest (kill del proceso detiene)
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established
