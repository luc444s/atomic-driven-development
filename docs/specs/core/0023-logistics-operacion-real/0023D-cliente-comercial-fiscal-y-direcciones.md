# SPEC 0023D — Cliente comercial, fiscal y direcciones

## Estado

Cerrada — 2026-07-04

## Nota de cierre

`0023D` se considera cerrada como spec de fortalecimiento del customer core para:

- identidad fiscal y comercial del cliente;
- busqueda operativa multi-criterio;
- direcciones base separadas por proposito;
- contactos base enriquecidos;
- visualizacion conjunta de cliente, direcciones y delivery points relacionados;
- frontera CRM vs logistics suficientemente explicita para esta etapa.

El cierre de esta spec **no** significa que todo el dominio cliente este terminado.

Quedan deliberadamente fuera y se mantienen como trabajo posterior:

- `0023R` contactos y responsables avanzados por sede / contexto operativo;
- `0023S` gestion comercial;
- `0023X` formas de pago con semantica mas rica;
- `0023AB` fiscalidad espanola ampliada;
- specs futuras de cobros, precios especiales y datos bancarios.

Regla de lectura a partir de este punto:

- cuando haya contradiccion entre el modelo inicial de `SPEC 0013` y el cierre documental/codigo de esta spec, para este alcance prevalece `0023D`.

## Contexto

El plugin `crm` ya resolvio el vacio estructural basico del proyecto:

- existe `crm_customers`;
- existe `customer_id` real para integracion con `logistics`;
- existen documento fiscal, direccion fiscal, contactos y direcciones adicionales.

Sin embargo, el contraste entre:

- `docs/specs/core/0013-crm-plugin.md`;
- `docs/docs-systutor-legacy/modulo_clientes.md`;
- las transcripciones de `grabaciones/Grab2/`;

muestra que el modelo actual todavia no representa bien al cliente real del negocio.

En la operacion real descrita por el cliente aparecen necesidades que hoy estan solo parcial o implicitamente cubiertas:

- nombre fiscal y nombre comercial claramente diferenciados;
- busqueda por multiples criterios operativos;
- varios establecimientos por empresa;
- direccion fiscal separada de direccion de entrega;
- responsables y contactos ligados al punto correcto;
- vinculacion real entre cliente, establecimiento, reparto y operacion diaria.

Esta spec abre el primer corte fuerte del dominio de clientes dentro de `SPEC 0023`.

## Objetivo

Fortalecer el modelo de cliente para que represente correctamente la realidad comercial y fiscal del negocio antes de abordar:

- contactos avanzados;
- ownership comercial;
- precios especiales;
- formas de pago complejas;
- remesas y cobros.

El resultado esperado es un cliente que pueda operar correctamente como base de:

- facturacion;
- reparto;
- puntos de entrega;
- contratos;
- busqueda operativa en oficina;
- futura integracion contable.

## No objetivos

Esta spec NO cubre aun:

- datos bancarios completos;
- remesas bancarias;
- cuentas por cobrar;
- precios especiales por cliente;
- presupuestos;
- contratos de envases;
- fiscalidad espanola avanzada completa (`recargo de equivalencia`, `criterio de caja`, etc.);
- ownership comercial detallado por agente/supervisor;
- optimizacion de rutas por geolocalizacion.

Esos temas salen a sub-specs propias.

## Problema actual

Hoy el CRM nuevo esta bien como customer core, pero todavia se queda corto frente a `Grab2` en estos puntos:

1. el cliente real no es solo una razon social con direccion fiscal;
2. una empresa puede tener varios establecimientos operativos;
3. el nombre comercial importa tanto como el fiscal para busqueda y operacion;
4. la oficina busca clientes por telefono, poblacion, CIF/NIF y nombre comercial;
5. los puntos de entrega y la direccion fiscal no deben confundirse;
6. los responsables por establecimiento no siempre coinciden con la entidad fiscal;
7. el modelo actual entre `crm` y `lg_delivery_points` aun no se siente como un solo flujo coherente.

## Principios de diseno

