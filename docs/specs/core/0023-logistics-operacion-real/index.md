# SPEC 0023 — Logistics: Operacion real del cliente

## Estado

Propuesta — Verificado contra código: 2026-07-04

## Contexto

El avance actual de `plugins/logistics/`, la documentacion del legacy y el material real de `grabaciones/Grab2` muestran una conclusion consistente:

- el sistema nuevo ya tiene un nucleo logistico operativo serio;
- el legacy aporta una base funcional madura construida durante anos;
- `Grab2` describe reglas de negocio reales que todavia no estan modeladas o cerradas en el sistema nuevo.

Esta spec no parte de la idea de "compatibilidad con legacy" como carga tecnica.

Parte de una idea distinta:

- legacy debe tratarse como base funcional seria;
- `Grab2` debe tratarse como evidencia de operacion real del cliente;
- el sistema nuevo debe preservar lo valioso de ambos y formalizar lo que hoy sigue implicito, manual o disperso.

## Objetivo

Convertir el conocimiento cruzado entre:

- avance real del sistema nuevo;
- documentacion legacy;
- conversaciones reales del cliente en `Grab2`;

en un backlog estructurado de implementacion para cerrar los gaps funcionales mas importantes del dominio logistico real.

## No objetivos

- no reescribir las specs anteriores;
- no invalidar lo ya implementado en `logistics`;
- no asumir que todo debe vivir dentro de `logistics` si el owner correcto es `crm`, `productos`, `stock` o un modulo futuro de facturacion/cobros;
- no convertir esta spec en una implementacion monolitica unica;
- no forzar compatibilidad tecnica con VB6, Crystal Reports o SQL Server.

## Fuentes base

- `docs/avances/logistics.md`
- `docs/specs/core/0014-1-logistics-gap-closure.md`
- `docs/specs/core/0020-logistics-planificacion-parciales.md`
- `docs/specs/core/0022-logistics-desmonolitizacion-frontend.md`
- `plugins/logistics/README.md`
- documentacion legacy ya analizada
- `grabaciones/Grab2/` y sus transcripciones

## Decision de interpretacion

Cuando haya tension entre estas fuentes:

1. `Grab2` manda para reglas de negocio operativas reales;
2. legacy manda como evidencia de procesos maduros ya probados;
3. el sistema nuevo manda para saber que ya existe hoy y que no debe reinventarse.

## Tabla maestra definitiva

Esta tabla es critica para implementar `SPEC 0023` y sus sub-specs.

## 1. Envases, ficha tecnica y trazabilidad

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Ficha tecnica de envase | La bombona necesita muchos mas datos tecnicos: litros, peso origen, peso actual, gas, datos troquelados, retimbrado, etc. | Si, legacy `Producto` y retimbrados tenian mucho mas detalle; `SPEC 0012` ya lo reconocia | Alto avance en envases; ya existen retimbrados, PH, servicios, labels, ownership | Parcial alto | Aun falta validar si todos los campos operativos reales de cliente ya estan visibles/editables en frontend y usados por procesos | `logistics` | `SPEC 0023A` Ficha tecnica completa de envase |
| Peso real del envase | Si la bombona tiene peso real, ese es el dato valido para operacion | Implicito en legacy por retimbrado y campos tecnicos | Parcial: hay peso actual/origen y endpoints de peso | Parcial | Falta convertirlo en regla visible y operativa en carga/transporte | `logistics` | `SPEC 0023B` Peso real y promedio |
| Peso promedio del envase | Si no hay peso real, usar un peso promedio por tipo/material/capacidad | En legacy aparece por Excel/operacion, no formalizado limpio | Bajo | Gap fuerte | Falta modelo, UI y regla backend de fallback | `logistics` + `productos` | `SPEC 0023B` |
| Trazabilidad completa por cilindro | Debe poder verse por donde paso cada bombona, especialmente medicinal | Si, legacy ya tenia trazabilidad fuerte | Si, base buena en `lg_cylinder_state_log` y vistas del frontend | Parcial alto | Falta garantizar que la trazabilidad incluya camion/almacen movil/ruta/cliente de forma operativa y auditable | `logistics` | `SPEC 0023C` Trazabilidad operativa extendida |
| Trazabilidad medicinal | Para medicinal es obligatorio poder reconstruir recorrido completo | No formalizado asi en docs, pero consistente con trazabilidad legacy | Bajo/medio | Gap fuerte | Falta un corte explicito de cumplimiento o trazabilidad reforzada | `logistics` | `SPEC 0023D` Trazabilidad medicinal |
| Etiquetado de cilindro | Cada bombona debe llevar codigo y etiqueta operativa | Si | Si | Bien encaminado | Validar formato final y flujo real de impresion en campo | `logistics` | incluir en `0023A/0023C` |

