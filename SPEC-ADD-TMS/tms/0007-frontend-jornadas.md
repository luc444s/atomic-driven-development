# A.SPEC TMS-007 — Pantalla "Jornadas" en frontend

## WHY
El backend ya materializa jornadas en `tms_jornada` y las expone vía `GET /tms/jornadas`, pero no hay UI que las muestre. El frontend TMS registra `routes: []` / `navigation: []` → la pantalla "Jornadas" anda vacía pese a que hay data.

## WHAT
Existe una pantalla "Jornadas" en la app web: lista los borradores en `DataTable` (badge de estado, filtro, paginación) y permite editar cada uno vía `Dialog` (PATCH). Se accede por menú lateral y ruta `tms/jornadas`.

## SCOPE
- `register.tsx`: route `tms/jornadas` + nav item, permiso `tms.jornada.read`.
- `api.ts` (TMS): `listJornadas`, `getJornada`, `patchJornada` + query keys.
- `JornadasListPage.tsx`: DataTable + filtro estado + paginación.
- `JornadaEditDialog.tsx`: Dialog con formulario (PATCH) siguiendo `frontend-ui-identity`.

## OUT OF SCOPE
- Confirmar/promover a `LogisticsVehicleSession`.
- Búsqueda por texto libre (solo filtro por estado).
- Detalle con mapa/vehículo (solo borrador editable).

## CONTRACT
- Ruta `tms/jornadas` requiere permiso `tms.jornada.read`.
- La tabla muestra: estado (badge), fecha, placa, chofer, cliente, tipo_transacción, observación, Acciones(Editar).
- Editar abre Dialog; PATCH exitoso actualiza la fila (invalida query).
- Errores del PATCH (404/409) se muestran con `<Alert title="Error">`.

## INVARIANTS
```yaml
invariants:
  - "labels usan block space-y-2 text-sm text-foreground"
  - "botones son <Button> de shared/ui/button"
  - "errores son <Alert>, no divs rojos"
  - "sin asteriscos rojos ni estilos inline"
```

## VERIFICATION
- Build de `apps/web` sin errores (tsc/vite).
- Al habilitar TMS + login con `tms.jornada.read`, el menú muestra "Jornadas" y la tabla lista las filas de `tms_jornada`.
- PATCH desde el Dialog refleja el cambio en la tabla (badge de estado).

## ROLLBACK
- Reversible: quitar la ruta/nav de `register.tsx` no borra data.

## Change Surface
```yaml
change_surface:
  allowed:
    - "editar plugins/tms/frontend/register.tsx"
    - "crear plugins/tms/frontend/api.ts"
    - "crear plugins/tms/frontend/pages/JornadasListPage.tsx"
    - "crear plugins/tms/frontend/components/JornadaEditDialog.tsx"
  prohibited:
    - "crear variantes de DataTable/Dialog (usar el core)"
    - "tocar app web shell fuera del registro del plugin"
```

## Blast Radius
```yaml
blast_radius:
  direct:
    - "registro de rutas/nav del plugin TMS en el shell"
  indirect:
    - "nuevo menú en la app web"
  must_not_affect:
    - "componentes del shell (DataTable, Dialog, Button)"
    - "otros plugins"
```

## Composition
```yaml
composition:
  requires_aspecs:
    - "TMS-006 (GET list/detail)"
  must_compose_with:
    - "frontend-ui-identity (patrones de la skill)"
  systemic_invariants: []
  composition_checks:
    - "la tabla muestra lo que GET /tms/jornadas devuelve"
    - "PATCH del Dialog coincide con el endpoint PATCH"
```

## Structural Constraints
```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - "plugins/tms/frontend/pages/JornadasListPage.tsx"
    - "plugins/tms/frontend/components/JornadaEditDialog.tsx"
```

## Traceability
- Requirement: exponer jornadas en la UI
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
