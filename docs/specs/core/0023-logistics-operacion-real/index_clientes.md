# SPEC 0023 — Index Clientes

## Estado

**CERRADA** — 2026-07-04

## Propósito

Este documento separa el analisis exclusivo del modulo de clientes antes de abrir las sub-specs de implementacion.

Su funcion es responder una pregunta concreta:

- como esta hoy `crm` frente a la operacion real descrita en `Grab2` y frente al legacy documentado.

No define aun la implementacion final completa.

Primero ordena:

- que ya existe;
- que existe parcialmente;
- que falta;
- que pertenece a `crm`;
- que pertenece a `logistics`;
- que probablemente pertenece a un modulo futuro de facturacion/cobros/comercial.

## Fuentes base

- `docs/specs/core/0013-crm-plugin.md`
- `plugins/crm/README.md`
- `plugins/crm/docs/modifying-crm.md`
- `docs/docs-systutor-legacy/modulo_clientes.md`
- `grabaciones/Grab2/` y sus transcripciones

## Conclusion general

El CRM nuevo ya resolvio el vacio estructural mas grave:

- ya no dependemos solo de `customer_name` libre;
- ya existe `customer_id` real;
- ya existe cliente formal con documento, direccion y contactos.

Pero frente a la operacion real descrita por el cliente en `Grab2`, el modulo todavia esta corto en cuatro capas criticas:

1. capa comercial;
2. capa fiscal espanola real;
3. capa bancaria y de remesas;
4. capa de cliente operativo multi-establecimiento.

## Lo que ya existe hoy en CRM

- cliente formal en `crm_customers`
- `legal_name`
- `commercial_name`
- `document_type_code`
- `document_number`
- `country_code`
- `email`, `phone`, `mobile`
- direccion fiscal
- direcciones adicionales
- contactos
- validacion fiscal multi-pais base
- catalogo de tipos de documento
- catalogo de formas de pago
- integracion con `logistics` via `customer_id`

## Lo que Grab2 exige por encima del estado actual

- busqueda de cliente por mas criterios operativos
- nombre fiscal vs nombre comercial vs establecimiento real
- responsable que recibe en punto de entrega
- agente/comercial/supervisor
- forma de pago operativa y vencimientos
- datos bancarios e IBAN
- remesas y devoluciones
- codigo contable
- intracomunitario / recargo / criterio de caja / exentos
- precios especiales por cliente
- condiciones comerciales persistentes

## Tabla maestra de clientes