> **Code Reality Check (2026-07-04):** 0023A está **cerrado** — todos los campos técnicos (30+) están visibles y editables en frontend. 0023B (peso real) tiene backend completo, falta el fallback de peso promedio que no existe. 0023C (trazabilidad) tiene datos en 7+ tablas relacionadas, falta enriquecer vista. 0023D (trazabilidad medicinal) no tiene **absolutamente nada** — ni un flag booleano, es greenfield total. Etiquetado tiene modelo completo, falta integración física con impresora.

## 2. Carga, reparto y almacen movil

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Camion como almacen movil | El camion funciona como un almacen movil real | Parcialmente implicito en legacy | Parcial: hay rutas, loads y movimientos | Gap importante | Falta modelarlo explicitamente como estado/ubicacion operativa | `logistics` | `SPEC 0023E` Almacen movil |
| Carga desde agenda | La agenda se acepta y eso dispara que debe cargarse | Parcial en legacy | Bajo/medio | Gap fuerte | Falta integrar agenda -> carga -> vehiculo | `logistics` | `SPEC 0023F` Agenda a carga |
| Aceptacion de tarea por repartidor | Un repartidor toma una ruta/tarea y desaparece para otros | No claro en docs, si en operacion real | Bajo | Gap fuerte | Falta ownership por repartidor en agenda | `logistics` | `SPEC 0023F` |
| Carga comprometida + stock libre | El camion sale con lo comprometido y con bombonas extra "libres" | Si, descrito por cliente | Bajo | Gap fuerte | Falta modelo de carga libre de ruta | `logistics` + `stock` | `SPEC 0023G` Stock libre en reparto |
| Escaneo al cargar | Se debe escanear al subir al camion | Legacy si operaba con escaneo por envase | Parcial: el sistema tiene escaneo y loads, pero no ese flujo unificado | Parcial | Falta el flujo exacto en UI/app | `logistics` | `SPEC 0023H` Escaneo de carga |
| Confirmacion de carga por conductor | El conductor debe aceptar que la carga esta correcta | Legacy lo sugiere por operacion | Bajo | Gap fuerte | Falta aceptacion explicita previa a salida | `logistics` | `SPEC 0023I` Confirmacion de conductor |
| Retorno a almacen | Lo que no se vende/regresa debe volver a almacen o quedar en camion trazado | Si | Parcial | Parcial | Falta cierre claro de remanente de camion/almacen movil | `logistics` | `SPEC 0023E/0023G` |

> **Code Reality Check (2026-07-04):** 0023E (almacén móvil) — existe estado `CARGA_EN_VEHICULO` pero no modelo de ubicación. 0023F (agenda→carga) — **no existe el flujo**, es el gap operativo más crítico del dominio. 0023G (stock libre) — modelo de comprometido sólido, cero de stock extra. 0023H (escaneo) — infraestructura de scan sólida pero atada a movements, no a loads. 0023I (confirmación conductor) — `confirm_loads` existe pero sin identidad de conductor. Retorno a almacén: `vehicle_return` + recepción existen, falta conciliación automática.

