# Módulo de Compras y Abastecimiento a Proveedores — SYSTUTOR OSS

> Estado: baseline de requisitos del módulo (charter). NO es una A.SPEC atómica:
> es la fuente normativa de la que se derivarán A.SPECs atómicas futuras
> (COMPRAS-002..N). Toda implementación del módulo debe trazarse a una sección
> de este documento.

## Estado de implementación (se actualiza al cerrar cada A.SPEC)

> Última actualización: COMPRAS-018 (devolución de mercadería §26; tracker 013..018 al día).

Leyenda: ✅ DONE · 🟡 PARCIAL · ❌ PENDIENTE · 🔮 FUTURO (fuera de horizonte cercano)

| § | Sección | Estado | Vía |
|---|---------|--------|-----|
| 3 | Tipos de compra | ❌ | solo mercancía tradicional hoy |
| 4 | Solicitud de compra | ❌ | |
| 5 | Orden de compra | ✅ | CRUD + items (pre-002, endurecido en 002) |
| 6 | Ciclo de vida | ✅ | COMPRAS-002 |
| 7 | Aprobación | 🟡 | confirm en un paso; políticas diferidas |
| 8 | Preparación de envases | ✅ | COMPRAS-005 |
| 9 | Despacho por serial | ✅ | COMPRAS-005 |
| 10 | Motivo de envío | ✅ | service_type por serial (COMPRAS-005) |
| 11 | Custodia del proveedor | ✅ | estado derivado EN_CUSTODIA (COMPRAS-005) |
| 12 | Control de permanencia | 🟡 | days_out + filtro days_gt (COMPRAS-005); alertas automáticas pendientes |
| 13 | Recepción desde proveedor | ✅ | receipts ✓ + retorno ✓ (007) + vínculo receipt↔despacho (008) |
| 14 | Recepción parcial | ✅ | retorno parcial por serial ilimitado (COMPRAS-007) |
| 15 | Conciliación por serial | ✅ | /return concilia seriales vs despacho (COMPRAS-007) |
| 16 | Conciliación física | ✅ | conteo físico serial-by-serial + discrepancias auditadas (COMPRAS-017) |
| 17 | Recepción comercial | ✅ | aceptadas/rechazadas + cierre comercial (COMPRAS-009) |
| 18 | Recepción con diferencias | ✅ | difference_type FALTANTE/SOBRANTE/DANO + incidencia (COMPRAS-009) |
| 19 | Servicios realizados | ✅ | líneas de servicio por serial en recepción (COMPRAS-014) |
| 20 | PH y retimbrado | ✅ | datos legales PH/retimbrado con vigencia y validación (COMPRAS-015) |
| 21 | Recepción en almacén | ✅ | stock_connector en receipts (orden→recepción→ledger) |
| 22 | Costos | ✅ | costo real prorratea item + cost_lines (COMPRAS-010) |
| 23 | Factura del proveedor | ✅ | alta + líneas + anulación (COMPRAS-011) |
| 24 | Conciliación tres vías | ✅ | orden↔recibido(aceptadas)↔facturado, MATCH/MISMATCH (COMPRAS-011) |
| 25 | Reclamaciones | ✅ | registro + ciclo a resolución (COMPRAS-012) + derivación idempotente desde MISMATCH (COMPRAS-013) |
| 26 | Devoluciones | ✅ | retorno de envases (007) + devolución de mercadería con lifecycle auditable (COMPRAS-018) |
| 27 | Cancelaciones | ✅ | regla received_qty=0 (COMPRAS-002) |
| 28 | Cierre | ✅ | close administrativo con motivo (COMPRAS-002) |
| 29 | Proveedores | ✅ | CRUD + catálogo/detalle UI (COMPRAS-004) |
| 30 | Evaluación de proveedores | 🔮 | |
| 31 | Integración planificación | ❌ | |
| 32 | Integración Logistics | 🟡 | lectura ✓ + vínculo opcional a jornadas ✓ (007); escritura/movimientos pendientes |
| 33 | Integración Inventario | ✅ | connector trazable |
| 34 | Integración Productos | ✅ | catálogo maestro único |
| 35 | Integración Finanzas | ❌ | |
| 36 | Trazabilidad | 🟡 | eventos de orden ✓; auditoría general pendiente |
| 37 | Multiempresa y sucursales | ✅ | tenant_id en todas las operaciones |
| 38 | Permisos operativos | 🟡 | 8 permisos (supplier/order/dispatch read+manage; COMPRAS-005) |
| 39 | Dashboard operativo | ❌ | |
| 40 | Consultas esenciales | ✅ | por orden/proveedor/cilindro en custodia (005) + historial técnico por serial (COMPRAS-016) |
| 41 | Reportes | ❌ | |
| 42 | Flujo principal llenado | ✅ | procure-to-pay completo: 002+005+007+008+009 (comercial) +010 (costo real) +011 (factura+tres vías) +012/013 (reclamaciones + derivación) +014/015/016/017 (servicio técnico, PH, historial y conteo físico) +018 (devolución de mercadería) |
| 43 | Flujo recepción parcial | ✅ | retornos parciales ilimitados, saldo visible (COMPRAS-007) |
| 44 | Flujo servicio técnico | ✅ | retorno 007 + servicios por serial (014) + PH/retimbrado (015) + historial técnico consultable (016) |
| 45 | Reglas críticas | 🟡 | vigentes como invariantes de specs cerradas |
| 46 | Objetivo operativo final | — | meta global |

