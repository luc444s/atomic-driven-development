# Changelog 2026-07-21 - Espanolizacion formal de Jornadas

## Que se implemento

Se unifico la terminologia visible del frontend de `Jornadas` para eliminar labels en ingles y codigos crudos en las vistas operativas.

## Cambios principales

1. `Stop Result` pasa a mostrarse como `Resultado de parada`.
2. Los estados y codigos internos de ruta, incidencias, carta porte y seriales ahora se traducen antes de renderizarse.
3. Se ajustaron textos mixtos como `Outcome`, `Workspace` y referencias de estado en los dialogs y cards del flujo.

## Alcance

- `plugins/logistics/frontend/components/vehicle-sessions/jornada-labels.ts`
- `plugins/logistics/frontend/components/vehicle-sessions/RouteStopResultsPanel.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/OperationalSummaryDetailDialog.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/OperationalSummaryInline.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionRouteTab.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/RouteOperationsCard.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/RouteStopProgressCard.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/RouteIncidentsPanel.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionWaybillCard.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/LoadSerialsDialog.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionLoadTab.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/RouteOperationForm.tsx`

## Notas

- El cambio se limito al frontend visible al operador; no se alteraron contratos de API ni nombres internos persistidos.