## 3. Carta porte, albaran y documentos de transporte

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Carta porte por movimiento | La carta porte nace por movimiento/carga, no por ruta global | Si, confirmado | Si, `waybill` es por movimiento | Bien alineado en base | Mantener esa base | `logistics` | `SPEC 0023J` Carta porte nueva |
| Carta porte editable en ruta | Si cambia lo entregado/retirado, la carta porte debe cambiar | No formalizado en legacy tecnico, si en operacion actual | No | Gap critico | Falta versionado y mutacion en ruta | `logistics` | `SPEC 0023J` |
| Carta porte digital valida | No hace falta imprimir; debe ser valida en tablet/sistema | No en legacy | No | Gap critico | Falta modelo digital-first | `logistics` | `SPEC 0023J` |
| Carta porte interna | Existe como necesidad operativa actual | No explicita en legacy tecnico | No | Gap critico | Falta modelarla | `logistics` | `SPEC 0023J-A` Carta porte interna |
| Carta porte externa | Existe como necesidad operativa actual | Solo aparece como uso, no como flujo explicito tecnico | No | Gap critico | Falta modelarla | `logistics` | `SPEC 0023J-B` Carta porte externa |
| Firma en carta porte | Debe poder identificarse quien conduce y quien asume | Legacy no lo soporta | No | Gap fuerte | Falta firma/aceptacion y rol conductor | `logistics` | `SPEC 0023J-C` Firma y conductor |
| Relacion carta porte - albaran | Son documentos distintos | Si, Grab2 lo aclara mucho mejor | No claramente separado en UI | Gap importante | Falta separar flujos y documentos | `logistics` | `SPEC 0023K` Albaran operativo |
| Albaran valorado / no valorado | Algunos clientes lo quieren con valor, otros no | Si, por operacion | No claro | Gap fuerte | Falta soporte de variantes | `logistics` + futura facturacion | `SPEC 0023K` |
| Entregas y retiros en albaran | Debe registrar llenas entregadas, vacias retiradas y excepciones | Si | Bajo/medio | Gap fuerte | Falta documento operativo rico | `logistics` | `SPEC 0023K` |
| Numeracion de albaran por sede | M-, S-, etc. por delegacion | No claro antes; ahora si | No visible | Gap concreto | Falta correlativo por centro | `logistics` | `SPEC 0023L` Numeracion por sede |

> **Code Reality Check (2026-07-04):** 0023J (carta porte por movimiento) — correcto, waybill es por movimiento. 0023J (editable en ruta) — **no existe versionado**, gap crítico real. 0023J-A/B (interna/externa) — **no hay distinción de tipo**, gap crítico real. 0023J-C (firma) — no existe en waybill. 0023K (albarán) — backend tiene endpoints separados pero el esquema es idéntico al waybill; `quantity_in/out` existen en el modelo pero el waybill los colapsa a 1 sola cifra. 0023L (numeración) — infraestructura de `document_series`/`document_number` existe, secuencial por warehouse, falta scope por branch/sede.

## 4. ADR, peso y mercancia peligrosa

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Peso total transportado | El sistema debe saber si el vehiculo puede cargar mas | Si, legado carta porte y ADR | Parcial | Parcial | Falta llevarlo al flujo visible de carga | `logistics` | `SPEC 0023M` Peso de transporte |
| Umbral 1000 kg / litros | A partir de ese umbral entra obligacion fuerte ADR/reporte | No estaba tan explicito en docs; Grab2 lo clarifica | No visible | Gap fuerte | Falta logica/reportes visibles | `logistics` | `SPEC 0023N` Reporte ADR anual |
| Reporte anual mercancia peligrosa | Debe saberse cuanto se cargo, descargo y transporto | No implementado | No | Gap fuerte | Falta modelo/reportes regulatorios | `logistics` | `SPEC 0023N` |
| Peso por producto transportado | Las equivalencias deben existir para descontar y calcular | Parcial en legacy y Excel | Bajo/medio | Gap fuerte | Falta tabla o regla clara de equivalencias | `productos` + `logistics` | `SPEC 0023O` Equivalencias de transporte |
| ADR visible al usuario | No solo calculo backend; debe ayudar a decidir | Parcial docs, backend existe | Backend si, frontend no | Gap importante | Falta UX ADR | `logistics` | `SPEC 0023P` ADR operativo |
| Seleccion de vehiculo segura | La capacidad/peso/compatibilidad debe afectar salida real | Legacy lo trataba mas por operacion que por UI | Parcial backend | Gap importante | Integracion final con carga/salida | `logistics` | `SPEC 0023P` |

