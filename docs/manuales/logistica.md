# Guía de uso — Módulo de Logística

**Público:** personal operativo (encargados de planta, planificadores, repartidores, almaceneros).
No requiere conocimientos técnicos ni de programación.

**Fuente:** este manual se escribió desde el comportamiento real de la aplicación, no desde diseños teóricos.

---

## ¿Qué es Logística?

Es el módulo donde se organiza el reparto de envases (garrafas/cilindros) y el vehículo como centro de operación.

Trabaja con dos ideas principales de arriba hacia abajo:

1. **El almacén** guarda el stock. Cada envase vive en un almacén o en un cliente.
2. **La jornada** es el viaje de un vehículo: se carga, sale a repartir, regresa y se concilia.

En el menú lateral, la sección **Logistics** agrupa las pantallas de uso diario.

---

## El menú del módulo

| Pantalla | Para qué sirve |
|---|---|
| **Jornadas** | El centro del reparto. Una jornada junta vehículo, ruta, carga, salida, retorno y conciliación. Es la pantalla más importante. |
| **Envases** | Registro y ficha técnica de cada cilindro/garrafa: estado, peso, marca, trazabilidad, mantenimiento. |
| **Almacenes** | Puntos de salida de la operación (planta, almacén de reparto). |
| **Contratos** | Condiciones comerciales de entrega/recolección de envases por cliente. |
| **Planificación** | Calendario de reservas de capacidad por vehículo (qué se espera cargar). |
| Entregas/Direcciones/Etc. | Pantallas de soporte para clientes, direcciones y operación auxiliar. |

Evita confundir **Jornadas** (lo que pasa hoy) con **Planificación** (lo que se reserva para adelante).

---

## 1. Almacenes

Almacén = punto desde donde sale el reparto.

Puedes ver y crear almacenes y zonas:

- **Crear almacén:** botón **Nuevo**, nombre, código (sigla corta) y dirección.
- **Asignar zona:** agrupa clientes por área geográfica para un mismo punto de salida.

Un almacén debe estar **activo** para poder usarse. El sistema espera que exista al menos un almacén activo de reparto; ese es el que se usa como base cuando una operación no indica otro.

> Consejo: nombra los almacenes de forma clara (ej. “FUENTE DE PIEDRA-MALAGA”) para que el reparto salga del punto correcto.

---

## 2. Jornadas (lo más usado)

Una jornada recorre el ciclo completo del vehículo:

```
Borrador → Cargando → Listo para salir → En ruta → De regreso → Pendiente de conciliación → Cerrada
```

Una jornada solo se puede **cancelar** antes de salir a ruta (Borrador, Cargando, Listo para salir). Con la salida ya iniciada, no.

### Cómo crear una jornada

1. Entra a **Jornadas**.
2. Botón **Nuevo** (o crea el vehículo primero si no existe).
3. Elige **vehículo** y **conductor**.
4. Elige el **almacén de origen** (dónde se carga).
5. Asocia una **ruta** o selecciona **clientes/direcciones** a visitar (crea la ruta automáticamente).
6. Guarda. La jornada queda en **Borrador**.

> Si el vehículo no existe, el mismo formulario permite crearlo on‑the‑fly.

### La consola de la jornada

Al abrir una jornada verás un **cronograma de pasos** (stepper) y el botón principal que avanza el estado según corresponda:

| Estado | Botón para avanzar | Qué hace |
|---|---|---|
| Borrador | **Iniciar carga** | Pasa a Cargando |
| Cargando | (automático al guardar carga completa) | Pasa a Listo para salir |
| Listo para salir | **Iniciar ruta** | Pasa a En ruta |
| En ruta | **Marcar retorno** | Pasa a De regreso |
| De regreso | **Retornar remanente** | Pasa a Pendiente de conciliación |
| Pendiente de conciliación | (guardar conteo sin diferencias) | Pasa a Cerrada |

Encima del cronograma podrás ver una **alerta roja de MERCANCÍA PELIGROSA (ADR)** si la carga supera los puntos permitidos. En ese caso consulta la carta porte antes de salir.

### Sesgo de seguridad importante

No avances el estado “de oído”. El sistema valida que haya stock, que los seriales estén completos y que la capacidad del vehículo sea la correcta. Si falta algo, te lo dirá con un mensaje claro — revísalo antes de continuar.

---

## 3. Carga de la jornada

En esta pestaña decides **qué sube al vehículo**.

- **Agregar producto:** busca el producto para añadirlo al plan de carga.
- **Cantidad planificada:** cuántas unidades de ese producto.
- **Seriales:** para productos que se controlan envase por envase, pulsa **Seriales** y marca físicamente cada cilindro (por serial o código de barras).
- **Disponibilidad en origen:** te muestra cuánto hay realmente en el almacén, para no planificar más de lo que existe.

Reglas que el sistema hace cumplir:

- Las cantidades deben ser **mayores que cero**.
- Si un producto requiere seriales, debes **capturarlos todos** antes de confirmar (no puedes confirmar con seriales faltantes).
- No puedes planificar y confirmar más stock del disponible en el almacén origen.

Cuando todo esté completo: **Guardar y confirmar** (esto además avanza la jornada).

---

## 4. La ruta (operación en la calle)

Una vez que el vehículo salió, en la pestaña **Ruta** se trabajan las paradas:

- Cada **parada** es un cliente o almacén a visitar, en orden.
- El mapa muestra la ruta y qué paradas ya se completaron (cambian de color).
- En cada parada se abre el **evento de operación** (qué se hace ahí):

| Tipo de operación | Qué significa |
|---|---|
| **Entrega** | Dejar envases llenos al cliente. |
| **Recojo** | Retirar envases vacíos del cliente. |
| **Cambio** | Entregar llenos y llevarse vacíos en la misma visita. |

### Para una entrega

El formulario te ofrece dos atajos para no escribir todo a mano:

- **Serial rápido:** escanea o escribe el serial del envase y el sistema detecta el producto solo.
- **Cards de composición:** muestra los productos que el vehículo lleva para agregarlos con un clic.

Luego define cantidades, selecciona los seriales concretos a entregar y confirma la parada.

### Llenado criogénico (planta)

Si operas tanques criogénicos (entrega de gas a granel), existe un diálogo de **Llenado** dentro de Envases:

- Muestra las **fuentes criogénicas** disponibles (tanque origen + su stock en kg).
- Seleccionas el **tipo de resultado** y marcamos **seriales vacíos** a llenar.
- Previsualizas si el tanque alcanza (total o parcial) y confirmas.
- El sistema descuenta el stock del tanque origen y deja la traza del llenado (`fill_operation_id`).

---

## 5. Conciliación y cierre de la jornada

Al regresar el vehículo, el sistema pasa a **Pendiente de conciliación**: se compara lo que salió contra lo que quedó.

- Se muestran las líneas esperadas (por producto).
- Cuentas el **stock real** que quedó en el camión y escribes la cantidad.
- Al guardar el conteo:
  - Sin diferencias → la jornada **se cierra** automáticamente.
  - Con diferencias → el sistema lo señala para revisar.

Es el momento de verificar faltantes/sobrantes. La jornada **solo se cierra cuando el conteo no tiene diferencias abiertas**.

---

## 6. Envases (ficha técnica y trazabilidad)

Pantalla para administrar el parque de cilindros:

- **Tabla de envases** con estados, búsqueda por serial/código y resumen por estado.
- Al abrir un envase: **ficha técnica** con marca, peso origen/actual, contenido, producto, datos de ADR, fechas de prueba hidrostática (PH).

Acciones disponibles desde un envase:

| Acción | Para qué |
|---|---|
| **Alta** (`+ Nuevo`) | Registrar un envase nuevo, con o sin alta operativa. |
| **Alta en lote** | Generar muchos envases secuenciales (prefijo + número correlativo + cantidad). |
| **Editar** | Corregir datos de la ficha técnica. |
| **Cambiar estado** | Moverlo (llenar, vaciar, trasladar, baja, etc.) con traza. |
| **Llenado / Vaciado** | Registrar contenido (incluye el llenado criogénico del punto 4). |
| **PH / Retimbrado / Garantía / Servicio** | Mantenimiento y certificaciones. |
| **Etiqueta** | Registrar la impresión de la etiqueta del envase. |
| **Trazabilidad** | Ver el recorrido histórico del envase (por dónde pasó, cuándo, en qué estado). |

### Estados del envase

| Estado | Significado |
|---|---|
| `EN_ALMACEN_VACIO` | Vacío y disponible en almacén (listo para llenar). |
| `CREADO_VACIO` | Recién dado de alta, sin carga operativa. |
| `LLENADO_OK` | Lleno y listo para reparto. |
| `EN_LLENADO` | En proceso de llenado. |
| `CARGA_EN_VEHICULO` | Subido al camión. |
| `EN_RUTA` | Viajando. |
| `EN_CLIENTE_LLENO` | Entregado lleno al cliente. |
| `EN_CLIENTE_VACIO` | Vacío en el cliente (a devolver). |
| `VACIO_EN_ALMACEN` | Devuelto del cliente. |
| `DESCARGADO_POR_RECEPCIONAR` | Descargado, pendiente de recepción en almacén. |
| `RECEPCIONADO` | Recibido y contabilizado en almacén. |
| `EN_MANTENIMIENTO` / `PARA_REPARACION` | En mantenimiento/reparación. |
| `PARA_TRASLADO` | En espera de traslado a otro almacén. |
| `BLOQUEADO` / `OBSERVADO` | Con observación; no opera. |
| `DE_BAJA` / `PERDIDO` | Fuera de uso / pérdida. |

