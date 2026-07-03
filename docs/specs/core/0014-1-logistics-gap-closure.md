# SPEC 0014.1 — Logistics: Cierre de Gaps sobre Implementación Existente

## Estado

Propuesta

## Contexto

La `SPEC 0014` define 15 bloques necesarios para cerrar la brecha funcional entre `plugins/logistics/` y el legacy.

Sin embargo, después de revisar el código real del plugin, esa spec no debe leerse como si todo el trabajo estuviera simplemente pendiente ni como si todo estuviera completamente cerrado.

El estado real es mixto:

- hay bloques ya implementados de punta a punta en backend y frontend;
- hay bloques con backend funcional pero sin pantalla operativa dedicada;
- hay bloques presentes como endpoints o servicios base, pero todavía sin cierre completo de UX, pruebas o criterios de aceptación.

Esta `SPEC 0014.1` no reemplaza a la `0014`.

La complementa para corregir dos problemas de lectura:

1. evitar sobreafirmar que un bloque está "hecho" solo porque existe código;
2. separar implementación existente de gaps reales de cierre.

---

## Objetivo

Definir el plan de cierre real sobre la implementación actual de `logistics`, distinguiendo con precisión:

- qué bloques de la `0014` ya tienen implementación sustancial;
- qué bloques siguen parciales;
- qué falta para considerar cada bloque operativamente cerrado.

---

## No objetivos

- reescribir la `SPEC 0014` desde cero;
- invalidar implementaciones ya existentes que sí aportan valor;
- introducir arquitectura nueva fuera de ADRs aceptados;
- tratar ausencia de UI como ausencia total de implementación cuando el backend sí existe.

---

## Matriz base de estado

### Convención

- **Implementado**: existe backend funcional y consumo operativo suficiente en frontend, aunque puedan quedar pruebas o mejoras menores.
- **Parcial**: existe implementación relevante, pero no alcanza aún cierre operativo completo.
- **Pendiente**: no existe implementación sustancial suficiente para el bloque.

### Estado actual de los 15 bloques

| Bloque | Estado 14.1 | Evidencia principal | Gap real de cierre |
|---|---|---|---|
| 1. Planificación | Implementado | `services/planning.py`, endpoints `/planning/*`, `frontend/pages/PlanningPage.tsx` | Validación final de criterios y casos borde |
| 2. Recepción | Implementado | `services/reception.py`, endpoints `/reception/*`, `frontend/pages/ReceptionPage.tsx` | Validación final de idempotencia y casos borde |
| 3. Carta Porte | Implementado | `/waybill/*`, `services/documents.py`, visor en `MovementsPage.tsx` | Cierre documental y pruebas integrales |
| 4. Reportes | Parcial | `/reports/route-agenda/*`, `/reports/dispatch-ticket/*`, `/reports/transfer-albaran/*`, `/reports/load-summary/*`, `/reports/adr-summary/*` | Falta consumidor/UI operativo de reportes |
| 5. Guía de Despacho | Parcial | `/movements/{id}/close-dispatch`, `/dispatch-receipt`, `vehicle-return`, acciones en `MovementsPage.tsx` | Falta cierre de flujo como módulo explícito |
| 6. Equipos por Movimiento | Implementado | `services/extensions.py`, endpoints `/equipment` y `/movements/{id}/equipment`, `EquipmentPage.tsx` | Pruebas y endurecimiento menor |
| 7. Restricciones Vehículo-Ruta | Parcial | `/vehicles/{id}/route-restrictions`, `/routes/{id}/eligible-vehicles` | Falta UI de administración |
| 8. Parámetros de Repartidor | Parcial | `/drivers/{id}/parameters` | Falta UI de mantenimiento |
| 9. Vinculación Vehículo-Cliente | Parcial | `/vehicles/{id}/delivery-points` | Falta UI de gestión |
| 10. Resumen Diario de Agenda | Parcial | `/agenda/daily-summary` | Falta pantalla o consumidor específico |
| 11. Schedule Semanal de Rutas | Parcial | `/routes/{id}/weekly-schedule` | Falta UI de edición/visualización |
| 12. Validación de Peso en Carga | Parcial | `/loads/weight-summary`, validación en servicios de rutas/carga | Falta exposición operativa clara en frontend |
| 13. Módulo ADR Completo | Parcial | `/adr/product-config/*`, `/adr/points/*`, `/adr/incompatibilities/*`, `/adr/eligible-vehicles/*` | Falta UI y cierre funcional del flujo completo |
| 14. GPS Tracking | Parcial | `/routes/{id}/gps-start`, `/routes/{id}/stops/{stop_id}/gps`, `/agenda/tasks/{id}/gps` | Falta captura móvil/operativa real |
| 15. Peso y Contenido de Cilindro | Parcial | `/cylinders/available-with-weight`, `/cylinders/{id}/weight`, `/products/{id}/content` | Falta UI específica y consumo explícito |