> **Code Reality Check (2026-07-04):** 0023M (peso transportado) — backend completo (`validate_route_weight_limit`, `build_load_weight_summary`), frontend de carga no muestra el peso. 0023N (umbral 1000 kg + reporte anual ADR) — **no existe absolutamente nada**, riesgo regulatorio real. 0023O (equivalencias) — no existen en logistics ni en productos. 0023P (ADR visible) — **corrección: frontend SÍ muestra ADR** en detalle de cilindro, waybill y formulario; el gap real es UX a nivel ruta/carga. 0023P (selección vehículo) — backend funcional (eligible-vehicles + restrictions), frontend no integrado.

## 5. Cliente, establecimientos y direcciones

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Nombre fiscal vs comercial | Son distintos y ambos importan | Si implicito | Bajo | Gap fuerte | CRM actual se queda corto | `crm` | `SPEC 0023D` Cliente comercial/fiscal |
| Varios establecimientos | Una empresa puede tener varias sedes/lugares de entrega | Si | Parcial por delivery points | Parcial | Falta modelo comercial completo y acople UX | `crm` + `logistics` | `SPEC 0023D` |
| Domicilio fiscal | Relevante para factura/contabilidad | Si | Bajo | Gap fuerte | Falta modelado fuerte o exposicion adecuada | `crm` | `SPEC 0023D` |
| Lugar de entrega | Relevante para logistica, distinto al fiscal | Si | Parcial | Parcial | Delivery points existen, pero falta amarre completo al modelo cliente | `crm` + `logistics` | `SPEC 0023D` |
| Responsable/contacto | Puede ser distinto del cliente/empresa | Si | Bajo/medio | Gap fuerte | Falta modelo rico de contactos | `crm` | `SPEC 0023R` Contactos y responsables |
| Asignacion de agente comercial | Cliente pertenece a agente/comercial | Si | Bajo | Gap fuerte | Falta owner comercial por cliente | `crm` | `SPEC 0023S` Gestion comercial |
| Ruta asociada a cliente/establecimiento | El cliente puede estar asociado a ruta/zona | Si | Parcial | Parcial | Falta la vision comercial-operativa completa | `crm` + `logistics` | `SPEC 0023D/0023F` |
| Coordenadas geograficas | Utiles para reparto y nuevos clientes | Si operativo, no critico inicial | Muy bajo | Gap medio | Falta captura simple | `crm` + futura app | `SPEC 0023T` Geolocalizacion minima |

> **Code Reality Check (2026-07-04):** Dominio cubierto por CRM cerrado (0023D, 0023R, 0023S, 0023XA/XB). Los gaps señalados son correctos y corresponden a futuros módulos de facturación/cobros, no a logistics.

## 6. Precios, presupuestos y condiciones especiales

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Precio de lista general | Existe una tarifa base general | Si | No en logistics, ni debe | Gap de dominio | Debe vivir fuera de logistics | `productos` / futuro comercial | `SPEC 0023U` Precios comerciales |
| Precio especial por cliente | Se guarda por cliente/producto | Si operativo | No | Gap fuerte | Falta motor minimo de condiciones comerciales | `crm` + `productos` | `SPEC 0023U` |
| Descuento porcentual | Puede aplicarse por porcentaje | Si | No | Gap fuerte | Falta modelo y permisos | `crm` + `productos` | `SPEC 0023U` |
| Precio fijo especial | Puede ser precio fijo, no solo % | Si | No | Gap fuerte | Falta modelo mixto | `crm` + `productos` | `SPEC 0023U` |
| Presupuesto previo | El comercial manda oferta y luego eso se convierte en condicion o venta | Si | No claro | Gap fuerte | Falta workflow presupuesto -> aprobacion -> pedido/despacho | futuro ventas/comercial | `SPEC 0023V` Presupuestos |
| Restriccion por rol | El comercial puede ofrecer pero no grabar cambios finales en ciertos casos | Si | No | Gap fuerte | Falta permisos por rol comercial | `crm` / ventas | `SPEC 0023V` |
| Condiciones comerciales persistentes | Lo pactado debe quedar visible para otros | Si | No | Gap fuerte | Falta historial/visibilidad comercial | `crm` | `SPEC 0023U/0023V` |

