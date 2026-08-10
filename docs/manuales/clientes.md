# Guía de uso — Módulo de Clientes (CRM)

**Público:** personal operativo (comerciales, administrativos, contabilidad).
No requiere conocimientos técnicos ni de programación.

**Fuente:** este manual se escribió desde el comportamiento real de la aplicación, no desde diseños teóricos.

---

## ¿Qué es Clientes?

Es el módulo donde se administra la ficha de cada cliente del negocio: datos fiscales, direcciones, contactos, condiciones comerciales, cuentas bancarias y precios.

En el menú lateral, la sección **Clientes** te lleva a la pantalla principal de gestión.

---

## La pantalla principal

Desde aquí ves el catálogo de clientes y creas o editas fichas.

- **Buscar:** escribe nombre fiscal, comercial, documento, teléfono, código o localidad.
- **Nuevo cliente:** botón naranja para dar de alta una ficha.
- Cada fila tiene **Editar** y **Ver**:
  - **Ver** abre la ficha completa del cliente (ficha operativa).
  - **Editar** reabre el formulario base para corregir datos generales.

La lista se pagina (10 por página).

---

## Dar de alta un cliente

Al pulsar **Nuevo cliente** se abre el formulario con dos bloques: **Datos generales** y **Direcciones**.

### Bloque 1 — Datos generales

- **Información fiscal:** país, tipo de documento (RUC/NIF/etc.), número de documento, domicilio fiscal, régimen, exención.
  - El tipo de documento depende del país que elijas.
  - Marcas accesorias: **Cliente exento** (no paga impuestos a aplicar), **intracomunitario**, criterio de caja, recargo de equivalencia.
- **Razón social / nombre:** nombre legal con el que factura.
- **Nombre comercial:** la marca con la que se conoce (opcional).
- **Contacto:** correo, teléfono y móvil del cliente.
- **Condiciones comerciales:**
  - **Forma de pago** (contado, crédito, etc.).
  - **Tipo de facturación:** Por operación / Mensual / Anticipada.
  - **Cliente exento** (casilla).

### Bloque 2 — Direcciones

Se registran una o más direcciones del cliente con tipos:

| Tipo | Para qué |
|---|---|
| **Fiscal** | Domicilio fiscal (obligatorio, se usa para facturar). |
| **Comercial** | Punto habitual de operación. |
| **Entrega** | Dónde se reparte/entrega mercadería. |
| **Otra** | Cualquier otro punto de interés. |

- La primera dirección con tipo **Fiscal** se toma como domicilio fiscal.
- Pulsa **+ Agregar dirección** para añadir más (comercial, entrega, otra).

> Consejo: rellena siempre la **dirección fiscal** completa. Es la que el sistema usa como sede legal del cliente.

Al pulsar **Guardar** se crea el cliente con sus direcciones.

---

## La ficha del cliente (pantalla Ver)

Al pulsar **Ver** se abre el detalle con la información general (lo que ves arriba: datos fiscales, contactos, direcciones) y un bloque de **Acciones** para administrar partes específicas:

| Acción | Para qué sirve |
|---|---|
| **Editar** | Corregir los datos generales del cliente. |
| **Movimientos** | Historial de movimientos de envases del cliente (salta a Logística). |
| **Direcciones** | Añadir, editar o eliminar direcciones; cambiar cuál es la fiscal. |
| **Contactos** | Gestionar personas de contacto (teléfonos, correos, roles). |
| **Gestión comercial** | Asignar agente y supervisor comercial al cliente. |
| **Cuentas bancarias** | Registrar IBAN, titular y banco para domiciliaciones. |
| **Precios especiales** | Condiciones comerciales/pricing propias de este cliente. |
| **Contratos** | Acceso a los contratos de envases del cliente (Logística). |

Aparte, si el cliente tiene **notas**, se muestran al final del bloque de acciones.

### Direcciones (desde la ficha)

- Lista todas las direcciones del cliente.
- Puedes crear, editar y eliminar direcciones.
- Botón para **marcar una dirección como fiscal** (cambia el domicilio fiscal).
> Eliminar una dirección pide confirmación antes de borrarse.

### Contactos

- Teléfonos, correos y personas de contacto.
- Puedes filtrar por dirección vinculada o por propósito del contacto.
- Cada contacto tiene tipo (teléfono/correo/etc.), rol, y si es el principal.

### Gestión comercial

- Asigna **agente** y **supervisor** para atender al cliente.
- Indica la **dirección** de operación y si la asignación es la principal.

### Cuentas bancarias y precios

- **Cuentas:** cuenta de pago, IBAN, titular y banco, para domiciliaciones.
- **Precios especiales:** condiciones comerciales propias del cliente, distintas del precio estándar.

---

## Casos comunes (paso a paso)

### A. Registrar un cliente nuevo
1. **Clientes** → **Nuevo cliente**.
2. Completa datos fiscales y comerciales.
3. Registra al menos la **dirección fiscal**.
4. **Guardar**.

### B. Cambiar el domicilio fiscal
1. Abre el cliente (**Ver**).
2. **Direcciones**.
3. Crea/edita la dirección correcta y márcala como **fiscal**.

### C. Añadir una persona de contacto
1. **Ver** el cliente.
2. **Contactos** → crea un nuevo contacto con teléfono/correo.

### D. Asignar comercial al cliente
1. **Ver** el cliente.
2. **Gestión comercial** → asigna agente y supervisor.

---

## Qué contempla el módulo (v1)

- Ficha fiscal completa por país y tipo de documento.
- Nombre legal y comercial, contactos, condiciones comerciales y forma de pago.
- Múltiples direcciones (fiscal, comercial, entrega, otra) con selección de la fiscal.
- Personas de contacto con rol y filtros.
- Asignación de agente/supervisor comercial.
- Cuentas bancarias (IBAN, titular, banco).
- Precios especiales por cliente.

## Qué NO contempla el módulo (v1)

- **No factura ni cobra:** la emisión de documentos de venta es de otro módulo.
- **No maneja el reparto:** la logística de envases se ve en el módulo Logística (acceso desde **Movimientos**).
- **No almacena contratos comerciales de precio avanzados** más allá de precios especiales básicos; el detalle de cupos/envases vive en Logística (Contratos).

## Límites y advertencias operativas

- El **tipo de documento depende del país**: elige país antes de fijar el documento.
- Asegúrate de registrar una **dirección fiscal completa**; se usa para facturar.
- Eliminaciones vinculadas (direcciones, asignaciones) piden **confirmación** antes de ejecutarse.

---

## Vocabulario básico

| Término | Significado |
|---|---|
| Razón social | Nombre legal del cliente (para facturar). |
| Nombre comercial | Marca con la que se conoce. |
| Domicilio fiscal | Dirección legal del cliente. |
| Forma de pago | Contado, crédito, etc. |
| Tipo de facturación | Por operación, mensual o anticipada. |
| Agente/Supervisor | Comercial que atiende al cliente. |
| IBAN | Código de cuenta bancaria para domiciliación. |