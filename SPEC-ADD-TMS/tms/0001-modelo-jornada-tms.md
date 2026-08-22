# A.SPEC TMS-001 — Persistir borrador de jornada TMS en OSS

## WHY
El sistema necesita guardar localmente la jornada materializada desde una salida a cliente legacy, para que un operador la revise/edite antes de confirmarla, sin depender de llamar al API legacy en cada consulta.

## WHAT
Existe una tabla `tms_jornada` en OSS que almacena el borrador de jornada (vehículo, chofer, cliente, dirección, ítems, estado) derivado de `cod_movimiento_legacy`.

## SCOPE
- Modelo `JornadaTMS` en `plugins/tms/backend/models.py`.
- Migración `001_initial_jornada.py` que crea `tms_jornada`.
- `cod_movimiento_legacy` único (idempotencia de sync).

## OUT OF SCOPE
- Lógica de sync (TMS-002).
- Tarea periódica (TMS-003).
- Endpoint de edición (TMS-004).
- Promoción a `LogisticsVehicleSession` (fuera de MVP).

## CONTRACT
- Postcondición: `tms_jornada` existe tras `migrate_plugins tms`.
- `cod_movimiento_legacy` UNIQUE INDEX.
- Campos de borrador son planos y editables (no derivados).

## INVARIANTS
```yaml
invariants:
  - "cod_movimiento_legacy es único en tms_jornada"
  - "estado ∈ {draft, pendiente, confirmed}"
  - "la migración es idempotente (checkfirst=True)"
```

## VERIFICATION
- `ruff check plugins/tms/backend/models.py plugins/tms/backend/migrations/001_initial_jornada.py` → sin errores.
- Import: `from plugins.tms.backend.models import JornadaTMS` OK.
- Tras migrar: `SELECT COUNT(*) FROM tms_jornada` devuelve 0 filas (tabla creada).

## ROLLBACK
- `downgrade(db)` hace `Base.metadata.drop_all` de `tms_jornada`. Reversible.

## Change Surface
```yaml
change_surface:
  allowed:
    - "crear plugins/tms/backend/models.py"
    - "crear plugins/tms/backend/migrations/001_initial_jornada.py"
  prohibited:
    - "modificar tablas de otros plugins"
    - "tocar systutor.core.database.Base más allá de importar"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "nueva tabla tms_jornada en la BD del plugin TMS"
  indirect:
    - "registro de migración del plugin TMS"
  must_not_affect:
    - "tablas de logistics/crm/stock/productos"
    - "runtime de otros plugins"
```

## Composition
```yaml
composition:
  requires_aspecs: []
  must_compose_with:
    - "TMS-002 (el sync usa este modelo)"
  systemic_invariants: []
  composition_checks:
    - "sync_salidas_hoy puede upsert sobre tms_jornada"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/models.py"
```

## Traceability
- Requirement: jornada borrador persistida en OSS
- Commit: pendiente
- Deployment: rama TMS

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
- [x] Traceability established
