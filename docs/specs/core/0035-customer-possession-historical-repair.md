---
id: "0035"
title: "Reparación Histórica de Posesión Cliente"
domain: logistics
module: envases
status: implementada
extends:
  - docs/specs/core/0034-customer-possession-invariant.md
---

# SPEC 0035 - Reparación Histórica de Posesión Cliente

## Estado

Implementada en demo/test - v1 (2026-07-29)

## Nota de alcance

La reparación histórica ya fue ejecutada sobre la base de prueba/demo actual.

Estado real hoy:

- huérfanos `EN_CLIENTE_*` reparados: `600`
- huérfanos restantes en demo/test: `0`
- estrategia usada en la ejecución realizada:
  - `session`: `0`
  - `contract`: `0`
  - `fallback`: `600`

Importante:

- la coherencia operativa quedó restaurada;
- la verdad histórica exacta no fue recuperable en esos casos;
- por eso esta spec debe leerse como **implementada para demo/test con fallback explícito**, no como reconstrucción histórica perfecta.

## Contexto

`SPEC 0034` fijó correctamente el diagnóstico principal:

- el problema raíz era del backend;
- el seeder amplificó esa debilidad creando muchos cilindros `EN_CLIENTE_LLENO` / `EN_CLIENTE_VACIO` sin ownership;
- el sistema quedó con estados “en cliente” sin poder responder en qué cliente estaban.

Después del endurecimiento del backend, el sistema ya no debe aceptar nuevos casos incoherentes.

Pero la base de datos histórica y de pruebas todavía necesita reparación.

## Frase guía

**Primero se blinda el dominio. Después se repara el histórico.**

## Objetivo

Definir cómo reparar cilindros históricos en `EN_CLIENTE_*` que no tienen ownership válido, sincronizándolos con clientes reales del sistema y dejando una traza explícita de la estrategia usada.

## No objetivos

- no reescribir toda la historia operacional vieja;
- no pretender recuperar verdad histórica exacta cuando la evidencia no existe;
- no mutar silenciosamente datos sin dejar huella de reparación;
- no usar heurísticas opacas sin clasificación explícita de confianza;
- no permitir que la reparación histórica debilite el nuevo invariante de `0034`.

## Alcance

Este slice cubre:

- cilindros históricos en `EN_CLIENTE_LLENO` o `EN_CLIENTE_VACIO` sin ownership;
- sincronización masiva de ownership y `customer_cylinder_ledger`;
- generación de `state_log` mínimo cuando falte;
- limpieza de `session_id` espuria cuando se usó como pseudo-cliente;
- alineación del seeder para que pueda reparar demo data dañada.

No cubre:

- contratos comerciales complejos;
- reconstrucción manual caso por caso de clientes reales perdidos;
- conciliación financiera.

## Decisión de dominio

### 1. La causa raíz se documenta explícitamente

Esta spec declara como verdad:

```text
causa raíz = backend sin invariante
amplificador = seeder
```

La reparación histórica existe porque el sistema permitió datos inválidos, no porque el seed fuera la fuente primaria del diseño.

### 2. El repair debe ser explícito y auditable

Toda reparación histórica debe dejar huella clara de:

- qué cilindro fue reparado;
- qué cliente quedó como vigente;
- qué evidencia o estrategia se usó;
- si fue inferencia fuerte o fallback de demo.

No se permite “arreglar” ownership sin poder saber luego que fue reparado.

### 2.1 Idempotencia convergente obligatoria

Regla nueva:

```text
un cilindro solo puede ser reparado una vez por este proceso
```

Implementación conceptual mínima:

- si ya existe ownership con marca `seed_orphan_repair:*` para ese cilindro, el proceso debe hacer `skip`;
- si ya existe ledger con `source_type` de repair para ese cilindro, el proceso no debe duplicarlo;
- la reejecución del proceso no puede crear múltiples “ownership vigentes reparados” para un mismo cilindro.

Traducción operativa:

```text
repair no puede ser acumulativo
repair debe ser convergente
```

### 3. Estrategias de reconstrucción ordenadas por confianza

La reparación masiva debe intentar, en este orden:

1. **Sesión/ruta**
   - si el cilindro tiene `session_id` y esa sesión resuelve inequívocamente un solo cliente real, usar ese cliente.
2. **Contrato activo**
   - si `product_id + condition` resuelven inequívocamente un solo cliente por contrato activo, usar ese cliente.
3. **Fallback de demo controlado**
   - solo para datos de prueba/demo sin evidencia suficiente;
   - se asigna un cliente real del sistema de forma determinista y distribuida;
   - debe quedar marcado explícitamente como repair de fallback.

### 3.1 Definición formal de “inequívoco”

Una fuente es inequívoca solo si resuelve exactamente un cliente.

Reglas:

- `0` clientes -> inválido
- `1` cliente -> válido
- `>1` clientes -> ambiguo -> no usar

No se permite tratar “el primer cliente encontrado” como evidencia suficiente.

### 4. Si no existe evidencia real, la reparación no debe simular historia exacta

Regla fuerte:

```text
coherencia operativa reconstruida != verdad histórica exacta
```

