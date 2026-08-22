# A.SPEC STOCK-OPT-001 — Evitar barrido masivo de balances en cada listado

## WHY

`list_balances` ejecuta `_ensure_catalog_balances` en **cada request** a
`/stock`. Esa función barre todos los productos × todos los almacenes del
tenant, carga todos los pares de balance existentes y hace commit. Con
catálogo grande el listado de stock demora (diagnóstico: recomputación
innecesaria en cada request).

La materialización de productos nuevos ya está cubierta por el evento
`product.created` → `ensure_balances_for_product` (event_handlers.py:19). El
barrido masivo solo es necesario la primera vez que un tenant tiene balances
(o cuando aparece un almacén nuevo sin pares).

## WHAT

Se agrega una guarda de estado estable al inicio de `_ensure_catalog_balances`:

- Consulta barata `SELECT id FROM stock_balance WHERE tenant = :t LIMIT 1`.
- Si no hay ningún balance → comportamiento actual (materializar todo).
- Si hay balances pero los almacenes solicitados **no** están todos cubiertos
  en balances → comportamiento actual (cubre almacén nuevo).
- Si hay balances y los almacenes solicitados ya están cubiertos → **return**
  sin leer el catálogo completo ni commitear.

Verdad nueva falsable ahora: en estado estable (tenant con balances y
almacenes ya cubiertos), un request a `/stock` ya no ejecuta el barrido
productos×almacenes ni el commit; solo 2 consultas ligeras.

## SCOPE

- `plugins/stock/backend/services/balances.py` → `_ensure_catalog_balances`.

## OUT OF SCOPE

- Índices adicionales sobre stock_balance (candidato de segunda slice:
  `(tenant_id, warehouse_id, product_id)`).
- Caching.
- Otros listados.

## CONTRACT

Precondiciones:
- `_ensure_catalog_balances` corre en cada `list_balances`.

Postcondiciones:
- Estado estable: sin barrido catálogo×almacenes ni commit por request.
- Materialización inicial y de almacenes nuevos intactas.
- Comportamiento observable del listado idéntico.

## INVARIANTS

```yaml
invariants:
  - todo producto del catalogo sin balance se materializa en 0 (regla de negocio intacta)
  - almacen nuevo sin pares se materializa al listarse
  - permisos/filtros de tenant intactos
  - no se cambia la query principal de listado
```

## VERIFICATION

```bash
# struct: guarda presente sin romper flujo existente
grep -n "LIMIT 1\|covered_warehouse" plugins/stock/backend/services/balances.py
# typecheck del backend
.venv/bin/python -c "import compileall,sys; sys.exit(0 if compileall.compile_file('plugins/stock/backend/services/balances.py', quiet=1) else 1)"
# manual (si hay datos): abrir /stock en estado estable y comparar tiempo vs antes
```

## ROLLBACK

Reversible: revertir la guarda (git checkout del archivo). Sin datos en juego.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/stock/backend/services/balances.py
  prohibited:
    - vendor/**
    - apps/**
    - plugins/stock/frontend/**
    - esquema DB
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - listado /stock (tiempo de respuesta)
  indirect:
    - materialización lazy de balances (solo inicial / almacenes nuevos)
  must_not_affect:
    - reglas de negocio de balances
    - otros listados
```

## Composition

```yaml
composition:
  requires_aspecs:
    - STOCK-001 (UI de stock acoplada a OSS, vuelve a usarse)
  must_compose_with: []
  systemic_invariants:
    - materialización de producto nuevo via evento product.created sigue activa
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
    - plugins/stock/backend/services/balances.py
```

## Traceability

- Requirement: "stock demora; evitar barrido masivo de balances por request"
- Commit: STOCK-OPT-001 (guarda estado estable en _ensure_catalog_balances)
- Deployment: main (backend)

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