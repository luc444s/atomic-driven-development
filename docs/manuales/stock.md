# Guía de uso — Módulo de Stock

**Público:** personal operativo (encargados de almacén, compras, contabilidad).
No requiere conocimientos técnicos ni de programación.

**Fuente:** este manual se escribió desde el comportamiento real de la aplicación, no desde diseños teóricos.

---

## ¿Qué es Stock?

Es el módulo donde se consulta y mueve el **stock físico** por producto y almacén, y donde se definen **los mínimos/máximos** de cada producto en cada almacén.

- El **balance** es la cantidad materializada de un producto en un almacén.
- Cada movimiento (ajuste, transferencia) queda registrado en el **ledger** (historial).

En el menú lateral, la sección **Stock** te lleva a la pantalla principal.

---

## La pantalla principal (Stock)

Tres tarjetas resumen arriba:

| Tarjeta | Significado |
|---|---|
| **Bases activas** | Cuántas combinaciones producto+almacén tienen balance. |
| **Alertas** | Balances **por debajo** del mínimo configurado. |
| **Cantidad total** | Suma de las cantidades visibles con el filtro actual. |

### Filtros de la tabla

- **Buscar:** por SKU, producto o almacén.
- **Almacén:** desplegable para ver un almacén específico (por defecto el **principal**).
- **Solo bajo mínimo:** marca para ver únicamente los productos bajo su mínimo.

Cada fila muestra **SKU, Producto, Almacén, Cantidad, Mín/Máx, Alerta** y acciones:

| Acción | Para qué |
|---|---|
| **Detalle** | Abre la ficha de ese producto en ese almacén. |
| **Ajustar** | Corrige la cantidad manualmente (positivo o negativo). |

Los botones superiores **Ajustar**, **Transferir** y **Configurar** abren esas operaciones sin salir del panel.

---

## Ajustar stock

Corrige la cantidad de un producto en un almacén (por ejemplo, tras un conteo físico).

1. **Producto** — búscalo con **Buscar producto**.
2. **Almacén** — selecciona dónde está la existencia.
3. **Cantidad** — número del ajuste:
   - **Positivo** (ej. `10`) = entrada de stock.
   - **Negativo** (ej. `-2`) = salida/sobrante descontado.
4. **Motivo** — explica por qué (ej. "Ajuste por conteo físico").

> Para **ingresos (cantidad positiva)**, el costo unitario se toma del costo activo del producto definido en Productos; no se escribe aquí.

Al **Guardar ajuste** se registra la operación en el ledger y se actualiza el balance.

---

## Transferir stock

Mueve existencias de un producto entre dos almacenes, registrando salida en origen y entrada en destino.

1. **Producto** — búscalo.
2. **Cantidad** — cuántas unidades.
3. **Almacén origen** — dónde salen.
4. **Almacén destino** — a dónde llegan (distinto del origen).
5. **Notas** (opcional) — ej. "Traslado a almacén de reparto".

Al **Guardar transferencia** el ledger queda con la salida y la entrada, y ambos balances se actualizan.

> El sistema no permite origen y destino iguales.

---

## Configurar mínimos y máximos

Define umbrales de control por **producto + almacén**. Sirven para la alerta "bajo mínimo".

1. **Producto** — búscalo.
2. **Almacén** — para qué almacén aplica.
3. **Mínimo** — cantidad mínima de seguridad.
4. **Máximo** — tope deseado (opcional).
5. **Configuración activa** — casilla para activarla/desactivarla.

Al **Guardar configuración** se aplica y la alerta de la pantalla principal se recalcula.

> La **configuración activa** determina si el umbral se tiene en cuenta. Desactiva la configuración si deja de aplicarse.

---

## La ficha de detalle (producto + almacén)

Al pulsar **Detalle** ves la información de ese producto en ese almacén: balance actual, límites y acceso a las mismas acciones (**Ajustar**, **Transferir**, **Configurar**) para ese producto concreto.

---

## Casos comunes (paso a paso)

### A. Corregir el conteo de un producto
1. **Stock** → **Ajustar**.
2. Elige producto, almacén, cantidad (+/−) y motivo.
3. **Guardar ajuste**.

### B. Mover stock a otro almacén
1. **Stock** → **Transferir**.
2. Producto, cantidad, origen y destino.
3. **Guardar transferencia**.

### C. Activar la alerta de reposición
1. **Stock** → **Configurar**.
2. Producto, almacén, **mínimo** (y máximo si aplica).
3. Activa **Configuración activa** → **Guardar**.
4. Verás el artículo en la tarjeta **Alertas** cuando baje del mínimo.

---

## Qué contempla el módulo (v1)

- Balance materializado por producto y almacén.
- Búsqueda, filtro por almacén y vista "solo bajo mínimo".
- Resumen: bases activas, alertas y cantidad total.
- Ajustes manuales (entradas y salidas) con motivo, sobre el ledger.
- Transferencias entre almacenes con salida/entrada.
- Configuración de mínimos/máximos por producto y almacén.

## Qué NO contempla el módulo (v1)

- **No controla envases por serial:** el control individual de cilindros/garrafas es de Logística (Envases).
- **No imprime informes de stock** por sí mismo (depende de reportes externos).
- **No valora automáticamente el stock** en dinero: el costo se toma del costo activo del producto en Productos.

## Límites y advertencias operativas

- Un **ajuste positivo** toma el costo del costo activo del producto en Productos: asegúrate de que ese costo esté definido.
- **Origen y destino de una transferencia deben ser distintos.**
- La **alerta "bajo mínimo" solo aparece si hay una configuración activa** con mínimo definido.

---

## Vocabulario básico

| Término | Significado |
|---|---|
| Balance | Cantidad materializada de un producto en un almacén. |
| Ledger | Historial de todos los movimientos de stock. |
| Ajuste | Corrección manual de la cantidad (+ entrada, − salida). |
| Transferencia | Movimiento de stock entre almacenes. |
| Mínimo | Umbral de seguridad; por debajo sale alerta. |
| Máximo | Tope deseado de existencia. |
| Base activa | Combinación producto+almacén con balance. |