| Tema | Hallazgo de Grab2 | Legacy documentado | CRM nuevo | Estado comparado | Gap exacto | Owner natural | Sub-spec sugerida |
|---|---|---|---|---|---|---|---|
| Razon social / nombre fiscal | Es el identificador formal principal | Si | Si | Bien | Ninguno estructural | `crm` | `0023D` |
| Nombre comercial | Se usa distinto al fiscal y es importante para operacion | Si | Si | Bien parcial | Mejorar busqueda y visibilidad | `crm` | `0023D` |
| Busqueda por nombre fiscal | Necesaria | Si | Parcial | Parcial | Afinar buscador real | `crm` | `0023D` |
| Busqueda por nombre comercial | Necesaria | Si | Parcial | Parcial | Afinar buscador real | `crm` | `0023D` |
| Busqueda por telefono | Necesaria para oficina | Si | Bajo | Gap medio | Agregar criterio operativo de busqueda | `crm` | `0023D` |
| Busqueda por poblacion/pueblo | Necesaria para ubicar cliente cuando no recuerdan nombre exacto | Si | Bajo | Gap medio | Agregar criterio operativo de busqueda | `crm` | `0023D` |
| Busqueda por CIF/NIF/DNI | Necesaria | Si | Parcial | Parcial | Mejorar UX y filtros | `crm` | `0023AB` |
| Documento fiscal multi-pais | Necesario | Si | Si | Bien base | Afinar Espana | `crm` | `0023AB` |
| NIF/CIF/NIE Espana | Necesario y con semantica real | Si | Parcial | Parcial-bajo | Validacion y reglas espanolas mas finas | `crm` | `0023AB` |
| Codigo cliente / codigo interno | Importa para operacion y contabilidad | Si | Parcial (`external_code`) | Parcial | Confirmar semantica y uso visible | `crm` | `0023D` |
| Codigo contable | Se usa para exportar y enlazar contabilidad | Si | No | Gap fuerte | Campo y contrato de exportacion | `crm` + futuro facturacion | `0023AK` |
| Cliente fiscal vs establecimiento | Una empresa puede tener varios puntos/establecimientos | Si | Parcial | Parcial | Unificar mejor modelo `crm` + `delivery_points` | `crm` + `logistics` | `0023D` |
| Direccion fiscal | Necesaria | Si | Si | Bien | Ajustes menores | `crm` | `0023D` |
| Direccion de entrega | Necesaria y distinta de la fiscal | Si | Parcial | Parcial | Aterrizarla operativamente | `crm` + `logistics` | `0023D` |
| Varias sedes | Necesarias | Si | Parcial | Parcial | Modelo mas rico por establecimiento | `crm` | `0023D` |
| Contacto por sede | Necesario | Si | Si | Bien | Contactos vinculados a direccion, con proposito y primary por scope | `crm` | `0023R` |
| Responsable que recibe | Existe operativamente, aunque no siempre se use | Si | Si | Bien | Contacto con rol, telefono, email vinculado a direccion | `crm` + `logistics` | `0023R` |
| Varios responsables | Existe en negocio real | Si | Si | Bien | Multiples contactos por cliente con filtros por sede y proposito | `crm` | `0023R` |
| Agente comercial asignado | Necesario | Si | Si | Bien | Owner comercial por cliente/establecimiento con roles AGENT/SUPERVISOR | `crm` | `0023S` |
| Supervisor de zona | Aparece en operacion | Parcial | Si | Bien | Modelo comercial minimo con primary por scope | `crm` | `0023S` |
| Ruta asociada al cliente | Importa para reparto | Si | Parcial | Parcial | Definir frontera CRM vs logistics | `logistics` con referencia a `crm` | `0023D` |
| Coordenadas / geolocalizacion | Utiles para reparto y nuevas altas | Si | Si base | Bien parcial | Mejor captura operativa | `crm` | `0023T` |
| Forma de pago base | Critica | Si | Si base | Bien parcial | Ampliar semantica y uso | `crm` | `0023X` |
| Facturacion mensual vs por operacion | Critica | Si | Parcial (`billing_type`) | Parcial | Integrar con modulo futuro | `crm` + futuro facturacion | `0023X` |
| Credito / contado | Critico | Si | Parcial | Parcial | Afinar operativamente | `crm` | `0023X` |
| Transferencia / 15 / 30 / 60 / 90 dias | Critico | Si | Bajo/parcial | Gap fuerte | Catalogo y semantica real | `crm` | `0023X` |
| Remesa bancaria | Critica | Si | No | Gap muy fuerte | Modelo y exportacion bancaria | futuro facturacion/cobros | `0023Y` |
| Devolucion de remesa | Critica para operacion | Si | No | Gap fuerte | Seguimiento de cobro | futuro cobros | `0023Z` |
| Cuentas por cobrar | Necesarias | Si | No | Gap fuerte | Vista operativa minima por cliente | futuro cobros | `0023Z` |
| Datos bancarios | Necesarios para remesa/domiciliacion | Si | No | Gap muy fuerte | IBAN/banco/cuenta/estado | futuro facturacion/cobros o CRM extendido | `0023AJ` |
| Intracomunitario | Necesario | Si | No fuerte | Gap fuerte | Flags y validaciones | `crm` + facturacion | `0023AB` |
| Recargo de equivalencia | Necesario para algunos clientes | Si | No | Gap fuerte | Modelo tributario | futuro facturacion | `0023AB` |
| Criterio de caja | Necesario para algunos clientes | Si | No | Gap fuerte | Modelo tributario | futuro facturacion | `0023AB` |
| Cliente exento | Necesario para algunos casos | Si | Parcial (`is_exempt`) | Parcial | Integracion real en documentos | `crm` + facturacion | `0023AB` |
| Clave de operacion | Importa para exportacion/contabilidad | Si | No | Gap fuerte | Campo y catalogo fiscal | futuro facturacion | `0023AB` |
| Precio especial por cliente | Necesario | Si | No | Gap muy fuerte | Modelo de condiciones comerciales | `crm` + `productos` o modulo comercial | `0023U` |
| Descuento porcentual por cliente | Necesario | Si | No | Gap fuerte | Regla comercial | `crm` + `productos` | `0023U` |
| Precio fijo por cliente | Necesario | Si | No | Gap fuerte | Regla comercial | `crm` + `productos` | `0023U` |
| Presupuesto previo | Se usa para fijar precio y luego convertirlo en venta | Si | No | Gap fuerte | Workflow presupuesto -> aceptacion -> condicion | futuro comercial/facturacion | `0023V` |
| Restricciones por rol comercial | No cualquiera puede fijar cualquier precio | Si | No | Gap fuerte | Permisos comerciales | futuro comercial | `0023V` |

## Lectura de prioridad

### Prioridad alta

1. `0023D` Cliente comercial/fiscal y direcciones — implementada
2. `0023R` Contactos y responsables — implementada
3. `0023S` Gestion comercial — implementada
4. `0023XA` Condiciones comerciales, fiscalidad y cobro del cliente — implementada
5. `0023XB` Frontend de condiciones comerciales — implementada

### Nota de consolidacion

Para reducir fragmentacion artificial del backlog, las lineas que antes aparecian como:

- `0023X` Formas de pago
- `0023AJ` Datos bancarios
- `0023AK` Codigo contable y exportacion base
- `0023AB` Fiscal Espana
- `0023U` Precios especiales por cliente
- `0023V` Presupuestos
- `0023Y` Remesas
- `0023Z` Cuentas por cobrar

se consolidan en `0023XA`, manteniendo dentro del documento la separacion de ownership entre `crm`, `productos`, `ventas`, `facturacion` y `cobros`.

## Criterio de implementacion

Antes de tocar codigo, este index debe responder siempre:

1. que parte pertenece realmente a `crm`;
2. que parte es operacion diaria de `logistics`;
3. que parte ya es dominio de facturacion/cobros y no debe mezclarse por accidente en el customer core.

La regla principal es:

- `crm` es dueno de la identidad, contacto, direcciones, documento fiscal y estado base del cliente;
- `logistics` es dueno de los puntos de entrega y operacion diaria de reparto;
- precios especiales, remesas, cuentas por cobrar y exportaciones contables no deben mezclarse por accidente dentro del customer core, aunque ahora se lean de forma consolidada en `0023XA`.
