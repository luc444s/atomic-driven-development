# A.SPEC [TMS-011] — Seriales de la salida como metadato nominal en el plan

> Verdicto speccer: ACCEPT_ONE. Verdad independiente falsable: cada item de la salida legacy
> trae sus seriales de envase (`LogEscaneo.Serie`) y el load plan los conserva como metadato
> nominal — sin crear `LogisticsCylinder` ni assignments.

## WHY

En legacy, al grabar la salida se registran los seriales de los envases que salen
(`LogEscaneo`: `CodMovimiento`, `Serie`, `ProductoId`). TMS-010 arma la carga sin seriales. Para
que la jornada viva conserve qué envases físicos salieron (fiel a legacy) pero SIN materializar
maestros de cilindros en esta rama, los seriales se transportan por el API y se guardan como
**metadato nominal** dentro del plan de carga.

## WHAT

- El API legacy `GET /salidas/{id}` expone `seriales: ["<Serie>", ...]` por item (JOIN
  `LogEscaneo` por `CodMovimiento` + `ProductoId`).
- OSS `SalidaItemLegacy.seriales: list[str]` (default `[]`), propagado por el materialize.
- El sync conserva los seriales como metadato en el item del load plan (JSON en `notes`), sin
  crear cilindros ni asignaciones.

## SCOPE

- Exponer `seriales` por item en `/salidas/{id}` (VB `SalidasHandler.vb`).
- `SalidaItemLegacy.seriales`.
- Propagación hasta el metadato del item del plan (TMS-010).

## OUT OF SCOPE

- Crear `LogisticsCylinder`.
- `select_load_serial` / `LogisticsLoadSerialAssignment`.
- Validar estado del cilindro.
- Waybill / guía de remisión.

## CONTRACT

- Postcondición: para una salida con items que tienen seriales en `LogEscaneo`, cada item del
  load plan conserva su lista de seriales como metadato; `lg_cylinders` y
  `lg_load_serial_assignments` quedan en 0 para esta salida.
- Precondición: existe el plan de carga de la sesión (TMS-010) y el API expone seriales.
- Salida sin seriales → `seriales=[]`, metadato vacío, sin error.

## INVARIANTS

```yaml
invariants:
  - "seriales son solo metadato: no crean cilindro ni assignment"
  - "no cambia el estado de cilindros (no existen en esta rama)"
  - "items sin seriales no rompen el plan"
  - "idempotente: re-sync mantiene los mismos seriales en el metadato"
```

## VERIFICATION

- Test OSS: salida con items + `seriales` → item del plan tiene metadato JSON con los seriales;
  `lg_cylinders` 0 y `lg_load_serial_assignments` 0.
- Test sin seriales → `seriales=[]` y metadato vacío.
- E2E real: `GET /salidas/{id}` de una salida con escaneos → `seriales` presente; verificar
  metadato del plan y cilindros 0.

## ROLLBACK

- Reversible: quitar el campo `seriales` del API/schema deja el metadato vacío; no hay filas de
  cilindros que limpiar.

## Change Surface

```yaml
change_surface:
  allowed:
    - "editar SalidasHandler.vb (VB, Win10) para exponer seriales"
    - "editar plugins/tms/backend/legacy/schemas.py"
    - "editar plugins/tms/backend/services/materialize.py"
    - "editar plugins/tms/backend/services/sync.py (metadato en plan item)"
  prohibited:
    - "crear cilindros ni assignments"
    - "tocar stock_bridge"
    - "confirmar/avanzar sesión"
    - "generar waybill"
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - "respuesta JSON de /salidas/{id} (nuevo campo seriales)"
    - "metadato en items de lg_load_plan_items"
  indirect:
    - "el plan muestra qué envases físicos salieron"
  must_not_affect:
    - "lg_cylinders / assignments"
    - "stock OSS y legacy"
    - "resto del contrato /salidas/{id}"
```

## Composition

```yaml
composition:
  requires_aspecs:
    - "TMS-010 (plan de carga DRAFT)"
    - "API legacy /salidas/{id} expone seriales"
  must_compose_with: []
  systemic_invariants: []
  composition_checks:
    - "con seriales expuestos, la salida re-materializada conserva metadato sin duplicar"
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/backend/legacy/schemas.py"
    - "plugins/tms/backend/services/sync.py"
```

## Traceability

- Requirement: seriales de la salida visibles en la jornada viva (nominales)
- Commit: pendiente
- Deployment: rama TMS + API legacy Win10

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