1. `crm` sigue siendo owner de la identidad del cliente.
2. `logistics` sigue siendo owner de la operacion diaria del punto de entrega.
3. la direccion fiscal no debe mezclarse con el punto operativo de reparto.
4. debe existir un camino simple para alta minima y un camino rico para completar la ficha.
5. la busqueda operativa debe responder a como trabaja oficina, no solo a como esta disenada la BD.
6. no se deben duplicar estructuras entre `crm_customer_addresses` y `lg_delivery_points` sin una razon clara.

## Alcance funcional

### 1. Identidad del cliente

El cliente debe soportar claramente:

- nombre fiscal / razon social (`legal_name`);
- nombre comercial (`commercial_name`);
- codigo externo / codigo cliente;
- documento fiscal segun pais;
- estado activo/inactivo.

### 2. Establecimientos del cliente

Debe quedar formalizado que una empresa puede tener:

- un domicilio fiscal;
- uno o varios establecimientos operativos;
- uno o varios puntos de entrega asociados a esos establecimientos.

No todos los establecimientos son necesariamente puntos de entrega logisticos activos, pero si deben poder existir como parte de la ficha del cliente.

### 3. Direcciones separadas por proposito

Deben distinguirse al menos estos propositos:

- `FISCAL`
- `COMERCIAL`
- `ENTREGA`
- `OTRA`

La direccion fiscal sigue siendo parte del customer core.

Los puntos de entrega usados en reparto siguen siendo operados por `logistics`, pero deben poder referenciar correctamente la estructura del cliente.

### 4. Contactos base enriquecidos

El customer core debe soportar contactos base del cliente con suficiente riqueza para no depender solo de un par `tipo`/`valor` generico.

Como minimo debe poder guardar:

- persona o nombre visible del contacto;
- etiqueta opcional de uso rapido;
- cargo / rol;
- telefono;
- email;
- vinculacion opcional a una direccion base del mismo cliente.

Reglas:

- estos contactos pertenecen al cliente como entidad comercial/fiscal, no al reparto diario;
- un contacto base puede tener telefono y email simultaneamente;
- `contact_type` puede sobrevivir como clasificacion liviana o compatibilidad, pero no debe gobernar por si solo la UX;
- el responsable que recibe una entrega concreta sigue siendo parte del punto operativo en `logistics`.

Este cierre absorbe el **primer corte imprescindible** de lo que luego podra ampliarse en `0023R`, sin esperar una sub-spec nueva para dejar de depender del modelo plano heredado de `0013`.

### 5. Busqueda operativa

La busqueda de cliente debe soportar, como minimo:

- nombre fiscal;
- nombre comercial;
- documento fiscal;
- telefono;
- email;
- ciudad/poblacion/localidad;
- codigo externo.

No todos los criterios tienen que verse como columnas visibles, pero si deben entrar en el filtro de busqueda.

### 6. Alta minima y enriquecimiento posterior

Debe existir un flujo minimo para crear rapido un cliente nuevo con:

- nombre fiscal;
- nombre comercial opcional;
- documento fiscal;
- telefono o email opcional;
- direccion minima.

Y luego enriquecer:

- establecimientos;
- contactos;
- delivery points;
- datos comerciales/fiscales adicionales.

## Ownership CRM vs Logistics

### Vive en CRM

- identidad fiscal/legal del cliente;
- nombre comercial;
- documento fiscal;
- direcciones base del cliente;
- contactos base del cliente;
- metadata de establecimiento no operativa;
- busqueda del cliente.

### Vive en Logistics

- delivery day;
- visit day;
- zone_id;
- warehouse_id;
- time_window;
- instructions;
- demand_units;
- demand_weight_kg;
- service_time_min;
- ruta operativa;
- agente operativo de reparto;
- relacion diaria con carga, agenda y salida.

### Regla de integracion

`lg_delivery_points` sigue vivo, pero debe representar un punto operativo del cliente, no reemplazar la ficha del cliente.

## Cambios de datos propuestos

### `crm_customers`

Mantener y endurecer:

- `external_code`
- `legal_name`
- `commercial_name`
- `document_type_code`
- `document_number`
- `country_code`
- `email`
- `phone`
- `mobile`
- `billing_type`
- `fiscal_address_id`

Agregar si aun no existe de forma explicita usable en frontend/contrato:

- `search_alias` opcional o derivado de `commercial_name` para busqueda operativa si hace falta;
- `customer_status` si el booleano `is_active` no basta para representar estados futuros;
- `notes` ya existe y debe mantenerse visible.

### `crm_customer_addresses`

Endurecer uso de:

- `address_type`
- `label`
- `line1`
- `city`
- `state`
- `district`
- `postal_code`
- `country_code`
- `latitude`
- `longitude`
- `gps_link`
- `contact_name`
- `contact_phone`
- `contact_email`

Agregar si hace falta:

- `is_operational_site` boolean para distinguir direcciones que son sede/establecimiento operable aunque no sean aun `delivery_point`.

Nota:

- `contact_name` / `contact_phone` / `contact_email` a nivel address sirven como captura rapida asociada a una direccion concreta;
- no reemplazan la tabla de contactos base del cliente ni la necesidad de personas/canales reutilizables.

### `crm_customer_contacts`

El modelo generico original de `SPEC 0013` (`contact_type` + `value` + `label`) ya no es suficiente para cerrar `0023D`.

Para este corte, los contactos base del cliente deben enriquecerse al menos con:

- `full_name` nullable;
- `label` nullable;
- `role` nullable;
- `phone` nullable;
- `email` nullable;
- `address_id` nullable como FK opcional a `crm_customer_addresses` del mismo cliente;
- `contact_type` mantenido como clasificacion simple o compatibilidad (`PHONE`, `EMAIL`, `OTHER`), pero no como unica fuente semantica del contacto;
- `is_primary`.

Reglas:

- `phone` y `email` dejan de viajar codificados dentro de un `value` generico;
- un mismo contacto puede representar una persona con varios canales, no solo una fila por canal;
- `label` se mantiene como alias corto opcional para oficina;
- si `address_id` existe, debe pertenecer al mismo cliente;
- este modelo sigue siendo **contacto base del cliente**, no responsable operativo por entrega.

Queda fuera de esta spec y se reserva para `0023R`:

- responsables multiples por sede con jerarquia o vigencia;
- contactos puramente operativos por punto de entrega;
- reglas de prioridad mas avanzadas por canal / establecimiento / contexto.

### `lg_delivery_points`

No mover ownership a CRM.

Pero si revisar si debe agregarse o reforzarse:

- referencia semantica al establecimiento/direccion base del cliente si no existe forma clara de vincularlo;
- consistencia de `customer_id` obligatoria;
- snapshot `customer_name` solo de lectura si hace falta por historico.

## Respuestas a decisiones que estaban abiertas

Este bloque fija decisiones usando la evidencia acumulada de `Grab2` y del legacy documentado.

### 1. `establecimiento` sera solo una address enriquecida o entidad propia?

Respuesta: **debe tratarse como entidad propia de negocio, aunque pueda apoyarse en una direccion base**.

Justificacion:

- en legacy existe `Vehiculo_cliente_nuevo` como tabla propia de puntos de entrega / establecimientos;
- no es solo una direccion: tiene contacto, telefono, correo responsable, zona, dia de reparto, agente asignado, sucursal, ventana horaria e instrucciones;
- `Grab2` confirma que una empresa puede tener varias sedes operativas con comportamiento distinto.

Decision:

- en el corto plazo, `crm` mantiene direcciones base del cliente;
- los establecimientos operativos que afectan reparto seguiran representados por una entidad operativa en `logistics` (`lg_delivery_points`), no por una simple `crm_customer_address`;
- mas adelante se puede crear una entidad comercial intermedia de establecimiento si hace falta, pero **esta spec no la crea aun**.

### 2. `delivery_point` debe referenciar una `crm_customer_address`?

Respuesta: **no obligatoriamente en esta etapa**.

Justificacion:

- legacy separaba la persona/cliente de sus puntos operativos de entrega;
- `Grab2` muestra que el punto de entrega tiene dinamica propia y puede diferir de la direccion fiscal o comercial;
- forzar ahora un FK fuerte a una address de CRM puede mezclar customer core con operacion diaria.

Decision:

- `lg_delivery_points` debe seguir referenciando obligatoriamente `customer_id`;
- puede conservar su propia direccion operativa;
- si despues hace falta un enlace opcional a `crm_customer_addresses`, se abre en otra sub-spec, pero no es prerequisito de `0023D`.

