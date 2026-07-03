# SPEC 0020 - Logistics: Cierre operativo de planificacion

## Estado

Propuesta

## Contexto

La `SPEC 0014.1` deja claro que planificacion en `logistics` ya no es un hueco funcional, sino una capacidad base con varios parciales de cierre operativo.

Hoy el modulo ya cubre:

- calculo de stock disponible desde `stock`;
- planificacion por modo `all`, `full` y `partial`;
- generacion y aceptacion de precargas;
- filtrado por `warehouse_id`;
- persistencia auditada del flujo principal.

Lo que falta no es ownership de stock ni de producto. Lo que falta es cerrar la experiencia operativa que en el legacy estaba repartida entre varios forms y ramas especificas:

1. aceptacion de precarga con seguimiento claro del traslado generado;
2. agenda del repartidor como consumidor operativo desde planificacion;
3. rama ADR de planificacion;
4. planificacion por grupo de producto;
5. grilla con validacion mas rica y feedback operativo mas claro.

`productos` es el catalogo maestro futuro y debe ser consumido como lectura para `prod_products`, `prod_groups` y configuracion ADR de producto. `logistics` no debe recuperar ownership de catalogos ni volver a duplicar la logica de producto.

## Objetivo

Cerrar los cinco parciales de planificacion sobre la implementacion actual de `logistics` sin alterar ownerships ya definidos por ADR.

## No objetivos

- no crear un plugin nuevo;
- no mover stock real fuera de `stock`;
- no duplicar catalogos maestros dentro de `logistics`;
- no reescribir la pagina de planificacion completa;
- no agregar filtros avanzados o paginacion nueva que no resuelvan estos cinco parciales;
- no introducir una segunda fuente de verdad para ADR o grupos de productos.

## Alcance

### 1. Aceptacion de precarga y traslado generado

El flujo de precarga debe quedar como una operacion visible y clara, no solo como una accion tecnica.

Incluye:

1. confirmar la aceptacion de una precarga pendiente desde la UI;
2. mostrar el resultado generado, incluyendo el movimiento de traslado creado;
3. refrescar stock disponible, pedidos pendientes y precargas luego de aceptar;
4. bloquear la aceptacion si la precarga no esta en estado `PENDIENTE`;
5. conservar el comportamiento idempotente y auditado ya existente;
6. evitar que la UI muestre el flujo como si modificara stock real.

### 2. Agenda del repartidor desde planificacion

La planificacion debe exponer un punto operativo para revisar y preparar agenda del repartidor sin apropiarse de la persistencia de agenda.

Incluye:

1. consumo de resumen diario de agenda;
2. acceso a tareas por repartidor y ruta usando los endpoints existentes de `agenda` y `routes`;
3. accion visible para preparar o revisar agenda desde el contexto de planificacion;
4. sincronizacion del contexto seleccionado de almacen, ruta o repartidor cuando aplique;
5. reutilizacion de los permisos y claims existentes, sin crear ownership nuevo.

### 3. Rama ADR de planificacion

La planificacion debe poder operar con una rama especifica para cargas o rutas con restricciones ADR.

Incluye:

1. mostrar puntos ADR del movimiento o conjunto planificado;
2. mostrar vehiculos elegibles para el contexto ADR;
3. mostrar incompatibilidades activas que afecten la seleccion;
4. consumir configuracion ADR de producto como dato maestro de lectura desde `productos` cuando este disponible, sin copiarla como fuente nueva en `logistics`;
5. bloquear o advertir cuando el vehiculo elegido no sea compatible con la carga ADR.

### 4. Planificacion por grupo de producto

La vista de planificacion debe poder agrupar el resumen por grupo de producto cuando el caso operativo lo requiera.

Incluye:

1. agrupar stock y cobertura usando `prod_groups` y `prod_products.group_id` como lectura;
2. mantener la planificacion real a nivel de producto, sin cambiar la llave transaccional;
3. permitir visualizar la cobertura por grupo sin crear una tabla duplicada en `logistics`;
4. conservar el comportamiento actual por producto como modo por defecto;
5. respetar la coexistencia con el estado actual de `productos`.

### 5. Grilla con validacion mas rica

La grilla de planificacion debe ayudar a decidir antes de confirmar, no solo listar datos.

Incluye:

1. validacion por fila de solicitado, planificado, pendiente y disponible;
2. feedback visual de cobertura consistente con el sistema visual del proyecto;
3. advertencias claras para `permit_without_stock`;
4. informacion visible para stock, grupo y ADR cuando aplique;
5. bloqueo de guardado si falta contexto obligatorio como almacen o producto seleccionado;
6. mantener la UI sin colores hardcodeados y con componentes compartidos.

## Reglas de negocio

1. `StockDisponible = stk_balance.quantity - StockComprometido - StockPlanificado`.
2. `StockComprometido` y `StockPlanificado` siguen viviendo en `logistics` y se derivan por query.
3. `CantPlanificada` no puede exceder `CantPendiente` salvo `permit_without_stock`.
4. Una precarga activa por fecha y almacen sigue siendo la regla.
5. Aceptar precarga sigue generando traslado y no modifica stock real.
6. La rama ADR debe respetar eligibilidad de vehiculo e incompatibilidades activas.
7. La agrupacion por grupo es una vista operativa; no cambia la semantica transaccional de `product_id`.
8. Todo el alcance sigue siendo tenant-aware y warehouse-scoped.

## Permisos

No se crean permisos nuevos en esta iteracion.

