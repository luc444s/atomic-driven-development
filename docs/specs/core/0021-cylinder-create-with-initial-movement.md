# SPEC 0021 — Logistics: Movimiento inicial al crear envase

## Estado

Implementada

## Contexto

Hoy `create_cylinder` (cylinders.py:114) crea `LogisticsCylinder` + `LogisticsCylinderStateLog`, pero no genera ningún `LogisticsMovement` asociado. Esto rompe la trazabilidad de origen del envase: no queda registro de si entró vacío o lleno, de quién proviene ni con qué documento.

`anotacion.md` define que el alta de envase debe hacer dos cosas juntas:

- crear la ficha del cilindro;
- generar el movimiento inicial que documenta su procedencia.

El movimiento debe reflejar:

- si el envase entró **vacío** → procedencia desde cliente;
- si el envase entró **lleno** → procedencia desde proveedor;
- el número de documento de origen (compra, ingreso, etc.).

## Objetivo

Definir un cierre consistente del alta de envase para que, al crear un cilindro, quede trazado su origen operativo con una de dos ramas explícitas:

- alta de envase vacío desde cliente;
- alta de envase lleno desde proveedor.

La spec debe permitir modelar ambas ramas sin tratarlas como variantes triviales del mismo movimiento.

## No objetivos

- No se modifica el flujo de confirmación de movimientos existente (`confirm_movement`);
- No se implementa autocompletado desde producto (gap #2);
- No se elimina `location` del schema (gap #8) — queda para otra spec;
- No se implementa kardex de gas (gap #9);
- No se toca la UI de edición ni las secciones de detalle del envase.
- No se replica literalmente la compra fantasma legacy completa si OSS puede resolver la trazabilidad con una implementación más acotada y consistente.

## Alcance

### Backend

1. El contrato del alta debe modelar primero la semántica funcional, no el código técnico del movimiento.
2. La rama elegida debe poder distinguir al menos:
   - `EMPTY_FROM_CUSTOMER`
   - `FULL_FROM_SUPPLIER`
3. El backend podrá derivar desde esa rama:
   - estado inicial del cilindro;
   - movimiento o movimientos técnicos a persistir;
   - impacto mínimo requerido en stock cuando aplique;
   - ownership inicial;
   - uso de documento relacionado;
   - uso de almacén activo.
4. La implementación debe extraer una helper común para evitar duplicar la lógica de transición + ownership entre alta inicial y confirmación de movimientos.
5. La implementación puede introducir un `movement_type` nuevo para la rama `FULL_FROM_SUPPLIER` si eso evita deformar semánticamente tipos existentes y mantiene la trazabilidad clara.

### Rama A — Vacío desde cliente

1. Requiere `customer_id` obligatorio.
2. Requiere `document_number` obligatorio.
3. Debe dejar trazado que el envase entra vacío desde cliente.
4. Debe crear la ficha del cilindro y registrar su movimiento logístico inicial de ingreso/custodia.
5. La contraparte cliente debe conservar FK real cuando exista (`customer_id`) y puede complementarse con snapshot legible si la implementación lo necesita para lectura rápida.

### Rama B — Lleno desde proveedor

1. Requiere `document_number` obligatorio.
2. No requiere proveedor formal en esta iteración.
3. Debe asumir almacén activo real del usuario como contexto operativo, siguiendo la lectura legacy de `TxtSucursal`.
4. Debe dejar el cilindro en estado inicial equivalente a `LLENADO_OK` como resultado funcional esperado en OSS.
5. Debe tratarse como una rama distinta del caso vacío, porque en legacy el ingreso lleno desde proveedor disparaba un flujo de compra/stock y no un simple movimiento espejo.
6. La implementación OSS no está obligada a replicar la compra fantasma legacy completa, pero sí debe explicitar qué parte de ese comportamiento se conserva y cuál se difiere.
7. En esta iteración no se exige FK formal de proveedor; basta documento relacionado + contexto operativo del almacén.
8. El mínimo obligatorio en OSS para esta rama incluye una contrapartida trazable de stock/gas en el módulo owner `stock`; no alcanza con trazar solo el cilindro como lleno.

### Frontend

1. El formulario de alta debe exponer explícitamente la rama de origen operativo:
   - vacío desde cliente;
   - lleno desde proveedor.
2. El formulario debe pedir `tipo de documento` y `número de documento`.
3. Si la rama es `vacío desde cliente`, debe exigir `customer_id`.
4. El almacén no se elige manualmente si el sistema ya tiene un almacén activo de usuario confiable; ese valor se deriva del contexto operativo.
5. Si el usuario no tiene almacén activo resoluble, el alta no debe continuar y el sistema debe exigir resolver primero el contexto operativo fuera de este flujo.
6. No se simplifica el resto del formulario en esta iteración.

### Flujo resultante

1. Usuario completa formulario y elige la rama operativa del alta.
2. El alta recibe `document_type`, `document_number` y, cuando aplique, cliente.
3. Backend crea la ficha del cilindro.
4. Backend registra el origen operativo según la rama elegida.
5. Si la rama es `FULL_FROM_SUPPLIER`, backend registra además la contrapartida mínima en stock/gas.
6. Backend deja trazabilidad atómica de cilindro + origen.
6. El alta debe persistir una referencia documental legible equivalente a `docafec`, aunque el modelo final no copie literalmente el campo legacy.
7. Respuesta devuelve el cilindro sin necesidad de cambiar esta spec hacia una reescritura completa del submódulo.

## Reglas de negocio

1. El alta debe distinguir dos ramas funcionales explícitas: vacío desde cliente y lleno desde proveedor.
2. `document_type` y `document_number` son obligatorios en ambas ramas.
3. `customer_id` es obligatorio solo para vacío desde cliente.
4. El caso lleno desde proveedor no debe modelarse como un espejo trivial de vacío desde cliente.
5. El estado inicial funcional del caso lleno desde proveedor debe equivaler a `LLENADO_OK`.
6. El almacén operativo del alta corresponde al almacén activo real del usuario y es obligatorio para cerrar la operación.
7. `docafec` o su equivalente moderno puede persistirse como texto libre de referencia operativa; no necesita ser FK a otra entidad en esta iteración.
8. La condición/ownership del envase debe seguir diferenciando propio, cliente, proveedor y garantía.
9. La rama `FULL_FROM_SUPPLIER` puede requerir un `movement_type` distinto del flujo vacío si los tipos existentes no representan correctamente el caso.
10. Solo la rama `FULL_FROM_SUPPLIER` tiene respaldo legacy para disparar un subflujo de stock/compra; las otras ramas no deben heredar ese comportamiento por analogía.
11. El estado inicial del alta debe quedar auditado en un log de estado equivalente al patrón legacy `ALTA CILINDRO` con almacén y observación operativa.
12. Ownership y contraparte no son el mismo concepto: la UI puede mostrar snapshot legible, pero el backend debe distinguir entre FK operativa de persona y condición del cilindro.
13. Si no existe almacén activo resoluble, el alta debe rechazarse con error operativo claro; no se permite `warehouse_id = null` en una operación cerrada de esta spec.
14. La rama `FULL_FROM_SUPPLIER` no se considera completa si no deja una traza consistente tanto en envase como en stock/gas.

## Contrato mínimo esperado

La implementación puede ajustar nombres, pero el contrato funcional del alta debe cubrir como mínimo:

1. `entry_mode` o equivalente con valores semánticos, no códigos legacy crudos.
2. `document_type` y `document_number`, o un campo moderno equivalente que conserve ambos componentes de trazabilidad legible.
3. `customer_id` obligatorio cuando la rama sea vacío desde cliente.
4. `warehouse_id` derivado del contexto activo del usuario.
5. `condition` del envase como dato distinto de la contraparte operativa.

El contrato no debe exponer `IC`/`IP` como obligación del frontend si esos códigos solo sirven como detalle interno de persistencia.

## Permisos

Reutiliza `logistics.cylinder.create`. No se crean permisos nuevos.

## Evidencia legacy relevante

1. `cbsucursal` se usaba en `FrmCatBombonas` como almacén/sucursal real y participaba en el insert del alta.
2. `TxtSucursal` provenía del contexto activo del usuario y se usaba como entero real de almacén.
3. `Checkllenodeprov` resolvía un estado inicial equivalente a `CREADO_LLENO` en el legacy.
4. `Agregastock_Click` para bombonas llenas desde proveedor no hacía solo trazabilidad: creaba movimiento de compra, comprobante, detalle y recálculo de totales.
5. `docafec` se persistía como texto libre en cabecera operativa.
6. `CBcondicion` distinguía semánticamente propio / cliente / proveedor / garantía.
7. `LogEstadoCilindro` persistía el alta con `Estado`, `Usuario`, `AlmacenId`, `Origen="ALTA CILINDRO"` y observación legible.
8. `Tipo=1` correspondía a cliente/garantía y `Tipo=4` a proveedor/propio como discriminante de control/ownership.
9. `InsertarECabeceraPedido` mezclaba FK real de persona (`LBLidProvCte`) con `docafec` texto libre y sucursal real (`TxtSucursal`).
10. `InsertardetallePedido` arrastraba condición, descripción y ubicación como payload operativo.
11. Solo `Checkllenodeprov` disparaba subflujo de compra/stock; `Checkvaciodecli`, `Checkvacioaprov` y `Checkllenoacli` no tenían flujo equivalente.
12. El legacy mezclaba snapshot textual y FK real de persona; OSS debe separar ambos conceptos sin perder trazabilidad.

## Decisiones de reinterpretación OSS

1. OSS conserva la distinción fuerte entre `vacío desde cliente` y `lleno desde proveedor`.
2. OSS no está obligado a copiar `ECabeceraPedido` / `EDetallePedido` ni la compra fantasma literal.
3. OSS sí debe conservar el resultado funcional mínimo del legacy:
   - estado inicial trazable;
   - documento relacionado legible;
   - almacén operativo real;
   - distinción de contraparte/ownership;
   - contrapartida mínima de stock para la rama lleno desde proveedor;
   - atomicidad entre alta y trazabilidad de origen.
4. Si el modelo actual de `logistics` no expresa correctamente `lleno desde proveedor`, se prefiere agregar un tipo o helper explícito antes que deformar semánticamente uno existente.
5. `Checkllenoacli` se considera comportamiento legacy incompleto o no confiable; no debe convertirse en regla funcional por omisión.
6. El legacy `CREADO_LLENO` se reinterpreta en OSS como `LLENADO_OK` porque el modelo actual ya usa `LLENADO_OK` como primer estado estable y operativo de un cilindro lleno en almacén; no se introduce un estado transitorio nuevo solo para copiar nomenclatura legacy.

## Eventos

El evento `logistics.cylinder.created` ya existe y se emite.

Esta spec no obliga todavía a agregar eventos nuevos, pero sí exige que la implementación preserve auditabilidad y trazabilidad del origen operativo.

## Migraciones

`LogisticsMovement` y `LogisticsMovementItem` ya existen, pero esta spec puede requerir:

1. seed o migración de catálogo si se introduce un `movement_type` nuevo para `FULL_FROM_SUPPLIER`;
2. ajustes de contrato/API para exigir `document_type`, `document_number` y contexto de almacén resuelto;
3. ninguna migración estructural adicional mientras la traza documental y el vínculo con stock puedan resolverse con el modelo actual.

## Pruebas

1. Unitaria: alta vacío desde cliente exige `customer_id` y `document_number`.
2. Unitaria: alta lleno desde proveedor exige `document_type` y `document_number`.
3. Unitaria: la rama llena desde proveedor deja estado funcional equivalente a `LLENADO_OK`.
4. Unitaria: la implementación reutiliza helper común para transición + ownership sin duplicar reglas.
5. Integración: el alta deja trazabilidad atómica de cilindro + origen operativo.
6. Integración: el almacén activo del usuario se usa cuando la rama lo requiere.
7. Integración: la referencia documental equivalente a `docafec` queda persistida en forma legible.
8. Integración: las ramas sin `FULL_FROM_SUPPLIER` no disparan por analogía un subflujo de stock/compra.
9. Integración: si no existe almacén activo resoluble, el alta falla con error operativo claro.
10. Integración: `FULL_FROM_SUPPLIER` deja una contrapartida trazable también en `stock` o en su API owner-side equivalente.

## Dependencias

- `anotacion.md` — reglas operativas de envases
- evidencia legacy de `FrmCatBombonas` sobre `TxtSucursal`, `Checkllenodeprov`, `docafec`, `CBcondicion` y `Agregastock_Click`
- `plugins/logistics/backend/services/cylinders.py` — `create_cylinder`
- `plugins/logistics/backend/services/movements.py` — creación de movements
- `plugins/logistics/backend/schemas.py` — `CylinderCreateRequest`
- `plugins/logistics/backend/router.py` — `create_cylinder_endpoint`