> **Code Reality Check (2026-07-04):** Dominio cubierto parcialmente por CRM cerrado (0023XA/XB). El motor de precios, descuentos y presupuestos es un gap real que vivirá en futuros módulos comerciales/facturación, no en logistics.

## 7. Facturacion, pagos y remesas

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Facturacion mensual automatica | Debe correr sola al inicio del mes | No lo teniamos tan claro | No | Gap fuerte | Falta scheduler + reglas + avisos | futuro facturacion | `SPEC 0023W` Facturacion programada |
| Clientes sin correo | Debe salir lista de no enviados y TXT de pendientes | No claro en docs | No | Gap concreto | Falta manejo de excepciones de envio | futuro facturacion | `SPEC 0023W` |
| Forma de pago | Es central en la ficha cliente | Si | No | Gap fuerte | Falta modelo | `crm` + facturacion | `SPEC 0023X` Formas de pago |
| Remesa bancaria | Es proceso critico y necesita fichero banco | Si operativo | No | Gap muy fuerte | Falta exportacion bancaria | facturacion/cobros | `SPEC 0023Y` Remesas |
| Cobrado / no cobrado / devuelto | Debe rastrearse manual/operativamente | Si | No | Gap fuerte | Falta cuentas por cobrar simples | facturacion/cobros | `SPEC 0023Z` CxC minimo |
| Anticipos | Puede cobrarse antes de ejecutar trabajo | Si | No | Gap medio/alto | Falta anticipo/adelanto | facturacion | `SPEC 0023AA` Anticipos |
| Facturacion inmediata vs fin de mes | Depende del cliente/servicio | Si | No | Gap fuerte | Falta politica de facturacion por cliente | facturacion | `SPEC 0023W/0023X` |

> **Code Reality Check (2026-07-04):** Dominio completo de futuros módulos. Todos los gaps señalados son reales — ninguno debe implementarse en logistics.

## 8. Impuestos, NIF/CIF y casos fiscales

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| NIF / CIF | Debe distinguir tipo de documento fiscal espanol | Si parcial | Bajo | Gap fuerte | Falta soporte serio de documento fiscal espanol | `crm` | `SPEC 0023AB` Fiscal Espana |
| Intracomunitario | Cliente puede estar o no registrado para IVA intracomunitario | Si | No | Gap fuerte | Falta flags/documentos y exportacion | `crm` + facturacion | `SPEC 0023AB` |
| Recargo de equivalencia | Hay clientes que lo requieren | Si | No | Gap fuerte | Falta soporte tributario | facturacion | `SPEC 0023AB` |
| Criterio de caja | Puede aplicar segun cliente | Si | No | Gap fuerte | Falta soporte tributario | facturacion | `SPEC 0023AB` |
| Exento / reducido / normal | El tipo fiscal no siempre es el mismo | Si | No | Gap fuerte | Falta modelo minimo de tratamiento fiscal | facturacion | `SPEC 0023AB` |
| Fianza sin IVA | Hay conceptos que no llevan IVA | Si | No | Gap concreto | Falta tipos especiales de concepto | facturacion | `SPEC 0023AC` Conceptos especiales |

> **Code Reality Check (2026-07-04):** Dominio de futuros módulos fiscales/facturación. El soporte NIF/CIF en CRM es básico, el resto no existe.

