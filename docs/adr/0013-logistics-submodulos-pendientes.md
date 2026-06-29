# ADR 0013 — Módulos Pendientes de Logistics como Submódulos

## Estado

Aceptado

## Contexto

El plugin `logistics` (v0.3.0) implementa el núcleo operativo de logística pero tiene **15 módulos pendientes** para alcanzar paridad funcional con el legacy (`modulo_logistica/`). Estos módulos fueron identificados en el análisis documentado en `docs/avances/logistics.md` y especificados en `docs/specs/core/0014-logistics-complete/`.

Los módulos pendientes son:

1. Planificación
2. Recepción
3. Carta Porte
4. Reportes
5. Guía de Despacho
6. Equipos por Movimiento
7. Restricciones Vehículo-Ruta
8. Parámetros de Repartidor
9. Vinculación Vehículo-Cliente
10. Resumen Diario de Agenda
11. Schedule Semanal de Rutas
12. Validación de Peso en Carga
13. Módulo ADR Completo
14. GPS Tracking
15. Peso y Contenido de Cilindro

Cada uno de estos módulos opera sobre las tablas existentes de `logistics` (`lg_orders`, `lg_movements`, `lg_cylinders`, `lg_routes`, `lg_agenda_tasks`, etc.) o requiere tablas nuevas que referencian directamente a las existentes.

## Decisión

Los 15 módulos se implementarán como **submódulos dentro del plugin `logistics`**, no como plugins independientes.

### Arquitectura

Cada submódulo seguirá el patrón existente:

```
plugins/logistics/backend/services/
├── planning.py          # Módulo 1
├── reception.py         # Módulo 2
├── waybill.py           # Módulo 3
├── reports.py           # Módulo 4
├── dispatch.py          # Módulo 5
├── equipment.py         # Módulo 6
├── vehicle_restrictions.py  # Módulo 7
├── driver_params.py     # Módulo 8
├── vehicle_clients.py   # Módulo 9
├── agenda_summary.py    # Módulo 10
├── route_schedule.py    # Módulo 11
├── load_validation.py   # Módulo 12
├── adr.py               # Módulo 13
├── gps_tracking.py      # Módulo 14
└── cylinder_weight.py   # Módulo 15
```

Los endpoints se agregarán al router existente (`router.py`) con el mismo sistema de permisos.

### Alternativas consideradas

1. **Plugins independientes** — Crear un plugin por módulo (ej. `planning`, `reception`, `waybill`).
   - Rechazado por: alto acoplamiento de datos (todos operan sobre `lg_*`), riesgo de dependencias circulares, duplicación de modelos.

2. **Módulo monolítico externo** — Crear una app separada fuera del sistema de plugins.
   - Rechazado por: perdería la integración con el plugin runtime (eventos, permisos, auditoría, multi-tenancy).

3. **División en 2-3 plugins** — Agrupar por afinidad (ej. planning+reception, ADR+waybill, reportes).
   - Rechazado por: los límites son difusos y seguirían compartiendo tablas. No hay ganancia real.

### Consecuencias

**Positivas:**

- Cohesión: toda la logística en un solo plugin con un modelo de datos unificado.
- Simplicidad: un solo punto de entrada, un solo conjunto de migraciones.
- Rendimiento: sin llamadas entre plugins para operaciones que cruzan submódulos.
- Consistencia: mismo patrón de servicios, mismos helpers de auditoría/eventos.

**Negativas:**

- El plugin `logistics` crecerá en tamaño (~12 servicios → ~27 servicios).
- Mayor responsabilidad en un solo plugin (riesgo de acoplamiento interno).
- Las miguciones se acumulan en un solo directorio.

**Mitigaciones:**

- Cada submódulo se implementa en un archivo separado con responsabilidad clara.
- Los endpoints se agrupan por prefijo en el router.
- Las migraciones se mantienen ordenadas por revisión.
- Si un submódulo crece lo suficiente (ej. ADR), se evalúa extraerlo a plugin propio en el futuro.

## Referencias

- SPEC 0014: `docs/specs/core/0014-logistics-complete/index.md`
- Avance del módulo: `docs/avances/logistics.md`
- ADR 0010: Logistics como plugin piloto
- ADR 0004: Runtime de plugins
