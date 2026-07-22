# Changelog 2026-07-22 - Autoagregado numérico en Seriales

## Qué se implementó

Se agregó autoagregado en `Seriales` cuando el usuario escribe un código numérico completo que coincide de forma única con el final del serial.

## Comportamiento

1. el usuario escribe un código numérico;
2. si la búsqueda devuelve una única coincidencia `AVAILABLE` cuyo serial termina exactamente en ese bloque numérico;
3. el sistema lo agrega automáticamente a `Seriales seleccionados` sin requerir Enter ni click en `Agregar`.

## Alcance

- `plugins/logistics/backend/services/load_serials.py`
- `plugins/logistics/frontend/components/vehicle-sessions/LoadSerialsDialog.tsx`
- `apps/api/tests/test_logistics_vehicle_sessions_v1.py`

## Nota

- Si el código es ambiguo o no es una coincidencia única segura, el flujo sigue siendo manual.
