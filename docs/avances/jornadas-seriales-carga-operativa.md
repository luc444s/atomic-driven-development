# Avance: Jornadas - seriales en carga operativa

## Qué se agregó

- Soporte backend para asignar seriales de envases a una jornada antes de confirmar la carga.
- Flujo `scanner-first` en `Carga Operativa` para capturar seriales por línea de producto.
- Bloqueo de confirmación de carga cuando faltan seriales obligatorios en productos serializados.
- Confirmación de seriales enlazada a la operación real de carga (`confirmed_by_operation_id`).
- Liberación de seriales con causa (`MANUAL`, `TIMEOUT`, `OPERATION_CANCELLED`).
- Transición real del cilindro:
  - `SELECTED` no cambia el estado real del envase;
  - al confirmar carga pasa a `CARGA_EN_VEHICULO`;
  - al salir la jornada pasa a `EN_RUTA`.

## Backend agregado

- Modelo: `lg_load_serial_assignments`
- Migración: `029_load_serial_assignments_v1.py`
- DTOs: `dto/load_serials.py`
- Servicio: `services/load_serials.py`
- Router: `routers/load_serials.py`

## Endpoints nuevos

- `GET /api/v1/plugins/logistics/vehicle-sessions/{session_id}/load-serials/selected?product_id=...`
- `PUT /api/v1/plugins/logistics/vehicle-sessions/{session_id}/load-serials/select`
- `PUT /api/v1/plugins/logistics/vehicle-sessions/{session_id}/load-serials/{assignment_id}/release`

## Frontend agregado

- API client: `frontend/api/load-serials.ts`
- Modal de captura: `LoadSerialsDialog.tsx`
- Integración en `SessionLoadTab.tsx`
- Conteo por línea de carga: seriales seleccionados / seriales requeridos
- Fallback manual con `Combobox` compartido del core para búsqueda puntual por serial

## Reglas fuertes implementadas

- Un mismo cilindro no puede quedar activo en dos jornadas a la vez.
- Para productos serializados, sin seriales completos no se puede confirmar la carga.
- La disponibilidad del cilindro se resuelve en backend.
- El flujo principal está pensado para scanner físico o celular como terminal de captura.

## Qué no hace todavía

- No integra aún cámara móvil nativa; por ahora el flujo usa input compatible con scanner y tipeo manual.
- No enriquece todavía `Carta Porte v2`; solo prepara seriales confirmados para ese siguiente slice.