---

## Decisiones de interpretación

### 1. "Implementado" no significa "spec cerrada formalmente"

En esta `0014.1`, un bloque puede figurar como `Implementado` aunque todavía queden:

- pruebas adicionales;
- documentación de cierre;
- endurecimiento de casos borde.

Lo que sí significa es que el bloque ya no debe tratarse como feature inexistente.

### 2. Backend existente cuenta como avance real

Si un bloque ya tiene:

- modelos;
- servicios;
- endpoints;
- permisos;

entonces no debe volver a clasificarse como "pendiente" solo por faltar pantalla dedicada.

### 3. La falta de UI sigue siendo gap válido

Cuando la spec exige uso operativo real por usuario final, un backend aislado no basta para considerar cierre completo.

Por eso varios bloques quedan `Parcial` en lugar de `Implementado`.

---

## Alcance de cierre por bloque parcial

### 4. Reportes

Falta:

- pantalla de consulta/consumo para reportes estructurados;
- validación del contrato de salida con usuarios operativos;
- decisión explícita sobre impresión/exportación fuera de la spec.

### 5. Guía de Despacho

Falta:

- consolidar el flujo como módulo operativo reconocible, no solo acciones dispersas en movimientos;
- validar correlativos, restricciones de modificación y recepción de despacho en escenarios reales.

### 7. Restricciones Vehículo-Ruta

Falta:

- UI para listar, editar y verificar restricciones desde frontend.

### 8. Parámetros de Repartidor

Falta:

- pantalla para editar parámetros por chofer;
- definición operativa mínima de qué parámetros son obligatorios.

### 9. Vinculación Vehículo-Cliente

Falta:

- flujo de administración desde frontend para vincular y desvincular puntos de entrega.

### 10. Resumen Diario de Agenda

Falta:

- vista dedicada que consuma `/agenda/daily-summary`.

### 11. Schedule Semanal de Rutas

Falta:

- editor visual de días por ruta;
- uso efectivo del schedule en planificación/selección de rutas si aún no está conectado de forma visible.

### 12. Validación de Peso en Carga

Falta:

- exponer al usuario el resultado del peso, límite y exceso antes de confirmar carga.

### 13. Módulo ADR Completo

Falta:

- pantalla de configuración ADR por producto;
- gestión de incompatibilidades;
- integración operativa visible con selección de vehículos.

### 14. GPS Tracking

Falta:

- integración real con frontend móvil o captura operativa de coordenadas;
- validación del flujo en ruta/parada/tarea.

### 15. Peso y Contenido de Cilindro

Falta:

- UI específica para consulta de peso/contenido;
- uso explícito dentro de operaciones donde ese dato sea relevante.

---

## Prioridad de cierre recomendada

### Alta

1. Guía de Despacho
2. Reportes
3. Módulo ADR Completo
4. Validación de Peso en Carga

### Media

1. Restricciones Vehículo-Ruta
2. Parámetros de Repartidor
3. Vinculación Vehículo-Cliente
4. Schedule Semanal de Rutas
5. GPS Tracking
6. Peso y Contenido de Cilindro

### Baja

1. Revalidación documental de bloques ya implementados

---

## Criterios de aceptación de esta 14.1

- existe una clasificación clara por bloque: `Implementado`, `Parcial` o `Pendiente`;
- la clasificación evita afirmar cierre total sin evidencia suficiente;
- los bloques ya implementados no vuelven a tratarse como trabajo inexistente;
- los gaps remanentes quedan expresados como trabajo concreto de cierre;
- `docs/avances/logistics.md` queda alineado con esta lectura.

---

## Referencias

- `docs/specs/core/0014-logistics-complete/index.md`
- `docs/avances/logistics.md`
- `plugins/logistics/backend/router.py`
- `plugins/logistics/backend/services/planning.py`
- `plugins/logistics/backend/services/reception.py`
- `plugins/logistics/backend/services/documents.py`
- `plugins/logistics/backend/services/extensions.py`
- `plugins/logistics/frontend/pages/PlanningPage.tsx`
- `plugins/logistics/frontend/pages/ReceptionPage.tsx`
- `plugins/logistics/frontend/pages/MovementsPage.tsx`
- `plugins/logistics/frontend/pages/EquipmentPage.tsx`