---

## 1. Propósito

El módulo de Compras administra el proceso mediante el cual una empresa solicita, autoriza, ordena, recibe y concilia bienes o servicios adquiridos a proveedores.

En el contexto de gases industriales, el módulo debe cubrir además un flujo operativo especialmente importante: la empresa puede enviar cilindros o envases propios vacíos a un proveedor para que sean llenados, inspeccionados, reparados, retimbrados o sometidos a otros servicios, y posteriormente recibir esos mismos envases de regreso.

Por lo tanto, Compras no se limita a registrar cuánto se compra y a qué precio. También debe coordinar la relación entre:

* la necesidad de abastecimiento;
* el proveedor;
* el producto o servicio solicitado;
* la orden de compra;
* los envases enviados al proveedor;
* la custodia temporal de esos envases;
* los envases efectivamente recibidos;
* las cantidades comerciales recibidas;
* las diferencias;
* los costos;
* los documentos del proveedor;
* el inventario resultante;
* y la trazabilidad histórica de toda la operación.

El módulo debe permitir responder con precisión preguntas como:

* ¿Qué se solicitó comprar?
* ¿A qué proveedor?
* ¿Quién lo autorizó?
* ¿Cuánto se ordenó?
* ¿Qué cilindros fueron enviados?
* ¿Cuáles siguen en poder del proveedor?
* ¿Cuáles regresaron?
* ¿Qué gas contiene cada uno?
* ¿Qué servicios realizó el proveedor?
* ¿Qué cantidad se recibió realmente?
* ¿Qué quedó pendiente?
* ¿Qué se facturó?
* ¿Existen diferencias entre lo ordenado, recibido y facturado?
* ¿Cuál fue el costo real de la operación?

---

# 2. Principio fundamental del módulo

Compras es responsable de la operación comercial de abastecimiento, pero no debe apropiarse de responsabilidades que pertenecen a otros módulos.

La separación principal será:

### Compras

Es responsable de:

* solicitudes de compra;
* órdenes de compra;
* proveedores dentro del contexto comercial;
* condiciones de compra;
* cantidades ordenadas;
* precios acordados;
* despachos de envases relacionados con compras;
* recepciones de proveedor;
* conciliación entre lo ordenado y lo recibido;
* servicios contratados al proveedor;
* diferencias;
* reclamaciones;
* seguimiento del cumplimiento del proveedor.

### Logística

Es responsable de:

* identidad individual de cada cilindro;
* serial;
* estado físico y operativo;
* ubicación;
* custodia;
* movimientos;
* trazabilidad;
* PH;
* retimbrados;
* inspecciones;
* servicios realizados sobre el envase.

Compras puede solicitar operaciones sobre cilindros, pero no debe modificar directamente su trazabilidad.

### Inventario

Es responsable de:

* existencias;
* almacenes;
* entradas;
* salidas;
* transferencias;
* stock disponible;
* ledger de inventario;
* valoración de existencias.

Compras informa que se ha producido una recepción; Inventario registra el efecto sobre stock.

### Productos

Es responsable de:

* gases;
* suministros;
* unidades;
* marcas;
* categorías;
* códigos;
* configuración ADR;
* costos y precios maestros cuando corresponda.

### Finanzas / Cuentas por Pagar

Es responsable de:

* obligaciones con proveedores;
* vencimientos;
* pagos;
* saldos;
* documentos contables;
* conciliaciones financieras.

---

# 3. Tipos de compra

El módulo debe permitir distinguir claramente qué se está comprando.

## 3.1 Compra de producto sin envase

Ejemplos:

* accesorios;
* válvulas;
* reguladores;
* equipos;
* material de soldadura;
* suministros;
* repuestos.

Se trata de una compra tradicional de mercancía.

---

## 3.2 Compra de gas utilizando envases propios

Este es uno de los casos principales.

La empresa posee los cilindros y los envía vacíos al proveedor.

El proveedor vende el contenido o servicio de llenado.

La empresa no está comprando nuevamente el cilindro.

Debe diferenciarse claramente:

* propiedad del envase;
* contenido del envase;
* servicio de llenado;
* cantidad comercial adquirida.

---

## 3.3 Compra de cilindros nuevos

La empresa puede adquirir:

* cilindro vacío;
* cilindro lleno;
* paquete de cilindros;
* bloque;
* recipiente especial.

En este caso, después de la recepción, el nuevo envase debe incorporarse al patrimonio y trazabilidad logística de la empresa.

---

## 3.4 Servicio realizado sobre envases

El proveedor puede recibir envases para:

* prueba hidrostática;
* retimbrado;
* inspección;
* reparación;
* mantenimiento;
* cambio de válvula;
* sustitución de componentes;
* pintura;
* acondicionamiento;
* limpieza;
* certificación.

Una misma operación puede incluir simultáneamente llenado y servicio técnico.

---

## 3.5 Compra mixta

Una orden puede contener diferentes conceptos:

* cargas de gas;
* servicios;
* repuestos;
* transporte;
* cilindros nuevos;
* accesorios.

La operación debe conservar la separación entre cada concepto para poder realizar posteriormente una conciliación correcta.

---

# 4. Solicitud de compra

La solicitud de compra representa una necesidad interna antes de comprometer una compra con un proveedor.

Puede originarse por:

* falta de stock;
* stock mínimo;
* pedido extraordinario;
* planificación logística;
* demanda proyectada;
* solicitud de almacén;
* necesidad de producción;
* mantenimiento;
* requerimiento de una sucursal;
* necesidad administrativa.

Debe registrar como mínimo:

* quién solicita;
* sede o sucursal solicitante;
* almacén;
* fecha;
* producto o servicio;
* cantidad;
* unidad;
* fecha requerida;
* prioridad;
* motivo;
* observaciones.

La solicitud puede pasar por revisión y aprobación antes de convertirse en una orden.

No todas las empresas deberán utilizar obligatoriamente solicitudes de compra. El sistema debe permitir operar directamente con órdenes cuando la política del cliente así lo permita.

---

# 5. Orden de compra

La orden de compra representa el compromiso comercial con el proveedor.

Debe contener:

* proveedor;
* sede o empresa compradora;
* fecha;
* moneda;
* condición de pago;
* fecha prevista;
* lugar de entrega;
* almacén destino;
* responsable;
* observaciones;
* referencia comercial;
* productos;
* servicios;
* cantidades;
* unidades;
* precios;
* descuentos;
* impuestos aplicables;
* costos adicionales cuando correspondan.

Cada línea debe permitir conocer:

* qué se compró;
* cuánto;
* cuánto se recibió;
* cuánto sigue pendiente;
* cuánto fue rechazado;
* cuánto fue cancelado.

---

# 6. Ciclo de vida de la orden

Una orden debe poder encontrarse, como mínimo, en situaciones equivalentes a:

