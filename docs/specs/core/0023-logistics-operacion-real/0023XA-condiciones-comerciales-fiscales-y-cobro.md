# SPEC 0023XA - Condiciones comerciales, fiscalidad y cobro del cliente

## Estado

Implementada

## Contexto

Despues de cerrar `0023D`, `0023R` y `0023S`, el gap restante del dominio cliente ya no esta en la identidad base del cliente sino en su capa comercial, fiscal y de cobro.

El legacy, `Grab2` y `index_clientes.md` describen varias necesidades que se tocan entre si y que en la practica se consumen juntas desde la ficha del cliente:

- forma de pago pactada con el cliente;
- politica de facturacion por cliente;
- datos bancarios para domiciliacion / remesa;
- datos fiscales espanoles e intracomunitarios;
- codigo contable y datos de exportacion;
- precios especiales por cliente;
- presupuesto previo como origen de condiciones comerciales;
- estado de deuda, remesa y cobro pendiente.

Abrir una spec separada por cada punto (`0023X`, `0023AJ`, `0023AK`, `0023AB`, `0023U`, `0023V`, `0023Y`, `0023Z`) ayuda a fragmentar el backlog, pero empieza a esconder que para el usuario final todas esas piezas forman una sola capa funcional: la ficha comercial-fiscal-financiera del cliente.

Esta spec las consolida como una sola lectura de dominio, manteniendo fronteras de ownership claras para no meter todo por error dentro de `crm`.

## Objetivo

Definir un marco unico para implementar la capa comercial, fiscal y de cobro asociada al cliente, separando con claridad:

- que datos maestros viven en `crm`;
- que condiciones consumen `ventas` / `facturacion`;
- que datos de catalogo o referencia cruzan con `productos`;
- que ejecucion transaccional vive en `cobros` / `caja` / remesas;
- que parte queda solo como visibilidad resumida dentro de la ficha del cliente.

## No objetivos

Esta spec NO significa:

- mover todo el modulo de facturacion a `crm`;
- meter remesas completas, asientos contables o conciliacion bancaria dentro del customer core;
- duplicar pricing base de `productos`;
- implementar un ERP contable dentro del plugin `crm`;
- mezclar el owner comercial interno (`0023S`) con politicas de descuento sin permisos claros.

## Fuentes base

- `docs/specs/core/0023-logistics-operacion-real/index_clientes.md`
- `docs/docs-systutor-legacy/modulo_clientes.md`
- `grabaciones/Grab2/hecho/Grabacion Dia 15 marzo con GEMA mostrando su sistema_transcripcion.txt`
- `grabaciones/Grab2/hecho/Grabacion28ENE2025_transcripcion.txt`
- `docs/specs/core/0023-logistics-operacion-real/0023D-cliente-comercial-fiscal-y-direcciones.md`
- `docs/specs/core/0023-logistics-operacion-real/0023R-contactos-y-responsables.md`
- `docs/specs/core/0023-logistics-operacion-real/0023S-gestion-comercial.md`

## Decision de consolidacion

Las sub-areas que antes aparecian como `0023X`, `0023AJ`, `0023AK`, `0023AB`, `0023U`, `0023V`, `0023Y` y `0023Z` pasan a tratarse como capitulos internos de `0023XA`.

Regla:

- `0023XA` no borra las fronteras entre modulos;
- `0023XA` unifica el analisis y el backlog porque todas esas piezas dependen del mismo objeto de negocio: el cliente y sus condiciones operativas de venta/cobro;
- si una seccion crece demasiado en complejidad, podra re-extraerse despues a una sub-spec ejecutable, pero partiendo desde este documento unico.

## Principios de diseno

1. `crm` es owner de los datos maestros del cliente y de sus condiciones base visibles en ficha.
2. `productos` sigue siendo owner del catalogo maestro y del precio base/promocion.
3. `ventas` / `facturacion` consumen condiciones del cliente al emitir presupuesto, pedido, albaran o factura.
4. `cobros` / `caja` son owner del estado transaccional de deuda, cobro, remesa, devolucion y conciliacion.
5. la ficha del cliente puede mostrar resumen financiero/comercial sin convertirse en owner de todo el flujo.
6. no duplicar la misma regla en `crm`, `ventas` y `cobros`.
7. cuando una condicion es solo preferencia o pacto base, vive en `crm`; cuando se vuelve movimiento, vive en el modulo transaccional correspondiente.
8. cuentas por cobrar NO vive en `crm`; `crm` solo puede mostrar resumenes consumidos desde el modulo owner.

## Mapa de ownership

