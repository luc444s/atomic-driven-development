# Changelog 2026-07-21 - Cantidad obligatoria en carga operativa

## Que se implemento

Se reforzo la regla de `Carga operativa` para que una linea que sale desde almacen no pueda guardarse ni confirmar la jornada con cantidad vacia, cero o invalida.

## Comportamiento

1. en frontend, `SessionLoadTab` bloquea `Guardar plan` / `Guardar y confirmar` si existe una linea desde almacen sin cantidad valida;
2. la UI muestra un alerta explicita de `Cantidad obligatoria`;
3. en backend, `load_plans` vuelve a validar la misma regla al guardar y al confirmar la carga para evitar bypass por API o datos inconsistentes.

## Alcance

- `plugins/logistics/frontend/components/vehicle-sessions/SessionLoadTab.tsx`
- `plugins/logistics/backend/dto/load_plans.py`
- `plugins/logistics/backend/services/load_plans.py`
- `apps/api/tests/test_logistics_vehicle_sessions_v1.py`

## Nota

- Esta regla complementa la obligatoriedad ya existente de seriales para productos serializados: ahora la carga queda incompleta tanto si faltan seriales como si falta una cantidad valida en una linea que sale desde almacen.