* borrador;
* pendiente de aprobación;
* aprobada;
* enviada al proveedor;
* parcialmente atendida;
* completamente atendida;
* cerrada;
* cancelada.

Una orden no debe considerarse completada únicamente porque haya sido enviada al proveedor.

Debe existir diferencia entre:

* autorizado;
* solicitado;
* recibido;
* facturado;
* cerrado.

---

# 7. Aprobación de compras

El sistema debe permitir políticas de autorización.

Ejemplos:

* compras pequeñas sin aprobación adicional;
* compras superiores a determinado importe requieren supervisor;
* servicios técnicos de cilindros requieren responsable autorizado;
* modificaciones posteriores a la aprobación deben quedar registradas.

La aprobación debe conservar:

* usuario;
* fecha;
* decisión;
* observación;
* importe aprobado;
* versión o condición de la orden en el momento de la aprobación.

Una orden modificada significativamente después de ser aprobada puede requerir nueva aprobación según la política configurada.

---

# 8. Preparación de envases para proveedor

Cuando la compra requiere enviar cilindros propios al proveedor, debe existir una etapa de preparación.

En esta etapa se seleccionan los envases que serán enviados.

Para cada envase se debe conocer:

* serial;
* tipo;
* producto asociado;
* capacidad;
* estado actual;
* ubicación;
* propietario;
* condición;
* PH vigente;
* información relevante para transporte o servicio.

Antes de autorizar la salida, el sistema debe detectar situaciones incompatibles.

Ejemplos:

* cilindro ya enviado a otro proveedor;
* cilindro en posesión de cliente;
* cilindro bloqueado;
* cilindro fuera de servicio;
* cilindro en reparación;
* serial inexistente;
* cilindro perteneciente a otra empresa;
* cilindro no disponible físicamente;
* condición técnica incompatible con la operación solicitada.

---

# 9. Despacho de envases al proveedor

El despacho representa la salida física de los envases hacia el proveedor.

Debe estar relacionado con:

* proveedor;
* orden de compra;
* sucursal;
* almacén de origen;
* transportista cuando corresponda;
* vehículo cuando corresponda;
* conductor cuando corresponda;
* fecha;
* motivo;
* responsable;
* listado exacto de envases.

El despacho debe conservar permanentemente qué seriales salieron.

Nunca debe depender únicamente de una cantidad.

No es suficiente registrar:

"50 cilindros enviados".

Debe poder conocerse cuáles fueron esos 50 cilindros.

---

# 10. Motivo de envío del cilindro

Cada cilindro enviado debe indicar por qué se entrega al proveedor.

Entre los motivos posibles:

* llenado;
* prueba hidrostática;
* retimbrado;
* inspección;
* reparación;
* mantenimiento;
* cambio de válvula;
* acondicionamiento;
* certificación;
* combinación de varios servicios.

Esto permite posteriormente comparar lo solicitado con lo efectivamente realizado.

---

# 11. Custodia del proveedor

Una vez entregado físicamente el cilindro, debe quedar registrado que se encuentra bajo custodia del proveedor.

Esto permite conocer en todo momento:

* cuántos cilindros posee cada proveedor;
* cuáles son;
* desde cuándo;
* por qué fueron enviados;
* qué orden los originó;
* qué servicio esperan;
* cuánto tiempo llevan fuera;
* cuáles ya debieron regresar.

Esta información es especialmente importante porque los envases pueden representar activos de alto valor.

---

# 12. Control de permanencia en proveedor

El módulo debe poder detectar envases retenidos demasiado tiempo.

Debe ser posible consultar:

* envases enviados hoy;
* envases pendientes;
* envases en proveedor por más de determinados días;
* envases cuyo retorno estaba previsto y no ocurrió;
* envases pendientes de servicio;
* envases asociados a órdenes ya vencidas.

Esto permite controlar pérdidas, olvidos y demoras.

---

# 13. Recepción desde proveedor

Cuando regresan los cilindros o productos, debe realizarse una recepción.

La recepción debe registrar:

* proveedor;
* orden relacionada;
* despacho relacionado;
* fecha;
* almacén receptor;
* responsable;
* documento del proveedor;
* cantidades recibidas;
* envases recibidos;
* servicios realizados;
* incidencias;
* observaciones.