La implementacion debe reutilizar los permisos existentes del flujo de orden, agenda, ruta, vehiculo y ADR, ademas de los claims vigentes por `tenant_id`, `branch_id` y `warehouse_id`.

## Eventos

No se agregan eventos nuevos obligatorios para cerrar estos cinco parciales.

Se preservan los eventos ya existentes del flujo de planificacion, en especial:

- `logistics.planning.preload_generated`;
- `logistics.planning.preload_accepted`.

Las acciones de agenda y ADR deben seguir usando la auditabilidad y eventos de sus subdominios existentes si ya aplican.

## Datos

### Lecturas existentes

- `lg_orders`
- `lg_order_items`
- `lg_plan_preloads`
- `lg_plan_preload_items`
- `lg_movements`
- `lg_vehicles`
- `lg_routes`
- `lg_route_stops`
- `lg_agenda_tasks`
- `lg_adr_product_config`
- `lg_adr_incompatibilities`
- `prod_products`
- `prod_groups`
- `stk_balance`

### Contratos de lectura esperados

- resumen de stock por producto;
- resumen de stock por grupo;
- detalle de precarga con movimiento generado;
- resumen diario de agenda;
- resumen ADR con vehiculos elegibles.

## Migraciones

No se requieren migraciones nuevas de base de datos para esta spec, salvo que la implementacion descubra una necesidad tecnica concreta y aislada que no pueda resolverse con los modelos y contratos actuales.

## Auditoria y observabilidad

1. toda aceptacion de precarga debe quedar auditada con `preload_id` y `movement_id`;
2. toda seleccion de agenda desde planificacion debe quedar trazable por usuario y almacen;
3. toda decision ADR relevante debe dejar rastreo operativo;
4. la UI debe mostrar errores operativos claros y no ocultar fallas de validacion;
5. el flujo no debe introducir logica escondida fuera de servicios y endpoints ya auditablemente definidos.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Mezclar planificacion con agenda y rutas sin frontera clara | alto | usar planificacion solo como consumidor operativo de agenda/rutas |
| Depender de catalogos de producto aun no estabilizados | medio | consumir `productos` como lectura y no como ownership local |
| Agrupar por grupo y perder precision de producto | medio | mantener `product_id` como clave transaccional y `group_id` solo como vista |
| Hacer de ADR una pantalla paralela en vez de una rama de planificacion | medio | integrar ADR como rama operativa del mismo workspace |
| Sobrecargar la grilla con demasiada informacion | medio | limitar la validacion a lo que cambia la decision de planificar |

## Criterios de aceptacion

### Funcionales

1. una precarga pendiente puede aceptarse desde la UI y deja visible el movimiento generado;
2. luego de aceptar una precarga, se refrescan stock, pedidos y precargas;
3. la planificacion muestra un punto operativo para agenda del repartidor sin duplicar persistencia;
4. la rama ADR muestra vehiculos elegibles e incompatibilidades antes de confirmar;
5. la vista puede agrupar cobertura por grupo de producto sin cambiar la transaccion por producto;
6. la grilla informa pendiente, disponible, cobertura y advertencias antes de confirmar.

### De ownership

1. `stock` sigue siendo la fuente de stock real;
2. `productos` sigue siendo la fuente maestra de producto y grupo;
3. `logistics` sigue siendo dueño de la planificacion operativa;
4. no se crean tablas duplicadas para grupos, agenda o ADR.

### De calidad

1. el frontend mantiene colores semanticos, no hardcodes visuales;
2. se reutilizan componentes compartidos cuando aplique;
3. los cambios quedan cubiertos por pruebas sobre la logica nueva o refactorizada;
4. la experiencia sigue funcionando dentro del scope de `warehouse_id`.

## Pruebas requeridas

1. unitarias para helpers de agrupacion, cobertura y validacion;
2. unitarias para la decision de aceptacion de precarga;
3. integracion para los endpoints de planificacion ya existentes que soportan el flujo;
4. integracion para ADR y agenda en el contexto de planificacion si se tocan sus consumidores;
5. verificacion frontend del modal o panel que muestre estas cinco ramas operativas.

## Notas para agentes

1. No copiar logica de producto, stock o agenda dentro de planificacion si ya existe un owner claro.
2. No introducir colores hardcodeados ni componentes visuales paralelos.
3. No convertir la spec en una reescritura de toda `PlanningPage`; el alcance son solo estos cinco parciales.
4. Leer antes `docs/adr/0013-logistics-submodulos-pendientes.md`, `docs/adr/0015-productos-plugin.md`, `docs/adr/0016-1-stock-claims-y-branch-derivado.md`, `docs/avances/logistics.md` y `docs/avances/productos.md`.
5. Si aparece una necesidad nueva fuera de estos cinco parciales, debe salir a otra spec.

## Dependencias

- ADR 0003 - Modelo tenancy y permisos
- ADR 0004 - Runtime de plugins
- ADR 0005 - Event bus y auditoria
- ADR 0008 - Testing y calidad
- ADR 0009 - Spec driven development
- ADR 0010 - Logistics como plugin piloto
- ADR 0013 - Modulos pendientes de Logistics como submodulos
- ADR 0015 - Productos plugin: Catalogo maestro
- ADR 0016.1 - Stock: Claims por warehouse y branch derivado de almacen
- `docs/avances/logistics.md`
- `docs/avances/productos.md`
- `docs/specs/core/0014-1-logistics-gap-closure.md`
- `plugins/logistics/backend/services/planning.py`
- `plugins/logistics/frontend/pages/PlanningPage.tsx`