### 3. `external_code` sera tambien el codigo contable?

Respuesta: **no debe asumirse eso**.

Justificacion:

- `Grab2` distingue entre codigo cliente/codigo interno y codigo contable;
- el codigo contable aparece como dato especifico para exportar a otro sistema;
- legacy tambien separa conceptos comerciales/fiscales y estructuras de integracion contable.

Decision:

- `external_code` sigue representando codigo externo o codigo cliente general;
- el **codigo contable** debe modelarse como campo aparte en una spec posterior (`0023AK`), no mezclarse dentro de `external_code`.

### 4. `commercial_name` debe ser obligatorio?

Respuesta: **no obligatorio a nivel de base, pero si altamente recomendado a nivel de operacion**.

Justificacion:

- en `Grab2` aparece repetidamente la diferencia entre nombre fiscal y nombre conocido por negocio;
- tambien aparece que algunos casos pequenos pueden operar sin una separacion real y dejar ese dato vacio o igual al nombre fiscal;
- volverlo obligatorio romperia el alta minima en casos donde no existe nombre comercial real.

Decision:

- `commercial_name` sigue siendo nullable;
- en frontend se debe sugerir fuertemente capturarlo;
- si no existe, la UX puede mostrar `legal_name` como fallback para busqueda y visualizacion.

### 5. El responsable que recibe debe ser parte del customer core o del punto operativo?

Respuesta: **del punto operativo**.

Justificacion:

- legacy lo maneja en `Vehiculo_cliente_nuevo` / establecimiento;
- `Grab2` lo describe como algo que puede variar por sede, entrega o contexto;
- no siempre coincide con el representante fiscal del cliente.

Decision:

- CRM puede guardar contactos generales del cliente;
- el responsable que recibe en reparto debe vivir ligado al punto operativo o delivery point.

### 5.b El contacto base del cliente debe seguir modelado como `type/value` generico?

Respuesta: **no como modelo principal**.

Justificacion:

- el negocio real no solo necesita un telefono o un email aislado, sino personas, cargos y relacion con una direccion base;
- el legacy y la operacion muestran que un mismo contacto puede tener mas de un canal;
- obligar a oficina a pensar cada dato como una fila `PHONE` / `EMAIL` degrada la UX y deja corto el contrato.

Decision:

- `crm_customer_contacts` debe evolucionar a contacto base enriquecido;
- `contact_type` puede conservarse como clasificacion ligera o compatibilidad, pero no como driver unico del formulario;
- el responsable operativo de recepcion sigue fuera de este modelo y vive en `logistics`.

### 6. La busqueda por poblacion, telefono y nombre comercial es requerida o solo deseable?

Respuesta: **requerida**.

Justificacion:

- en `Grab2` la oficina lo pide explicitamente como forma real de ubicar clientes;
- depender solo de razon social o documento no refleja el uso diario.

Decision:

- estos criterios se consideran obligatorios para cerrar `0023D`.

### 7. Los datos bancarios deben entrar ya en esta spec?

Respuesta: **no**.

Justificacion:

- son criticos para negocio, pero pertenecen a una capa ya cercana a facturacion/cobros/remesas;
- `SPEC 0013` los dejo fuera deliberadamente;
- meterlos aqui mezclaría customer core con cobro demasiado pronto.

Decision:

- se documentan como dependencia fuerte del roadmap;
- no entran en `0023D`;
- quedan para `0023AJ` y `0023Y`.

## Matriz de campos base para `0023D`