| Tema | Owner principal | Consumidores |
|---|---|---|
| forma de pago base del cliente | `crm` | `ventas`, `facturacion`, `cobros` |
| politica de facturacion (`por_operacion`, `mensual`, anticipada, etc.) | `crm` | `facturacion` |
| datos bancarios maestros del cliente | `crm` | `cobros`, `remesas`, `facturacion` |
| flags fiscales del cliente | `crm` | `facturacion`, exportacion contable |
| codigo contable del cliente | `crm` | exportacion contable / facturacion |
| precio base del producto | `productos` | `ventas`, `crm` resumen, `facturacion` |
| precio especial por cliente | `crm` + `productos` (contrato comercial cruzado) | `ventas`, `facturacion` |
| presupuesto/cotizacion | futuro `ventas` / `comercial` | `crm`, `facturacion` |
| deuda, cobro, remesa, devolucion | `cobros` / `caja` | `crm` resumen |

## Regla explicita sobre cuentas por cobrar

`crm` NO es owner de cuentas por cobrar.

Eso significa:

- `crm` no persiste facturas vencidas;
- `crm` no persiste saldo pendiente;
- `crm` no persiste pagos parciales;
- `crm` no persiste remesas emitidas o devueltas;
- `crm` no persiste estado de cobranza transaccional.

El owner correcto de esa informacion es un futuro modulo de `cobros` / `cobranzas` / `facturacion`, segun como se termine nombrando en el monorepo.

`crm` solo puede:

- guardar condiciones maestras que afectan el cobro, como forma de pago base o datos bancarios maestros;
- consumir un resumen de lectura del estado financiero del cliente;
- mostrar ese resumen dentro de la ficha del cliente sin apropiarse del dominio transaccional.

Regla de arquitectura:

- si el dato nace de una factura, vencimiento, pago, remesa o devolucion, NO vive en `crm`.
- si el dato describe una preferencia, condicion pactada o metadata base del cliente, SI puede vivir en `crm`.

## Alcance funcional

### 1. Formas de pago y politica de facturacion

El sistema debe modelar como dato base del cliente:

- forma de pago por defecto;
- dias o regla de vencimiento;
- modalidad de cobro base (`CONTADO`, `TRANSFERENCIA`, `REMESA`, etc.);
- politica de facturacion (`por_operacion`, `mensual`, `anticipada`, otra definida);
- posibilidad de distinguir remesa de otras formas aunque comparta dias.

Reglas:

- esto no registra el cobro real; registra la condicion base pactada;
- `crm_payment_terms` puede sobrevivir, pero debe enriquecerse para expresar semantica real, no solo un catalogo plano de dias;
- `billing_type` no debe quedarse como string decorativo; debe tener contrato funcional claro.

### 2. Datos bancarios del cliente

Debe soportarse al menos:

- titular;
- banco;
- IBAN / numero de cuenta;
- BIC/SWIFT opcional;
- estado activo/inactivo;
- uso para remesa/domiciliacion;
- notas y trazabilidad de cambios.

Reglas:

- los datos bancarios maestros del cliente viven en `crm`;
- una remesa emitida, devuelta o conciliada NO vive en `crm`;
- debe permitirse historico o al menos cambio seguro de cuenta principal;
- el modulo de remesas consume estos datos, no los redefine.

### 3. Fiscalidad espanola e intracomunitaria

Debe modelarse explicitamente:

- NIF / CIF / NIE con semantica visible;
- flag intracomunitario;
- clave de operacion fiscal;
- cliente exento;
- recargo de equivalencia;
- criterio de caja;
- otros flags tributarios minimos que afecten documento o exportacion.

Reglas:

- no toda la logica fiscal tiene que vivir en CRM, pero los atributos base del cliente si;
- si un valor afecta la factura o el fichero de exportacion, debe existir como dato maestro consumible;
- `is_exempt` actual no alcanza por si solo para cubrir la casuistica espanola.

### 4. Codigo contable y exportacion base

Debe existir un campo explicito de codigo contable del cliente separado de `external_code`.

Reglas:

- `external_code` sigue representando codigo cliente / codigo operativo interno;
- `accounting_code` o equivalente representa el enlace a contabilidad;
- no mezclar ambos conceptos;
- la exportacion contable debe leer este campo sin exigir que CRM sea owner de toda la exportacion.

### 5. Precios especiales por cliente

Debe soportarse una capa minima de condiciones comerciales por cliente y opcionalmente por producto:

- precio fijo especial;
- descuento porcentual;
- vigencia;
- estado activo;
- observacion/origen comercial.

Reglas:

- `productos` sigue siendo owner del precio base;
- la condicion especial del cliente es un override comercial, no un reemplazo del catalogo base;
- la resolucion esperada sigue siendo: tarifa cliente > promocion producto > precio base producto;
- no implementar esto como texto libre dentro de `notes` del cliente.
- este primer corte solo soporta alcance `GLOBAL` o `PRODUCT`; linea/grupo quedan para una evolucion posterior con contrato explicito contra catalogos de `productos`.

### 6. Presupuestos y origen de la condicion comercial

Debe formalizarse que en muchos casos el precio especial nace desde una cotizacion o presupuesto previo.

Esta spec no obliga a implementar ya todo el modulo de presupuestos, pero si deja definidos los enlaces:

- una condicion comercial puede originarse en un presupuesto;
- un presupuesto aceptado puede crear o actualizar una condicion de cliente;
- debe existir trazabilidad del origen comercial cuando aplique.

Regla:

- en este corte `crm` solo guarda una referencia externa al origen comercial si existe; el owner del presupuesto sigue siendo un futuro modulo de `ventas` / `comercial`.

### 7. Remesas y cuentas por cobrar

Esta capa ya es transaccional y no debe vivir completa dentro de `crm`, pero `crm` debe poder mostrar resumen consumido desde el modulo owner.

Debe contemplarse a futuro:

- estado de cobro por cliente;
- remesas pendientes / emitidas / devueltas;
- facturas vencidas;
- proxima fecha de cargo;
- resumen de deuda.

Reglas:

- el owner funcional de esta ejecucion es `cobros` / `caja` / `facturacion`;
- `crm` solo muestra resumen y contexto del cliente;
- no meter ledger de cobro dentro de `crm_customers`.
- no crear tablas `crm_*` para deuda, vencimientos, pagos, remesas o devoluciones.

## Datos propuestos

### `crm_customers`

Mantener y reforzar:

- `external_code`
- `payment_term_code`
- `billing_type`
- `is_exempt`

Agregar o formalizar:

- `accounting_code` nullable
- `is_intracommunity` boolean
- `fiscal_operation_key` nullable
- `tax_regime_code` nullable
- `equivalence_surcharge_applicable` boolean
- `cash_criterion_applicable` boolean

### Nueva tabla sugerida: `crm_customer_bank_accounts`

Campos minimos:

- `id`
- `tenant_id`
- `customer_id`
- `bank_name`
- `account_holder`
- `iban`
- `bic_swift` nullable
- `is_primary`
- `is_active`
- `notes` nullable
- `created_at`
- `updated_at`

### Nueva tabla sugerida: `crm_customer_pricing_terms`

Campos minimos:

- `id`
- `tenant_id`
- `customer_id`
- `product_id` nullable
- `scope_type` (`PRODUCT`, `GLOBAL`)
- `pricing_mode` (`FIXED_PRICE`, `PERCENT_DISCOUNT`)
- `fixed_amount` nullable
- `discount_percent` nullable
- `currency` nullable
- `valid_from`
- `valid_to` nullable
- `source_quote_ref` nullable
- `approved_by` nullable
- `is_active`
- `notes` nullable
- `created_at`
- `updated_at`

Reglas:

- si `scope_type = PRODUCT`, `product_id` es obligatorio;
- si `pricing_mode = FIXED_PRICE`, `fixed_amount` es obligatorio;
- si `pricing_mode = PERCENT_DISCOUNT`, `discount_percent` es obligatorio;
- no resolver aqui el precio final; esa resolucion la consume `ventas` / `facturacion`.
- `source_quote_ref` es solo referencia externa legible; no implica FK dura mientras no exista modulo owner de presupuestos.

## API esperada

### CRM base

- `GET /customers/{id}` debe poder exponer condiciones comerciales/fiscales resumidas.
- `PUT /customers/{id}` debe permitir actualizar campos maestros de esta capa segun permisos.

### Formas de pago

- `GET /catalog/payment-terms`
- `POST /catalog/payment-terms` o equivalente administrativo si se abre gestion editable
- `PUT /customers/{id}/commercial-profile` o equivalente para actualizar forma de pago / billing policy

### Datos bancarios

- `GET /customers/{id}/bank-accounts`
- `POST /customers/{id}/bank-accounts`
- `PUT /bank-accounts/{id}`
- `DELETE /bank-accounts/{id}`

### Precios especiales

- `GET /customers/{id}/pricing-terms`
- `POST /customers/{id}/pricing-terms`
- `PUT /pricing-terms/{id}`
- `DELETE /pricing-terms/{id}`

### Cobro resumido

- `GET /customers/{id}/financial-summary` en el futuro modulo owner de `cobros` / `facturacion`

Regla:

- `crm` no es owner de este endpoint;
- `crm` puede consumir y mostrar este resumen en ficha cuando el modulo owner exista.
- si se expone una vista embebida en CRM, debe ser una proyeccion de lectura, no una fuente de verdad independiente.

## Frontend esperado

La ficha del cliente debe mostrar, en tabs o bloques separados:

- perfil comercial basico;
- forma de pago y politica de facturacion;
- bloque fiscal;
- datos bancarios;
- condiciones especiales / precios especiales;
- resumen de cobro / deuda consumido desde modulo owner cuando exista.

Reglas UX:

- no mezclar contactos, owners comerciales, fiscalidad y precios en un solo formulario caotico;
- diferenciar claramente datos maestros de cliente vs estados transaccionales;
- si un dato viene de otro modulo, mostrarlo como resumen o lectura, no como owner silencioso.

## Permisos

Minimo sugerido:

- `crm.customer.read`
- `crm.customer.update`
- `crm.financial.read`
- `crm.financial.manage`
- `crm.pricing.read`
- `crm.pricing.manage`

Regla:

- cuentas bancarias, perfil financiero/fiscal ampliado y pricing especial NO deben colgar solo de `crm.customer.update`.
- este documento adopta permisos dedicados como decision por defecto para datos sensibles.

## Eventos

Eventos sugeridos:

- `crm.customer.financial_profile_updated`
- `crm.customer.bank_account_added`
- `crm.customer.bank_account_updated`
- `crm.customer.bank_account_removed`
- `crm.customer.pricing_term_added`
- `crm.customer.pricing_term_updated`
- `crm.customer.pricing_term_removed`

## Migraciones

Minimo esperado:

1. ampliar `crm_customers` con campos fiscales/comerciales faltantes;
2. crear `crm_customer_bank_accounts`;
3. crear `crm_customer_pricing_terms`;
4. decidir si `crm_payment_terms` sigue seeded o pasa a catalogo editable con mejor semantica.
5. actualizar `docs/contracts/crm-api.md` junto con la implementacion; la spec no debe divergir del contrato publicado.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Meter cobros completos dentro de CRM | alto | mantener ownership transaccional fuera de CRM |
| Duplicar pricing base de productos | alto | dejar precio base en `productos` y solo overrides aqui |
| Mezclar `external_code` con codigo contable | medio/alto | separar campo explicitamente |
| Hacer una mega UI sin fronteras | medio | dividir frontend por bloques funcionales |
| Consolidar demasiado y perder ejecutabilidad | medio | usar capitulos internos y cortar implementaciones por fases |

## Fases recomendadas

### Fase 1 - Customer financial profile minimo

- enriquecer forma de pago y billing policy;
- agregar fiscalidad espanola minima en `crm_customers`;
- agregar `accounting_code`.

### Fase 2 - Datos bancarios

- tabla y CRUD de cuentas bancarias;
- cuenta principal por cliente;
- lectura usable desde futura remesa.

### Fase 3 - Precios especiales

- tabla y CRUD de condiciones especiales;
- integracion de lectura con `productos` / `ventas`.

### Fase 4 - Presupuesto y cobro resumido

- enlace a presupuesto origen;
- resumen de deuda / remesa consumido desde modulo owner.

## Criterios de aceptacion

1. la ficha del cliente puede representar de forma coherente su perfil comercial, fiscal y financiero sin mezclar ownerships;
2. la forma de pago del cliente deja de ser un string pobre y pasa a tener semantica utilizable por otros modulos;
3. el cliente puede tener datos bancarios propios sin meter remesas completas en CRM;
4. el sistema soporta flags fiscales espanoles reales como intracomunitario, recargo de equivalencia, criterio de caja y clave de operacion;
5. el cliente puede tener condiciones especiales de precio sin duplicar el precio base del catalogo de `productos`;
6. el codigo contable queda separado del codigo cliente;
7. la futura capa de cobros puede consumir estos datos sin volver a modelarlos desde cero.

## Relacion con sub-specs previas

Para efectos de backlog y lectura:

- `0023X` -> absorbida por `0023XA` capitulo 1
- `0023AJ` -> absorbida por `0023XA` capitulo 2
- `0023AB` -> absorbida por `0023XA` capitulo 3
- `0023AK` -> absorbida por `0023XA` capitulo 4
- `0023U` -> absorbida por `0023XA` capitulo 5
- `0023V` -> absorbida por `0023XA` capitulo 6
- `0023Y` -> absorbida por `0023XA` capitulo 7
- `0023Z` -> absorbida por `0023XA` capitulo 7

Si en ejecucion alguna de esas areas necesita volverse una spec implementable independiente, debe declararse como corte derivado de `0023XA`, no como documento desconectado.