## 9. Contratos de envases

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Contrato anual | Se paga por adelantado y se renueva por facturacion | No tan claro | No | Gap fuerte | Falta submodulo contrato | `logistics` + facturacion | `SPEC 0023AD` Contratos envases |
| Contrato diario | Existe como modalidad | No claro | No | Gap | Falta modelado | `logistics` | `SPEC 0023AD` |
| Fin de contrato | El contrato termina al devolver la bombona | No formalizado | No | Gap fuerte | Falta cierre por devolucion | `logistics` | `SPEC 0023AD` |
| No se amarra a serie | Se amarra al tipo/cantidad, no a la matricula especifica | Si por operacion actual | No | Gap fuerte | Falta modelo correcto | `logistics` | `SPEC 0023AD` |
| Generacion previa | Puede mandarse antes de entregar | Si operativo | No | Gap medio | Falta workflow documental | `logistics` | `SPEC 0023AD` |
| Firma del contrato | Puede ser fisica ahora; digital despues | Si operativo | No | Gap medio | Falta estrategia de firma por etapas | `logistics` | `SPEC 0023AE` Firma contractual |

> **Code Reality Check (2026-07-04):** **No existe absolutamente nada** en código. Es uno de los gaps más grandes de logistics — submódulo completo por construir. 0 modelos, 0 endpoints, 0 UI. Prioridad: crítica.

## 10. Numeracion, delegaciones y multi-sede

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Correlativo por delegacion | M-, S-, etc. con secuencia por sede | Si por operacion real ahora | No | Gap concreto | Falta diseno de series por centro | `logistics` + futura facturacion | `SPEC 0023L` |
| Visibilidad por centro | Cada sede solo debe ver lo suyo; central ve todo | Si | Parcial por tenancy/warehouse | Parcial | Falta trasladarlo a clientes/facturacion/comercial | `core` + `crm` + `logistics` | `SPEC 0023AF` Scope por delegacion |
| Permisos por establecimiento | Repartidor/comercial debe ver solo su centro | Si | Parcial | Parcial | Falta aterrizarlo en modulos nuevos | `core` | `SPEC 0023AF` |

> **Code Reality Check (2026-07-04):** 0023L (correlativo) — infraestructura de `document_series`/`document_number` existe con secuencial por warehouse, falta scope por branch/sede. 0023AF (visibilidad) — warehouse-scope funciona en logistics endpoint por endpoint, no hay middleware global.

## 11. Productos, componentes y equivalencias

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Componentes / materias primas | No todo es producto final; tambien hay componentes e insumos | Si implicito | Bajo | Gap fuerte | Falta modelado o al menos clasificacion suficiente | `productos` + `stock` | `SPEC 0023AG` Clasificacion de productos |
| Equivalencias de carga | 30 m3 argon equivale a cierto peso liquido, etc. | Si operativo | No claro | Gap fuerte | Falta tabla/regla de equivalencias | `productos` | `SPEC 0023O` |
| Servicios como producto | Un "producto" tambien puede ser un servicio | Si operativo | Muy bajo | Gap fuerte | Falta taxonomia simple de tipo de producto | `productos` | `SPEC 0023AG` |
| Producto fisico vs virtual | Un servicio o fianza no es bombona fisica | Si | No | Gap fuerte | Falta distincion de dominio | `productos` + facturacion | `SPEC 0023AG/0023AC` |

> **Code Reality Check (2026-07-04):** Gaps de `productos`, no de `logistics`. Las equivalencias de transporte (0023O) no existen en ningún módulo — es el gap transversal más urgente de este dominio.

## 12. Reportes y operacion gerencial

| Tema | Regla / hallazgo de Grab2 | Legacy documentado | Sistema nuevo | Estado comparado | Gap exacto | Owner natural | Spec / sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Reportes de consistencia de documentos | Debe saberse que factura no subio / no se envio | Si operativo | No | Gap fuerte | Falta modulo de consistencia documental | facturacion | `SPEC 0023AH` Consistencia documental |
| Reportes gerenciales moviles | Hay reportes que conviene ver desde movil/app | No formalizado | No | Gap medio | Falta distinguir reportes operativos vs gerenciales | cross-module | `SPEC 0023AI` Reportes gerenciales |
| Reportes obligatorios ADR | Deben existir por cumplimiento | Si por necesidad legal | No | Gap fuerte | Falta reporting regulatorio | `logistics` | `SPEC 0023N` |
| Estado de deuda/cobros | Debe verse por cliente | Si | No | Gap fuerte | Falta modulo simple de deuda por cliente | cobros/facturacion | `SPEC 0023Z` |