| Campo | Ya existe | Fuente principal | Obligatorio | Owner | Nota |
|---|---|---|---|---|---|
| `legal_name` | Si | Grab2 + legacy + CRM actual | Si | `crm` | Nombre fiscal / razon social |
| `commercial_name` | Si | Grab2 + legacy + CRM actual | No | `crm` | Fallback visual a `legal_name` si esta vacio |
| `external_code` | Si | CRM actual | No | `crm` | No debe confundirse con codigo contable |
| `document_type_code` | Si | legacy + CRM actual | Si | `crm` | Debe afinarse para Espana |
| `document_number` | Si | legacy + CRM actual | Si | `crm` | Debe afinarse para Espana |
| `country_code` | Si | CRM actual | Si | `crm` | Base para validacion fiscal |
| `email` | Si | Grab2 + CRM actual | No | `crm` | Puede ser requerido en ciertos flujos de facturacion |
| `phone` | Si | Grab2 + CRM actual | No | `crm` | Debe entrar en busqueda |
| `mobile` | Si | CRM actual | No | `crm` | Secundario |
| `billing_type` | Si | Grab2 + CRM actual | No | `crm` | Solo base; semantica se amplia despues |
| `fiscal_address_id` | Si | CRM actual | Si para cliente completo | `crm` | No confundir con entrega |
| `notes` | Si | CRM actual | No | `crm` | Mantener visible |
| `crm_customer_contacts.full_name` | Si | Grab2 + legacy + CRM enriquecido | No | `crm` | Persona visible del contacto base |
| `crm_customer_contacts.label` | Si | Operacion oficina + CRM enriquecido | No | `crm` | Alias corto opcional |
| `crm_customer_contacts.role` | Si | Grab2 + legacy | No | `crm` | Cargo / rol de la persona |
| `crm_customer_contacts.phone` | Si | Grab2 + legacy | No | `crm` | Canal directo; entra en UX y contrato |
| `crm_customer_contacts.email` | Si | Grab2 + legacy | No | `crm` | Canal directo; no debe depender de `value` |
| `crm_customer_contacts.address_id` | Si | CRM enriquecido | No | `crm` | Vinculo opcional a direccion base |
| Direcciones `FISCAL` | Si | legacy + CRM actual | Si | `crm` | Base de cumplimiento |
| Direcciones `COMERCIAL` | Parcial | Grab2 + legacy | No | `crm` | Debe reforzarse |
| Direcciones `ENTREGA` | Parcial | Grab2 + legacy | No en CRM core | `logistics` / `crm` coordinado | Operacion diaria |
| `contact_name` por punto | Parcial | Grab2 + legacy | No | `logistics` / `crm` coordinado | Responsable de recepcion |
| `contact_phone` por punto | Parcial | Grab2 + legacy | No | `logistics` / `crm` coordinado | Uso operativo |
| `contact_email` por punto | Parcial | Grab2 + legacy | No | `logistics` / `crm` coordinado | Uso operativo |

## Reglas de migracion inicial

1. no romper clientes ya creados en `crm`;
2. no migrar automaticamente `delivery_points` a direcciones CRM ni viceversa;
3. reforzar primero contrato y frontend antes de intentar reconciliar toda la data historica;
4. si un cliente ya existe sin `commercial_name`, se mantiene valido;
5. si una busqueda necesita `commercial_name` y no existe, usar `legal_name` como fallback;
6. no inventar `codigo contable` ni datos bancarios placeholder en esta spec.

## Checklist de implementacion

1. revisar contrato actual de `crm_customers` y `crm_customer_addresses`
2. confirmar si falta algun campo minimo para `0023D`
3. formalizar contrato enriquecido de `crm_customer_contacts`
4. ampliar backend de busqueda multi-criterio
5. crear o adoptar `Combobox` compartido en core frontend
6. ampliar `CustomerSearchDialog` para criterios operativos reales
7. decidir que flujos usan `Combobox` y cuales usan `SearchDialog`
8. ampliar alta/edicion para dejar clara la diferencia fiscal/comercial
9. revisar detalle de cliente para visualizar mejor direcciones, contactos y establecimientos
10. revisar integracion con `lg_delivery_points` sin duplicar ownership
11. correr tests de CRM
12. correr tests de logistics que dependan de `customer_id`

## API / contrato esperado

### CRM

Se debe garantizar que el contrato de cliente permita:

1. devolver nombre fiscal y comercial;
2. devolver varias direcciones con `address_type`;
3. devolver contactos base enriquecidos (`full_name`, `label`, `role`, `phone`, `email`, `address_id`, `is_primary`);
4. filtrar por busqueda multi-criterio;
5. distinguir claramente la direccion fiscal actual;
6. exponer suficientes datos para que `CustomerSearchDialog` sea util a oficina.

### Logistics

Se debe garantizar que:

1. `lg_delivery_points` siga filtrando por `customer_id` real;
2. el detalle de cliente pueda verse junto a sus delivery points;
3. no se dupliquen responsabilidades de direccion fiscal dentro de `logistics`.