La recepción puede ser total o parcial.

---

# 14. Recepción parcial

El sistema nunca debe asumir que todo lo despachado regresa simultáneamente.

Ejemplo:

Se enviaron 100 cilindros.

Regresan 72.

Posteriormente regresan 20.

Quedan 8 pendientes.

El sistema debe conservar claramente:

* 100 enviados;
* 92 recibidos;
* 8 pendientes.

Los 8 pendientes continúan bajo custodia del proveedor.

La orden puede permanecer parcialmente atendida hasta que se resuelva el saldo pendiente.

---

# 15. Conciliación por serial

Durante la recepción se debe comparar cada cilindro recibido con los cilindros previamente enviados.

El sistema debe distinguir:

* cilindro esperado y recibido;
* cilindro esperado pero pendiente;
* cilindro no esperado;
* serial duplicado;
* serial desconocido;
* cilindro perteneciente a otra operación;
* cilindro perteneciente a otro proveedor;
* cilindro perteneciente a otro propietario.

Las diferencias no deben ocultarse ni corregirse automáticamente.

Deben quedar registradas para revisión.

---

# 16. Conciliación física

Además del serial, la recepción debe poder comprobar:

* producto contenido;
* condición lleno/vacío;
* presión cuando aplique;
* válvula;
* capacidad;
* estado físico;
* sello;
* identificación;
* PH;
* retimbrado;
* observaciones visuales.

Dependiendo del nivel de control de cada cliente, algunos campos podrán ser obligatorios y otros opcionales.

---

# 17. Recepción comercial

La recepción física de cilindros y la recepción comercial de producto son conceptos relacionados, pero diferentes.

Ejemplo:

Se enviaron 50 cilindros para llenado de oxígeno.

Pueden regresar 50 cilindros físicamente, pero comercialmente existir una diferencia en la cantidad suministrada.

El sistema debe permitir determinar:

* cantidad ordenada;
* cantidad recibida;
* cantidad aceptada;
* cantidad rechazada;
* cantidad pendiente.

Esto es especialmente importante cuando la unidad comercial no coincide exactamente con el número de envases.

---

# 18. Recepción con diferencias

Una recepción debe permitir registrar incidencias tales como:

* faltante;
* sobrante;
* producto incorrecto;
* cilindro incorrecto;
* cilindro dañado;
* cilindro vacío;
* llenado incompleto;
* servicio no realizado;
* servicio incorrecto;
* válvula incorrecta;
* daño durante custodia;
* problema documental;
* diferencia de cantidad;
* diferencia de precio;
* condición técnica no conforme.

La recepción puede ser aceptada:

* completamente;
* parcialmente;
* con observaciones;
* o rechazada.

---

# 19. Servicios realizados por proveedor

Cada servicio técnico realizado sobre un cilindro debe poder relacionarse con el envase específico.

Ejemplos:

* prueba hidrostática;
* retimbrado;
* cambio de válvula;
* reparación;
* pintura;
* inspección;
* mantenimiento.

La información resultante deberá pasar a formar parte de la historia técnica del cilindro.

Compras registra qué servicio fue adquirido y cuánto costó.

Logística conserva el historial técnico del envase.

---

# 20. Prueba hidrostática y retimbrado

Cuando un proveedor realiza una prueba hidrostática o retimbrado, la recepción debe permitir registrar la información necesaria para actualizar la trazabilidad técnica.

Debe quedar relacionado:

* cilindro;
* proveedor;
* fecha;
* resultado;
* vigencia;
* referencia documental;
* observaciones.

El módulo de Compras conserva el vínculo comercial.

Logística conserva el estado técnico resultante.

---

# 21. Recepción en almacén

Una vez aceptada la recepción, los productos deben ingresar al almacén correspondiente.

El módulo de Compras no debe modificar directamente cantidades de stock.

La recepción validada constituye el origen documental que permite a Inventario registrar el movimiento correspondiente.

Esto mantiene una separación clara entre:

* "se recibió una compra";
* y "se actualizó el inventario".

---

# 22. Costos

Compras debe conservar el costo comercial de adquisición.

El costo puede incluir:

* precio del producto;
* costo de llenado;
* transporte;
* seguros;
* inspección;
* retimbrado;
* mantenimiento;
* manipulación;
* otros cargos.

Debe ser posible distinguir qué costos afectan:

* al producto;
* al servicio;
* al transporte;
* al envase;
* o a toda la operación.

La política definitiva de valoración de inventario corresponde al módulo de Inventario y Costos.

---

# 23. Factura o documento del proveedor

El módulo debe poder relacionar las compras y recepciones con los documentos entregados por el proveedor.

Debe poder conocerse:

* qué orden originó la factura;
* qué recepciones están incluidas;
* qué productos fueron facturados;
* qué servicios fueron facturados;
* qué cantidades;
* qué precios;
* qué impuestos;
* qué diferencias existen.

Una factura no debe implicar automáticamente que todo lo facturado fue recibido correctamente.

---

# 24. Conciliación de tres vías

Una función importante del módulo será comparar:

### Lo ordenado

Lo que la empresa autorizó comprar.

### Lo recibido

Lo que efectivamente ingresó y fue aceptado.

### Lo facturado

Lo que el proveedor está cobrando.

El sistema debe detectar diferencias entre estos tres elementos.

Ejemplos:

* ordenado 100, recibido 100, facturado 100;
* ordenado 100, recibido 95, facturado 100;
* ordenado 100, recibido 105, facturado 105;
* precio acordado diferente al facturado;
* servicio facturado pero no registrado como realizado.

Las diferencias deben quedar pendientes de revisión.

---

# 25. Reclamaciones al proveedor

El sistema debe permitir registrar reclamaciones derivadas de una operación de compra.

Motivos posibles:

* faltante;
* producto incorrecto;
* mala calidad;
* cilindro dañado;
* servicio incompleto;
* servicio defectuoso;
* precio incorrecto;
* documento incorrecto;
* demora;
* pérdida de envase;
* daño durante custodia.

Cada reclamación debe poder seguirse hasta su resolución.

---

# 26. Devoluciones a proveedor

Cuando un producto recibido no es aceptado, puede requerirse devolución.

Debe poder conocerse:

* qué se devuelve;
* por qué;
* cantidad;
* serial cuando corresponda;
* recepción de origen;
* proveedor;
* fecha;
* responsable;
* resolución.

La devolución no debe borrar la recepción original.

Debe conservarse toda la historia.

---

# 27. Cancelaciones

Las órdenes pueden cancelarse total o parcialmente.

La cancelación debe considerar si existen:

* cantidades ya recibidas;
* cilindros actualmente en poder del proveedor;
* facturas;
* servicios realizados;
* movimientos de inventario.

No debe permitirse una cancelación que borre obligaciones o trazabilidad existente.

---

# 28. Cierre de una compra

Una orden podrá cerrarse cuando la operación haya sido resuelta.

El cierre debe considerar:

* cantidades recibidas;
* cantidades pendientes;
* cilindros pendientes;
* reclamaciones;
* servicios pendientes;
* diferencias comerciales;
* facturación relacionada.

Puede existir un cierre administrativo con diferencias aceptadas explícitamente.

La razón debe quedar registrada.

---

# 29. Proveedores

El sistema debe conservar información comercial relevante del proveedor:

* razón social;
* identificación fiscal;
* direcciones;
* contactos;
* condiciones de pago;
* moneda habitual;
* productos suministrados;
* servicios disponibles;
* plazos habituales;
* observaciones;
* estado activo/inactivo.

También debe permitir medir su desempeño.

---

# 30. Evaluación de proveedores

A futuro, el historial de Compras debe permitir obtener indicadores como:

* entregas a tiempo;
* porcentaje de cumplimiento;
* faltantes;
* reclamaciones;
* diferencias de facturación;
* tiempo promedio de retorno de cilindros;
* servicios rechazados;
* calidad;
* precio promedio;
* volumen comprado.

Esto permitirá comparar proveedores con información real.

---

# 31. Integración con planificación

Compras debe poder recibir necesidades provenientes de otros módulos.

Ejemplos:

* stock bajo;
* previsión de ventas;
* necesidad de ruta;
* producción;
* pedidos pendientes;
* stock mínimo;
* demanda extraordinaria.

Sin embargo, la generación automática de una necesidad no debe implicar automáticamente autorizar una compra.

---

# 32. Integración con Logistics

La integración con Logistics es esencial.

Compras necesita solicitar operaciones relacionadas con:

* salida de cilindros;
* entrega al proveedor;
* custodia;
* retorno;
* recepción;
* actualización técnica;
* servicios realizados.

Logistics debe seguir siendo el único propietario de:

* estado del cilindro;
* ubicación;
* historia;
* custodia;
* PH;
* retimbrados;
* seriales.

Compras conserva las razones comerciales de esas operaciones.

---

# 33. Integración con Inventario

Compras origina movimientos de inventario, pero no controla directamente el ledger.

Debe existir trazabilidad entre:

* orden;
* recepción;
* movimiento de inventario.

De esta forma será posible explicar siempre por qué aumentó una existencia.

---

# 34. Integración con Productos

Todos los productos y servicios comercializables deberán utilizar el catálogo maestro.

Compras no debe mantener un catálogo paralelo.

Esto incluye:

* gases;
* accesorios;
* repuestos;
* servicios;
* unidades;
* categorías;
* marcas;
* configuraciones relevantes.

---

# 35. Integración con Finanzas

La compra aceptada y documentada podrá originar una obligación con el proveedor.

Finanzas debe poder conocer:

* proveedor;
* importe;
* vencimiento;
* moneda;
* documento;
* saldo;
* pagos;
* estado financiero.

Compras no debe convertirse en un módulo de tesorería.

---

# 36. Trazabilidad

Toda operación importante debe conservar historial.

Debe poder conocerse:

* quién creó;
* quién modificó;
* quién aprobó;
* quién despachó;
* quién recibió;
* quién rechazó;
* quién cerró;
* cuándo ocurrió;
* qué cambió;
* qué motivo fue indicado.

La trazabilidad debe ser especialmente estricta cuando se trata de activos físicos como cilindros.

---

# 37. Multiempresa y sucursales

Toda operación debe pertenecer claramente a la empresa correspondiente.

Cuando aplique, también deberá relacionarse con:

* sucursal;
* almacén;
* área;
* usuario responsable.

Una empresa nunca debe poder consultar o modificar operaciones pertenecientes a otra empresa.

---

# 38. Permisos operativos

El módulo debe diferenciar capacidades como:

* consultar compras;
* crear solicitudes;
* crear órdenes;
* editar borradores;
* aprobar;
* enviar al proveedor;
* preparar cilindros;
* despachar;
* recibir;
* aceptar diferencias;
* cancelar;
* cerrar;
* administrar reclamaciones;
* consultar costos;
* consultar documentos del proveedor.

No todos los usuarios deben poder realizar todas las acciones.

---

# 39. Dashboard operativo

El módulo debería ofrecer una vista resumida con información útil para operación.

Ejemplos:

* órdenes abiertas;
* órdenes vencidas;
* compras parcialmente recibidas;
* recepciones pendientes;
* cilindros en proveedor;
* cilindros demorados;
* productos pendientes;
* reclamaciones abiertas;
* diferencias de recepción;
* diferencias entre recepción y facturación.

El objetivo no es solamente mostrar cifras, sino identificar operaciones que requieren atención.

---

# 40. Consultas esenciales

Debe ser posible consultar fácilmente:

### Por proveedor

* órdenes;
* recepciones;
* cilindros en custodia;
* reclamaciones;
* facturas relacionadas;
* historial.

### Por cilindro

* cuándo fue enviado;
* a qué proveedor;
* por qué;
* cuándo regresó;
* qué servicio recibió;
* qué compra lo originó.

### Por orden

* solicitado;
* ordenado;
* despachado;
* recibido;
* pendiente;
* facturado.

### Por producto

* cantidades compradas;
* proveedores;
* precio histórico;
* cantidad pendiente;
* volumen por periodo.

---

# 41. Reportes

El módulo deberá estar preparado para generar reportes como:

* órdenes de compra;
* compras por proveedor;
* compras por producto;
* compras por periodo;
* pendientes de recepción;
* recepciones parciales;
* envases en poder de proveedores;
* envases demorados;
* servicios realizados;
* diferencias de recepción;
* reclamaciones;
* historial de precios;
* cumplimiento de proveedor;
* conciliación orden-recepción-factura.

---

# 42. Flujo principal: cilindros enviados para llenado

El flujo principal será:

1. Se detecta la necesidad de producto.
2. Se genera una solicitud cuando la política lo requiera.
3. Se selecciona proveedor.
4. Se crea la orden de compra.
5. La orden es aprobada.
6. Se determina qué cilindros vacíos serán enviados.
7. Se valida que cada cilindro esté disponible.
8. Se prepara el despacho.
9. Los cilindros salen del almacén.
10. Se registra su traslado.
11. Se confirma que quedan bajo custodia del proveedor.
12. El proveedor realiza el llenado o servicios acordados.
13. Los cilindros regresan.
14. Se realiza recepción por serial.
15. Se detectan faltantes o diferencias.
16. Los cilindros aceptados regresan a disponibilidad operativa.
17. Los cilindros pendientes continúan asociados al proveedor.
18. Se registra la cantidad comercial recibida.
19. Inventario procesa la entrada correspondiente.
20. Se registran costos y documentos relacionados.
21. Se concilia lo ordenado, recibido y facturado.
22. Se resuelven diferencias.
23. Se cierra la operación.

---

# 43. Flujo con recepción parcial

Si no regresan todos los cilindros:

* la recepción se registra únicamente por los efectivamente recibidos;
* los restantes continúan pendientes;
* no se modifica artificialmente su situación;
* la orden permanece parcialmente atendida;
* el sistema muestra claramente el saldo;
* pueden existir múltiples recepciones posteriores.

Nunca debe requerirse crear una nueva orden solamente porque el proveedor entrega parcialmente.

---

# 44. Flujo de servicio técnico

Cuando los cilindros son enviados para servicios:

1. Se identifica el servicio requerido.
2. Se seleccionan cilindros.
3. Se genera la operación con proveedor.
4. Los cilindros se despachan.
5. Quedan bajo custodia externa.
6. El proveedor realiza el trabajo.
7. Se reciben los cilindros.
8. Se registra resultado técnico.
9. Se actualiza su historial logístico.
10. Se registra el costo.
11. Se aceptan o rechazan los servicios.
12. Se cierra la operación.

---

# 45. Reglas críticas

El módulo debe respetar las siguientes reglas:

* Ningún cilindro debe desaparecer de trazabilidad durante una compra.
* El número de cilindros enviados no reemplaza al detalle por serial.
* Una recepción parcial no debe cerrar automáticamente una orden.
* Un cilindro pendiente debe continuar visible como propiedad en custodia del proveedor.
* Compras no modifica directamente estados logísticos.
* Compras no modifica directamente inventario.
* Los servicios técnicos deben conservar relación con el cilindro.
* Las diferencias nunca deben corregirse silenciosamente.
* Cancelar una operación no debe borrar su historia.
* Una factura del proveedor no demuestra por sí sola que la mercancía fue recibida.
* Una recepción no demuestra por sí sola que la factura sea correcta.
* La propiedad del cilindro debe distinguirse del producto contenido.
* Todo cambio crítico debe quedar auditado.

---

# 46. Objetivo operativo final

El objetivo final del módulo no es simplemente saber cuánto dinero se gastó.

Debe proporcionar control completo sobre el abastecimiento.

Para una empresa de gases industriales, debe ser posible entrar al sistema y saber inmediatamente:

* qué falta comprar;
* qué está ordenado;
* qué está viajando;
* qué tiene cada proveedor;
* qué cilindros siguen fuera;
* qué regresó;
* qué quedó pendiente;
* qué servicios se realizaron;
* qué se recibió físicamente;
* qué entró en stock;
* qué se facturó;
* cuánto costó;
* y qué diferencias deben resolverse.

De esta manera, Compras se convierte en el orquestador del abastecimiento comercial mientras Logistics, Inventario, Productos y Finanzas mantienen la autoridad sobre sus respectivos dominios.
