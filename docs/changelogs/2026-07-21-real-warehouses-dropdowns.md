# Changelog 2026-07-21 - Dropdowns de almacenes solo con almacenes reales

## Cambio

Se consolidó el patrón de frontend para que los dropdowns de almacenes usen solo almacenes reales/fijos y excluyan almacenes móviles (`warehouse_type = MOBILE`).

## Patrón reusable

- Archivo: `plugins/logistics/frontend/api/warehouses.ts`
- Helpers agregados:
  - `isRealWarehouse()`
  - `getRealWarehouses()`

## Aplicado en

- `plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/CreateVehicleFromJornadaDialog.tsx`
- `plugins/logistics/frontend/pages/VehiclesPage.tsx`
- `plugins/logistics/frontend/pages/ReceptionPage.tsx`
- `plugins/logistics/frontend/pages/OrdersPage.tsx`
- `plugins/logistics/frontend/pages/MovementsPage.tsx`
- `plugins/logistics/frontend/pages/PlanningPage.tsx`
- `plugins/logistics/frontend/contracts/dialogs/contract-form-dialog.tsx`
- `plugins/logistics/frontend/LogisticsPage.tsx`

## Intención

- evitar que los usuarios elijan almacenes móviles en dropdowns donde se espera un almacén real/base/origen/destino administrativo;
- mantener los almacenes móviles solo como parte del contexto operativo derivado de la jornada, no como opción normal de selección en formularios generales.