## Frontend esperado

### Dependencia de UI compartida

La implementacion de esta spec necesita una pieza nueva en el core frontend:

- un `Combobox` reusable en `apps/web/src/shared/ui/`.

Esta dependencia queda formalizada en:

- `docs/specs/core/0023-logistics-operacion-real/0023AL-combobox-compartido-core-frontend.md`

Justificacion:

- el `Select` actual solo cubre listas pequenas y cerradas;
- `CustomerSearchDialog` ya cubre el caso modal y remoto;
- entre ambos falta un bloque intermedio para seleccion inline con filtro rapido, que es justo el tipo de interaccion que oficina y formularios de cliente van a necesitar.

Decision:

- no seguir creando selects enriquecidos por modulo;
- crear `Combobox` como bloque compartido del core frontend;
- reservar `SearchDialog` para datasets remotos, multi-columna o modales;
- usar `Combobox` para selecciones inline con filtro textual y lista acotada o mediana.

Regla de uso:

1. `Select`: catalogos pequenos y estables;
2. `Combobox`: seleccion inline filtrable;
3. `SearchDialog`: busqueda modal y mas pesada.

### Lista de clientes

Debe poder buscar por:

- nombre fiscal;
- nombre comercial;
- documento;
- telefono;
- localidad/poblacion.

### Alta / edicion de cliente

Debe mostrar claramente:

- identidad fiscal;
- nombre comercial;
- direccion fiscal;
- direcciones adicionales / establecimientos;
- contactos con persona, cargo, telefono, email y direccion base vinculada cuando exista.

### Detalle de cliente

Debe poder mostrar:

- resumen fiscal;
- resumen comercial;
- direcciones;
- contactos;
- delivery points operativos relacionados.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Mezclar customer core con delivery point operativo | alto | mantener ownership claro entre `crm` y `logistics` |
| Repetir direcciones entre CRM y logistics | alto | definir bien direccion fiscal vs punto de entrega |
| Agregar demasiada complejidad al alta minima | medio | separar alta minima de enriquecimiento posterior |
| Hacer una busqueda sofisticada pero poco util | medio | usar criterios reales de `Grab2` |
| Bloquear implementacion por fiscalidad avanzada | medio | dejar lo fiscal avanzado a `0023AB` |

## Criterios de aceptacion

### Funcionales

1. el cliente puede existir con nombre fiscal y nombre comercial diferenciados;
2. la busqueda permite ubicar clientes por criterios operativos reales;
3. una empresa puede tener varias direcciones/establecimientos sin confundirlos con la direccion fiscal;
4. los contactos base del cliente soportan al menos persona, cargo, telefono y/o email sin depender de un `value` generico como modelo principal;
5. el detalle de cliente muestra direcciones, contactos y puntos operativos relacionados de forma comprensible;
6. `logistics` sigue usando `customer_id` real sin volver a texto libre.

### De ownership

1. CRM sigue siendo owner de identidad, direccion fiscal y contactos base;
2. logistics sigue siendo owner de delivery points y reparto diario;
3. no se crean duplicaciones de dominio innecesarias entre ambos plugins.

### De calidad

1. se actualizan tests CRM y logistics cuando corresponda;
2. se actualiza contrato API si cambia response o filtros;
3. la implementacion no rompe `CustomerSearchDialog` ni integraciones actuales.

## Entregables de esta spec

1. cierre del modelo base de cliente comercial/fiscal;
2. criterios claros de busqueda operativa;
3. cierre del primer gap fuerte de contactos base sin esperar `0023R` completa;
4. frontera CRM vs logistics documentada y reflejada en codigo;
5. base lista para abrir despues:
   - `0023R-contactos-y-responsables`
   - `0023S-gestion-comercial`
   - `0023X-formas-de-pago`
   - `0023AB-fiscal-espana`

## Referencias

- `docs/specs/core/0013-crm-plugin.md`
- `docs/specs/core/0023-logistics-operacion-real/index_clientes.md`
- `docs/docs-systutor-legacy/modulo_clientes.md`
- `plugins/crm/docs/modifying-crm.md`
- `grabaciones/Grab2/`