> **Code Reality Check (2026-07-04):** Reportes ADR (0023N) y estado de deuda (0023Z) son gaps fuertes reales. Consistencia documental (0023AH) y reportes gerenciales (0023AI) no existen. Los 5 reportes operativos existentes (route-agenda, dispatch-ticket, transfer-albaran, load-summary, adr-summary) están consolidados y funcionales.

## Lectura consolidada (verificada contra código)

### Lo que ya esta fuerte en el sistema nuevo

- envases (incluyendo ficha técnica completa — 0023A cerrado);
- trazabilidad base (datos en 7+ tablas, vista por enriquecer);
- rutas base;
- carga base;
- movimientos base;
- planificacion base;
- recepcion base;
- equipos;
- `waybill` base (por movimiento, bien alineado);
- ADR en backend (config, incompatibilidades, puntos, vehículos elegibles);
- ADR visible en frontend (cilindro, waybill, formulario — gap 0023P corregido).

### Lo que estaba mas presente en legacy/documentacion

- flujo de carta porte por movimiento;
- despacho;
- ADR;
- forms de operacion logistica;
- tecnica historica de reportes.

### Lo que `Grab2` revela como gap real (confirmado)

- ~~cliente comercial/fiscal rico~~ → CRM cerrado (0023D, 0023R, 0023S);
- **contratos de envases** → no existe nada, crítica;
- precio especial por cliente → futuro comercial;
- remesas y formas de pago → futura facturación;
- **almacén movil real** → existe estado CARGA_EN_VEHICULO, no modelo;
- **agenda → carga → camion → reparto** → no existe el flujo, crítica operativa;
- **carta porte viva/digital** → no existe versionado, crítica;
- **albaran operativo real** → endpoints existen, datos idénticos a waybill;
- **pesos promedio/reales** → real weight existe, fallback promedio no;
- **reporting ADR >1000 kg** → no existe, riesgo regulatorio;
- **correlativos por delegacion** → infra existe, scope branch falta.

## Estructura sugerida de sub-specs (actualizada post-verificación)

### Envases (prioridad alta)
- `0023A-envase-ficha-tecnica-y-pesos.md` — **gap cerrado**, solo auditar
- `0023B-peso-real-y-promedio.md` — crear modelo de fallback
- `0023C-trazabilidad-operativa-extendida.md` — enriquecer vista existente
- `0023D-trazabilidad-medicinal.md` — greenfield, compliance
- `0023AD-contratos-de-envases.md` — submódulo completo

### Carga y reparto (prioridad alta)
- `0023E-almacen-movil.md` — modelar vehículo como ubicación
- `0023F-agenda-carga-vehiculo.md` — flujo core operativo
- `0023G-stock-libre-reparto.md` — modelo de carga extra
- `0023H-escaneo-de-carga.md` — integrar scan con loads
- `0023I-confirmacion-conductor.md` — workflow de aceptación

### Documentos de transporte (prioridad alta)
- `0023J-carta-porte-digital.md` — versionado + interna/externa + firma
- `0023K-albaran-operativo.md` — separar de waybill, valorado/no
- `0023L-numeracion-por-sede.md` — series por branch

### ADR y regulatorio (prioridad media)
- `0023M-peso-de-transporte.md` — frontend de carga
- `0023N-reporte-ADR-anual.md` — umbral 1000 kg + reporte anual
- `0023O-equivalencias-de-transporte.md` — tabla de densidades
- `0023P-ADR-operativo.md` — UX + selección vehículo

### Reportes (prioridad media-baja)
- `0023AH-consistencia-documental.md`
- `0023AI-reportes-gerenciales.md`
- `0023Z-CxC-minimo.md` — estado de deuda

