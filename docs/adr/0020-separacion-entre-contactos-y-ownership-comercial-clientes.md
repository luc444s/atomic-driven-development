# ADR 0020 - Separacion entre contactos del cliente y ownership comercial

## Estado

Aceptado

## Contexto

El legacy y `Grab2` usan lenguaje que mezcla varias figuras distintas alrededor del cliente:

- persona de contacto;
- responsable que recibe;
- agente comercial;
- supervisor;
- vendedor;
- usuario operativo del reparto.

Si se modelan todas esas figuras en una sola estructura, el sistema vuelve a mezclar:

- personas externas del cliente;
- ownership interno del negocio;
- operacion diaria de `logistics`.

`0023D` ya cerro el customer core. Para abrir `0023R` y `0023S` sin repetir el caos del
legacy, hace falta una decision arquitectonica previa.

## Decision

SYSTUTOR OSS separa tres capas distintas alrededor del cliente:

1. **Contactos del cliente en CRM**
2. **Ownership comercial interno en CRM**
3. **Responsabilidad operativa diaria en logistics**

### 1. Contactos del cliente en CRM

Se modelan como personas externas vinculadas al cliente o a una direccion/sede.

Ejemplos:

- contacto de facturacion;
- contacto de compras;
- responsable habitual de recepcion;
- contacto de cobranza.

Estos viven en `crm_customer_contacts` y su evolucion se documenta en `0023R`.

### 2. Ownership comercial interno en CRM

Se modela como relacion entre el cliente (o una sede) y usuarios internos del sistema.

Ejemplos:

- agente comercial del cliente;
- supervisor comercial o de zona;
- owner de cuenta.

Esto vive en una estructura separada de asignaciones comerciales y se documenta en `0023S`.

### 3. Responsabilidad operativa diaria en `logistics`

La operacion diaria del punto de entrega sigue en `logistics`.

Ejemplos:

- `agent_user_id` del delivery point;
- quien toma o acepta la carga;
- quien realiza el reparto;
- estado diario de agenda/ruta/recepcion.

Ese ownership operativo no se mueve a CRM.

## Reglas derivadas

1. No usar una sola tabla para contactos externos y owners internos.
2. No usar `agent_user_id` de `logistics` como sustituto del owner comercial CRM.
3. Un contacto puede coincidir con un responsable operativo, pero no se asume que sea la
   misma cosa ni se usa la misma entidad para ambos casos.
4. Un owner comercial siempre referencia `users`; un contacto CRM nunca reemplaza a `users`.
5. La sede/direccion base puede ser el punto comun de integracion entre `0023R` y `0023S`.

## Alternativas descartadas

### A. Una sola tabla para contactos, agentes y supervisores

Descartada porque:

- mezcla actores externos e internos;
- vuelve ambiguo el ownership;
- complica permisos y auditoria;
- replica el desorden conceptual del legacy.

### B. Dejar toda la nocion de agente/responsable en `logistics`

Descartada porque:

- el ownership comercial no pertenece a la operacion diaria;
- CRM necesita saber quien atiende comercialmente una cuenta incluso fuera del reparto;
- pricing, presupuestos y facturacion futura necesitaran owner comercial propio.

### C. Poner agente y supervisor como columnas directas en `crm_customers`

Descartada porque:

- no soporta overrides por sede;
- escala mal si aparece mas de un rol o mas de una asignacion activa;
- hace mas dificil evolucionar hacia ownership mas rico.

## Consecuencias

### Positivas

- queda clara la diferencia entre persona del cliente y usuario interno;
- `0023R` y `0023S` pueden avanzar en paralelo sin pisarse;
- pricing, presupuestos y permisos comerciales tendran una base mas limpia;
- se protege la frontera CRM vs `logistics`.

### Negativas

- aumenta el numero de estructuras del dominio cliente;
- obliga a UX separada para contactos y ownership comercial;
- requiere eventos, pruebas y contrato API adicionales.

## Dependencias

- `0023D` implementada como baseline del customer core;
- `0023R` para contactos y responsables;
- `0023S` para ownership comercial;
- `0003` tenancy y permisos;
- `0005` auditoria y eventos;
- `0009` spec driven development.
