# A.SPEC STOCK-001 — Reactivar UI de stock en OSS (acoplada)

## WHY

El commit `225e445` desregistró la UI de stock del host ("Legacy es dueño del
stock; OSS no materializa balances"). El usuario revierte esa decisión: **stock
sigue acoplado a OSS**. La regla "legacy dueño" aplica solo cuando el módulo
TMS esté activo, no en general.

## WHAT

Se restaura `plugins/stock/frontend/register.ts` al contenido previo al
desregistro: rutas de stock (balance, ajuste, transferencia, configuración,
detalle) y la entrada de navegación "Stock" en el sidebar.

Verdad nueva falsable ahora: el sidebar muestra el módulo Stock y sus páginas
cargan (Balance, Ajuste, Transferencia, Configuración, Detalle).

## SCOPE

- `plugins/stock/frontend/register.ts` (restaurar registro UI).

## OUT OF SCOPE

- Cambios en la lógica de stock (sigue igual; sólo UI host).
- TMS (la regla legacy-dueño queda condicionada a TMS activo, sin cambios acá).

## CONTRACT

Precondiciones:
- `register.ts` actual con `navigation: []` y `routes: []`.

Postcondiciones:
- `register.ts` registra 6 rutas de stock y 1 entrada de navegación "Stock".
- Sidebar muestra Stock; rutas `/stock*` cargan sus páginas.

## INVARIANTS

```yaml
invariants:
  - permisos stock.* intactos (routing usa requiredPermissions existentes)
  - componentes/paginas de stock sin modificaciones
  - otros plugins sin cambios
  - backend/API de stock sin cambios
```

## VERIFICATION

```bash
grep -n "navigation\|routes" plugins/stock/frontend/register.ts  # navegacion Stock presente
# manual: sidebar muestra Stock; /stock carga StockBalancePage
```

## ROLLBACK

Reversible: reaplicar el desregistro (git checkout de `225e445` sobre el
archivo).

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/stock/frontend/register.ts
  prohibited:
    - vendor/**
    - plugins/stock/backend/**
    - plugins/tms/**, plugins/logistics/**, plugins/crm/**, plugins/productos/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - sidebar (vuelve Stock) y rutas /stock
  indirect:
    - permisos stock.* ahora visibles en UI
  must_not_affect:
    - lógica de balances en backend
    - write-back TMS
```

## Composition

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants:
    - "legacy dueño de stock" queda condicionado a TMS activo (regla del usuario)
  composition_checks: []
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - plugins/stock/frontend/register.ts
```

## Traceability

- Requirement: "stock sigue acoplado a OSS; legacy-dueño solo con TMS activo"
- Commit: STOCK-001 (restaura register.ts de stock)
- Deployment: main

- Commit: `89d533b`

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