### Diferidos a otros módulos
- `0023D-cliente-comercial-fiscal-y-direcciones.md` → CRM (cerrado)
- `0023R-contactos-y-responsables.md` → CRM (cerrado)
- `0023S-gestion-comercial.md` → CRM (cerrado)
- `0023XA/XB-condiciones-comerciales.md` → CRM (cerrado)
- `0023U-precios-comerciales.md` → futuro comercial
- `0023V-presupuestos.md` → futuro ventas
- `0023W-facturacion-programada.md` → futuro facturación
- `0023X-formas-de-pago.md` → futuro facturación
- `0023Y-remesas.md` → futuro cobros
- `0023Z-CxC.md` → futuro cobros
- `0023AA-anticipos.md` → futuro facturación
- `0023AB-fiscal-espana.md` → futuro facturación
- `0023AC-conceptos-especiales.md` → futuro facturación
- `0023AE-firma-contractual.md` → futuro (post-contratos)
- `0023AF-scope-por-delegacion.md` → core
- `0023AG-clasificacion-productos.md` → productos
- `0023T-geolocalizacion.md` → crm + futura app

## Backlog priorizado (orden de implementación sugerido)

### Fase 1 — Envases (lo que toca cilindros directamente)
| Prio | Gap | Spec | Esfuerzo | Depende de |
|------|-----|------|----------|------------|
| 1 | Trazabilidad medicinal | 0023D | Medio | — |
| 2 | Contratos de envases | 0023AD | Alto (submódulo) | — |
| 3 | Peso promedio fallback | 0023B | Bajo | — |
| 4 | Trazabilidad extendida (UI) | 0023C | Bajo (solo vista) | — |

### Fase 2 — Carga y reparto (flujo operativo core)
| Prio | Gap | Spec | Esfuerzo | Depende de |
|------|-----|------|----------|------------|
| 5 | Agenda → carga → vehículo | 0023F | Alto | Fase 1 |
| 6 | Stock libre en reparto | 0023G | Medio | 0023F |
| 7 | Camión como almacén móvil | 0023E | Medio | 0023F, 0023G |
| 8 | Confirmación de conductor | 0023I | Bajo | 0023F |
| 9 | Escaneo al cargar | 0023H | Medio | 0023F, infra scan exists |

### Fase 3 — Documentos de transporte
| Prio | Gap | Spec | Esfuerzo | Depende de |
|------|-----|------|----------|------------|
| 10 | Carta porte versionada (editable en ruta) | 0023J | Alto | Fase 2 |
| 11 | Carta porte interna/externa | 0023J-A/B | Medio | 0023J |
| 12 | Firma digital en carta porte | 0023J-C | Medio | 0023J |
| 13 | Albarán operativo (separado de waybill) | 0023K | Alto | 0023J |
| 14 | Numeración por sede | 0023L | Bajo | — |

### Fase 4 — ADR y regulatorio
| Prio | Gap | Spec | Esfuerzo | Depende de |
|------|-----|------|----------|------------|
| 15 | Peso transportado visible en carga (UI) | 0023M | Bajo | — |
| 16 | Umbral 1000 kg ADR | 0023N | Medio | 0023O |
| 17 | Reporte anual ADR | 0023N | Medio | 0023N (umbral) |
| 18 | Equivalencias de transporte | 0023O | Medio | productos |
| 19 | UX ADR + selección vehículo | 0023P | Medio | — |

### Fase 5 — Reportes y cierre
| Prio | Gap | Spec | Esfuerzo | Depende de |
|------|-----|------|----------|------------|
| 20 | Estado de deuda/cobros mínimo | 0023Z | Medio | futura facturación |
| 21 | Consistencia documental | 0023AH | Medio | Fase 3 |
| 22 | Reportes gerenciales | 0023AI | Alto | Fase 3+ |

## Criterio de implementacion

La implementacion de `SPEC 0023` debe respetar estas reglas:

1. no duplicar ownership de `productos`, `crm`, `stock` o futuros modulos de facturacion si no corresponde;
2. no tratar legacy como dependencia tecnica, sino como evidencia funcional madura;
3. no ignorar `Grab2` cuando contradiga simplificaciones previas de specs o documentacion;
4. no considerar cerrado un bloque solo porque exista endpoint si el flujo operativo real sigue incompleto;
5. dividir la implementacion por sub-specs pequeñas, trazables y testeables.
