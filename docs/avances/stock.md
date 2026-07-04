# Avance: Módulo Stock

## Propósito

Documentar el estado real del plugin `stock`, qué partes de SPEC 0016 ya quedaron implementadas, qué decisiones de implementación se cerraron en código y qué gaps siguen dependiendo del core o de validación posterior.

Este documento debe leerse antes de extender `plugins/stock/`.

> **Estado: Cerrado** — El plugin está completo para su integración con otros módulos via eventos, auditoría, y endpoints documentados. No se requiere desarrollo adicional en stock salvo la integración operativa con ventas/logistics cuando esos módulos existan.

---

## 1. Estado actual

### Identidad

| Propiedad | Valor |
|---|---|
| Plugin ID | `stock` |
| Estado | **Cerrado** — listo para integración con otros plugins |
| ADR principal | `docs/adr/0016-stock-plugin.md` |
| Spec principal | `docs/specs/core/0016-stock-plugin/index.md` |
| Dependencias | `logistics`, `productos` |

### Implementado en esta iteración

- manifest `plugin.json` completo y válido para runtime persistente;
- backend con modelos `stk_ledger`, `stk_balance`, `stk_config`;
- FKs reales a `prod_products` y `lg_warehouses`;
- migración inicial `001_initial_stock.py`;
- endpoints de balance, ledger, ajuste, transferencia y configuración;
- **endpoint de ledger global (`GET /ledger`)** para consultar movimientos entre productos;
- auditoría y eventos para ajustes y transferencias;
- idempotencia por `reference_id` / `idempotency_key`;
- frontend inicial con página de balances y modales;
- **página de lista de configuraciones (`StockConfigPage`)** en `/stock/configs`;
- prueba de integración backend del flujo principal;
- **22 tests de integración** cubriendo flujos principales, validación de errores, idempotencia, scope y búsqueda;
- soporte real de claims contextuales `warehouse_id` en core;
- `lg_warehouses.branch_id` y derivación de branch operativo desde almacén;
- enforcement de scope por almacén en endpoints de `stock`;
- compilación frontend validada.
- `permissions/` y `events/` tienen `__init__.py` (consistente con `productos`).
- **5 tests de concurrencia sobre PostgreSQL real** validando `SELECT FOR UPDATE` con 10/20 threads concurrentes, lost update detection, mixed-sign adjustments y transfers.

---

## 2. Decisiones cerradas en código

### 2.1 FKs reales, no lógicas

- `stock` ya quedó implementado con FKs reales hacia `prod_products` y `lg_warehouses`;
- no se dejó en modo MVP ni en modo “referencia blanda”.

### 2.2 Sin import interno entre plugins en backend

- `stock` valida productos y almacenes con query directa a la misma BD;
- no importa servicios internos de `productos` ni `logistics`.

### 2.3 Frontend sin acoplarse a componentes internos de `productos`

- se creó `apps/web/src/components/ProductSearchDialog.tsx` como componente compartido;
- `stock` no depende de `plugins/productos/frontend/components/*`.

### 2.4 Runtime persistente alineado

- `stock` usa `backend_entrypoint: backend.plugin:register`;
- `stock` usa `frontend_entrypoint: frontend/register.ts`;
- durante esta implementación también se corrigió el mismatch de manifest en:
  - `plugins/productos/plugin.json` → `frontend/register.tsx`
  - `plugins/crm/plugin.json` → `frontend/register.tsx`

### 2.5 Claims contextuales resueltos en core

- el core ya resuelve `tenant_id` y `branch_id`;
- ahora también resuelve claims contextuales `warehouse_id` desde `user_context_claims`;
- `TenantContext` expone `current_warehouse_ids` cuando existen restricciones;
- ausencia de claims de almacén significa acceso no restringido por warehouse dentro del tenant;
- `stock` consume ese alcance; no implementa un sistema propio de claims.

### 2.6 Branch operativo derivado del almacén

- `lg_warehouses` ahora tiene `branch_id`;
- al crear un almacén sin branch explícito, logistics usa por defecto el `branch_id` del usuario autenticado;
- `stock` usa el branch del almacén en auditoría/eventos;
- en transferencias, el `event_log.branch_id` se resuelve desde el almacén origen y el payload incluye `from_branch_id` y `to_branch_id`.

---

## 3. Cobertura actual de la SPEC 0016

### Implementado

- balance por producto+almacén;
- ledger histórico;
- ajuste manual;
- transferencia entre almacenes;
- configuración de mínimos/máximos;
- invalidación por stock negativo;
- eventos:
  - `stock.balance.adjusted`
  - `stock.transfer.completed`