Cuando la base no contiene evidencia suficiente, el sistema puede restaurar coherencia para demo/pruebas, pero debe marcar que fue una reconstrucción, no historia original recuperada.

### 4.1 Control de fallback

El fallback no puede ser libre.

Regla:

- fallback solo permitido cuando `env in {local, development, test}`;
- o cuando exista un flag explícito equivalente a `allow_fallback=true`;
- en producción, sin evidencia suficiente, el resultado debe ser `NO_REPARABLE`.

### 5. El ownership reparado pasa a ser vigente

Al reparar un cilindro en `EN_CLIENTE_*`, el sistema crea un ownership nuevo que pasa a ser el ownership vigente según la regla de `0034`.

No se edita un registro inexistente ni se reescribe historia anterior.

### 6. `session_id` espurio debe limpiarse

Si un cilindro quedó en `EN_CLIENTE_*` con `session_id` usada solo como pseudo-contexto de cliente y ya no representa custodia operativa válida, esa `session_id` debe limpiarse durante la reparación.

## Control de ejecución

El proceso de reparación debe cumplir:

### 1. Idempotencia

- no duplicar ownership ni ledger;
- no reprocesar cilindros ya reparados.

### 2. Determinismo

- misma entrada -> mismo resultado;
- el mismo cilindro no puede cambiar de cliente entre ejecuciones si el contexto de ejecución no cambió.

### 3. Control de fallback

- fallback deshabilitado por defecto en producción;
- requiere activación explícita fuera de entornos demo/test.

## Reglas de negocio

1. Todo cilindro `EN_CLIENTE_*` sin ownership debe clasificarse como inconsistencia crítica.
2. El repair debe crear ownership vigente para todos los casos reparables.
3. El repair debe crear evidencia en `lg_customer_cylinder_ledger`.
4. Si falta `state_log`, el repair puede crear un log mínimo de reconstrucción.
5. Toda reparación por fallback debe marcarse explícitamente como `fallback`.
6. Un repair no debe dejar `EN_CLIENTE_*` sin cliente real del sistema.
7. Un repair no debe depender de `session_id` como sustituto final de cliente.
8. Un cilindro ya reparado no debe ser reparado nuevamente por el mismo proceso.

## Datos

Entidades afectadas:

- `lg_cylinders`
- `lg_cylinder_ownership`
- `lg_customer_cylinder_ledger`
- `lg_cylinder_state_log`
- `lg_vehicle_sessions`
- `lg_routes`
- `lg_route_stops`
- `lg_delivery_points`
- `lg_cylinder_contracts`

Herramienta principal prevista:

- `apps/api/app/commands/seed_massive.py`

## Migraciones

No requiere migración estructural obligatoria.

La reparación puede ejecutarse como comando o rutina operativa sobre datos existentes.

## Auditoría y observabilidad

La reparación debe dejar trazabilidad explícita en:

- ownership (`notes` o campo equivalente de repair);
- customer ledger (`source_type` específico);
- state log (`origin` de reparación) si hubo que crearlo.

Ejemplo de marcas aceptables:

- `seed_orphan_repair:session`
- `seed_orphan_repair:contract`
- `seed_orphan_repair:fallback`

## Riesgos

1. Algunos casos históricos no tendrán evidencia suficiente y solo podrán repararse con fallback.
2. Un fallback de demo mejora coherencia, pero no representa historia exacta.
3. Si se ejecuta repair en datos productivos sin filtro, puede crear falsa precisión histórica.
4. La reparación debe ser explícitamente idempotente y convergente, no solo “segura”.

## Criterios de aceptación

1. Todo cilindro histórico en `EN_CLIENTE_*` sin ownership queda reparado o explícitamente clasificado como no reparable.
2. La reparación crea ownership vigente coherente con el estado actual del cilindro.
3. La reparación crea ledger de posesión para cilindros reparados.
4. La reparación limpia `session_id` espuria cuando no representa custodia operativa válida.
5. La estrategia usada queda visible en los datos de reparación.
6. El seeder alineado ya no vuelve a crear nuevos huérfanos `EN_CLIENTE_*`.
7. Reejecutar el repair no duplica ownership ni ledger para cilindros ya reparados.
8. Una fuente solo se usa como evidencia cuando resuelve exactamente un cliente.
9. En producción, sin evidencia suficiente y sin flag explícito, el cilindro debe quedar como `NO_REPARABLE`.

## Pruebas requeridas

1. test de integración: cilindro huérfano con sesión/ruta inequívoca -> repair por `session`.
2. test de integración: cilindro huérfano con contrato inequívoco -> repair por `contract`.
3. test de integración: cilindro huérfano sin evidencia suficiente en demo -> repair por `fallback`.
4. test de integración: cilindro reparado queda con ownership vigente y ledger.
5. test de integración: re-ejecutar repair no duplica ownership ni ledger.
6. test de integración: evidencia con más de un cliente -> caso ambiguo, no usar.
7. test de integración: fallback deshabilitado en producción -> caso sin evidencia queda `NO_REPARABLE`.

## Notas para agentes

- no presentar el fallback como verdad histórica exacta;
- reparar primero coherencia, luego explicar el nivel de confianza;
- no esconder la estrategia usada;
- cualquier repair productivo debe diferenciarse claramente del repair de demo.
