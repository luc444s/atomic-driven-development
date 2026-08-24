# A.SPEC COMPRAS-003 — División estructural de router y schemas del módulo compras

> A.SPEC estructural (ADD §12). No agrega comportamiento observable nuevo:
> introduce una propiedad estructural nueva — archivos con una sola razón de
> cambio — antes de que las features COMPRAS-004+ agranden los god-files.

## WHY

Tras COMPRAS-002, `router.py` tiene 569 líneas mezclando tres dominios
(suppliers, orders, receipts) más helpers de serialización y construcción del
conector de stock; `schemas.py` tiene 235 líneas con 22 clases de tres dominios
distintos. ADD §12.2 los pone en zona de revisión (>400) y §12.4 exige
extracción antes de agregar más responsabilidades. Las features próximas
(despacho por serial, custodia) crecerían `orders` aún más sobre el god-file.

Los servicios ya están divididos (`services/{suppliers,orders,addressses,receipts}.py`);
la división de routers/schemas sigue ese mismo corte de dominio.

## WHAT

Verdad estructural falsable ahora:

```text
backend/
├── routers/
│   ├── __init__.py     # arma el APIRouter agregando sub-routers
│   ├── common.py       # DB_SESSION, TENANT_CONTEXT, deps REQUIRE_*,
│   │                   # _build_stock_connector()
│   ├── suppliers.py    # CRUD proveedor + addresses/contacts/bank-accounts
│   ├── orders.py       # órdenes: list/get/create/update/confirm/cancel/
│   │                   # close + serializers + list_tanks
│   └── receipts.py     # POST /orders/{id}/receive
└── schemas/
    ├── __init__.py     # re-exporta todos los modelos (compatibilidad)
    ├── suppliers.py    # Supplier*, Supplier{Address,Contact,BankAccount}*
    └── orders.py       # Purchase*, Receive*, CancelOrderRequest,
                        # CloseOrderRequest
```

- `backend/router.py` se reduce a entrypoint (ADD §12.3): importa `routers`,
  monta los sub-routers bajo el prefijo `/purchase` y exporta `router`.
  El import en `plugin.py` NO cambia.
- `backend/schemas.py` desaparece como archivo y pasa a paquete; todo import
  `from plugins.commerce.purchase.backend.schemas import X` sigue funcionando
  vía re-export en `__init__.py`.

## SCOPE

- Nuevo paquete `plugins/commerce/purchase/backend/routers/` (5 archivos).
- Nuevo paquete `plugins/commerce/purchase/backend/schemas/` (3 archivos).
- Eliminación de `backend/router.py` monolítico (reemplazado por agregador fino)
  y de `backend/schemas.py` monolítico.

## OUT OF SCOPE

- Cambios de comportamiento, endpoints nuevos o firmas distintas.
- Migraciones de DB.
- Frontend.
- Servicios (`services/*`) ya divididos — solo se ajustan imports si hiciera falta.

## CONTRACT

Precondiciones:

- COMPRAS-002 integrada; suite `test_compras_plugin.py` en verde (11 tests).

Postcondiciones:

- Ningún archivo del backend de compras supera las 400 líneas.
- Cada router de dominio declara únicamente sus rutas y sus dependencias.
- Los imports públicos existentes siguen resolviendo:
  - `from plugins.commerce.purchase.backend.router import router`
  - `from plugins.commerce.purchase.backend.schemas import <cualquiera>`
- Rutas HTTP idénticas (mismos paths, métodos, response_model, permisos).

## INVARIANTS

```yaml
invariants:
  - Cero cambios de contrato HTTP: la suite completa pasa sin modificar tests.
  - Multi-tenant y permisos por ruta quedan exactamente igual.
  - La máquina de estados sigue viviendo SOLO en services/orders.py (COMPRAS-002).
  - plugin.py no cambia (entrypoint del plugin intacto).
```

## VERIFICATION

- `wc -l plugins/commerce/purchase/backend/routers/*.py
  plugins/commerce/purchase/backend/schemas/*.py` — todos < 400.
- `cd apps/api && python -m pytest tests/test_compras_plugin.py -q`
  → 11 passed (cero modificaciones al archivo de tests).
- Import-check explícito:
  `python -c "from plugins.commerce.purchase.backend.schemas import CloseOrderRequest;
  from plugins.commerce.purchase.backend.router import router"` sin error.
- Runtime: habilitar plugin compras y `GET /purchase/orders` responde igual.

## ROLLBACK

Reversible: revertir commit(s). Es refactor movimiento-de-código; cualquier
regresión se detecta con la suite existente. Sin efectos sobre datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - plugins/commerce/purchase/backend/routers/**
    - plugins/commerce/purchase/backend/schemas/**
    - plugins/commerce/purchase/backend/router.py   # queda agregador fino
    - plugins/commerce/purchase/backend/schemas.py  # eliminado
  prohibited:
    - plugins/commerce/purchase/backend/services/**
    - plugins/commerce/purchase/backend/models.py
    - plugins/commerce/purchase/frontend/**
    - apps/api/tests/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - compras.http_layer.structure
  indirect:
    - compras.routes.all
  must_not_affect:
    - services layer behavior
    - stock connector contract
    - logistics / stock / crm plugins
```

## Composition

```yaml
composition:
  requires_aspecs:
    - COMPRAS-002
  must_compose_with:
    - COMPRAS-004 # despacho por serial crecerá routers/orders.py ya dividido
  systemic_invariants:
    - El backend de compras mantiene un corte por dominio coherente
      (routers ↔ services ↔ models).
  composition_checks:
    - Tras COMPRAS-004, ningún archivo nuevo supera 400 líneas.
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: un router por dominio comercial; schemas espejan el mismo corte
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - backend/routers/<dominio>.py
    - backend/schemas/<dominio>.py
```

## Traceability

- Requirement: instrucción del usuario — "cuidado con el schema inferno y el
  route giant, desde ahora conviene dividir" (tras COMPRAS-002).
- ADD doctrine: SPECIFICATION.md §12 (ley estructural), §12.4 (trigger extracción).
- Commit: pendiente.

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