- auditoría:
  - `balance.adjust`
  - `transfer.create`
  - `config.manage`
- idempotencia de ajuste y transferencia;
- locking pesimista con `SELECT ... FOR UPDATE` en el servicio.
- claim `warehouse_id` resuelto desde core y aplicado en `stock`.
- catálogo de almacenes filtrado por scope desde `stock`.
- branch derivado del almacén en eventos de ajuste y transferencia.

### Implementado parcialmente

- fallback routes frontend: existen para detalle, ajuste, transferencia y config, pero la UX principal sigue siendo modal desde la página de balances.

---

## 4. Archivos clave

### Backend

- `apps/api/app/kernel/tenants/models.py`
- `apps/api/app/kernel/tenants/service.py`
- `apps/api/app/kernel/tenants/context.py`
- `apps/api/app/kernel/auth/service.py`
- `apps/api/app/api/v1/core/users.py`
- `apps/api/app/api/v1/core/services/users.py`
- `plugins/stock/backend/plugin.py`
- `plugins/stock/backend/common.py`
- `plugins/stock/backend/models.py`
- `plugins/stock/backend/schemas.py`
- `plugins/stock/backend/router.py`
- `plugins/stock/backend/services/balances.py`
- `plugins/stock/backend/services/catalog.py`
- `plugins/stock/backend/services/operations.py`
- `plugins/stock/migrations/001_initial_stock.py`

### Frontend

- `plugins/stock/frontend/register.ts`
- `plugins/stock/frontend/api.ts`
- `plugins/stock/frontend/types.ts`
- `plugins/stock/frontend/pages/StockBalancePage.tsx`
- `plugins/stock/frontend/pages/StockConfigPage.tsx`
- `plugins/stock/frontend/components/ModalAjusteStock.tsx`
- `plugins/stock/frontend/components/ModalTransferenciaStock.tsx`
- `plugins/stock/frontend/components/ModalConfigStock.tsx`
- `plugins/stock/frontend/components/ModalDetalleStock.tsx`
- `apps/web/src/components/ProductSearchDialog.tsx`
- `plugins/logistics/frontend/pages/WarehousesPage.tsx` (sigue usable; branch se infiere por backend si no se envía)

### Tests

- `apps/api/tests/test_core_management_apis.py`
- `apps/api/tests/test_logistics_plugin.py`
- `apps/api/tests/test_stock_plugin.py` (23 tests SQLite)
- `apps/api/tests/test_stock_concurrency_postgres.py` (5 tests PostgreSQL, con `SYSTUTOR_PG_TEST=1`)

---

## 5. Validaciones ejecutadas

- `ruff check apps/api/app/kernel/tenants apps/api/app/kernel/auth apps/api/app/api/v1/core apps/api/tests/test_core_management_apis.py apps/api/tests/test_stock_plugin.py plugins/logistics/backend plugins/logistics/migrations/007_warehouse_branch.py plugins/stock`
- `.venv/bin/pyright apps/api/app/kernel/tenants apps/api/app/kernel/auth apps/api/app/api/v1/core apps/api/tests/test_core_management_apis.py apps/api/tests/test_stock_plugin.py plugins/logistics/backend plugins/stock`
- `pytest apps/api/tests/test_core_management_apis.py apps/api/tests/test_logistics_plugin.py apps/api/tests/test_stock_plugin.py`
- `npm run build`

Estado al cierre de esta iteración:

- Ruff: OK
- Pyright: OK
- Pytest core/logistics/stock: OK
- Build frontend: OK

---

## 6. Riesgos y siguientes pasos

### Riesgos abiertos

- el modelo de claims contextuales existe, pero hoy solo se usa para `warehouse_id`; si aparecen más claims, habrá que decidir si el API de administración se generaliza o sigue por caso de uso.

### Siguiente trabajo recomendado

1. ~~agregar pruebas adicionales de concurrencia real sobre PostgreSQL~~ → `test_stock_concurrency_postgres.py` (5 tests, ejecutar con `SYSTUTOR_PG_TEST=1`);
2. ~~agregar endpoint de ledger global~~ → `GET /ledger` implementado;
3. ~~agregar vista frontend de lista de configuraciones~~ → `StockConfigPage` en `/stock/configs`;
4. cuando existan integraciones operativas con ventas/logistics, emitir o consumir eventos de stock desde esos módulos sin dual-write;
5. widget de dashboard "Low stock alerts" para el shell principal.