> Nota técnica simplificada: la ubicación actual de un envase se determina por el **último evento de ubicación** (entrada a almacén, carga, entrega, recogida). Cuando un envase queda sin ubicación visible, causa probable es que se dio de alta sin una operación que fije su almacén.

### Alta de envases en lote — casos límite

La herramienta de lote crea envases secuenciales. Dos cosas a saber:

- Si el alta **no incluye un almacén de destino**, los envases quedan **sin ubicación**. Para que queden vinculados a un almacén, debe resolverse el almacén de la operación (por defecto, el almacén activo principal).
- El lote no pide cliente: es un **vaciado directo en almacén**, no una entrada "desde cliente". Por eso no te pide datos del cliente.

Regla práctica: **asegúrate de que exista un almacén base resuelto** antes de generar el lote; así cada envase nace ubicado correctamente.

---

## 7. Contratos

Los **contratos** definen condiciones de entrega/recolección de envases por cliente (derechos de cupo, cantidades, excedentes).

Desde aquí:

- Crear / editar un contrato.
- Marcar un contrato como **vencido**.

Se usa para controlar cuántos envases corresponden a un cliente y qué pasa si entrega más de lo pactado.

---

## 8. Planificación (reservas de capacidad)

Planificación es un **calendario operacional**: qué capacidad de cada vehículo está reservada para adelante.

Se alimenta de las reservas y muestra qué se espera cargar por vehículo. **No** manipula el estado en vivo del reparto — para eso está Jornadas.

Sirváse como: "¿qué tenemos comprometido para el vehículo X?" antes de aceptar más reparto.

---

## Casos comunes (paso a paso)

### A. Un cliente pide envases y sale el vehículo
1. Registra el **pedido** (clientes → Pedidos) o la visita en la jornada.
2. Crea la **jornada** con vehículo, conductor y ruta.
3. Carga los productos y captura seriales.
4. Confirmas carga → Listo para salir.
5. Inicias ruta → el vehículo sale.
6. En cada parada haces Entrega/Recojo/Cambio.
7. Marcas retorno, retornas remanente.
8. Concilias el conteo y cierras la jornada.

### B. Recibo envases vacíos del cliente
- En la parada correspondiente usas operación **Recojo** o **Cambio**.
- El envase pasa a la jornada como devolución y luego se concilia al regreso.

### C. Necesito dar de alta muchos envases de una vez
- Usa **alta en lote** en Envases, con prefijo y secuencia.
- Verifica que haya almacén base resuelto para que queden ubicados.

### D. Un envase viene defectuoso
- Desde su ficha: **Cambiar estado** a `OBSERVADO` o `PARA_REPARACION`.
- Registra el **servicio** o la **incidencia** correspondiente.

---

## Qué contempla el módulo (v1)

- Ciclo completo de jornada: carga → salida → ruta → retorno → conciliación → cierre.
- Carga con control de stock disponible y captura de seriales.
- Entrega, recogida y cambio en paradas, con serial rápido y composición del vehículo.
- Alta, edición y trazabilidad de envases (estados, PH, retimbrados, garantías, servicios, etiquetas).
- Llenado criogénico de cilindros desde tanques con descuento de stock.
- Ubicación de envases por evento (entrada a almacén, carga, entrega) y por campo de ubicación.
- Almacenes, vehículos, pedidos, rutas, movimientos, contratos y planificación de reservas.

## Qué NO contempla el módulo (v1)

- **No imprime documentos PDF** por sí mismo: carta porte, albarán y reportes se entregan como datos estructurados; la impresión física queda fuera.
- **No factura ni cobra**: el registro de venta/cobro pertenece a otro módulo (futuro).
- **No mueve dinero ni tarifas**: solo condiciones de entrega y envases.
- No hace traslado sin una jornada/operación asociada: cada movimiento de stock tiene dueño operativo.
- El **GPS** en ruta es registrado por el dispositivo, no es un servicio de rastreo permanente por cuenta propia.

## Límites y advertencias operativas

- **No se puede cancelar una jornada ya salida a ruta.** Piensa antes de pulsar "Iniciar ruta".
- **La conciliación solo cierra sin diferencias.** Prepara el conteo para no quedar trabado.
- **No confirmes una carga con seriales faltantes.** El sistema lo bloquea por diseño.
- **Un envase sin ubicación** suele venir de un alta sin almacén de operación, no de un error tuyo — pero avísalo para corregirlo.

---

## Vocabulario básico

| Término | Significado |
|---|---|
| Envase / Cilindro | Garrafa o botella que se transporta. |
| Serial | Número único individual del envase. |
| Jornada | Viaje del vehículo (todo su ciclo). |
| Carga | Productos + envases que suben al vehículo. |
| Parada | Cliente o almacén visitado en la ruta. |
| Conciliación | Comparación de lo que salió vs lo que quedó. |
| PH | Prueba hidrostática (certificado del cilindro). |
| ADR | Normativa de mercancías peligrosas (alerta roja). |
| Criogénico | Gas en fase líquida a granel (tanque). |