---
id: "draft-cilindro-ubicacion-fisica"
title: "Ubicación Física del Cilindro — Dirección de Delivery Point como Ubicación Real"
domain: logistics
module: cilindros
status: en_discusion
---

# SPEC (borrador) - Ubicación Física del Cilindro

## Contexto

Hoy la ubicación de un cilindro se resuelve a nivel **lógico** (`location_type` + `location_id`):

- `get_cylinder_current_location` devuelve `(location_type, location_id)` donde `location_type ∈ {WAREHOUSE, VEHICLE, CUSTOMER}`.
- Se deriva del último evento definitorio en `lg_cylinder_events` (`_LOCATION_DEFINING_EVENTS`: `WAREHOUSE_IN`, `VEHICLE_LOAD`, `CUSTOMER_DELIVERY`, `CUSTOMER_PICKUP`).

El problema: **no aparece la ubicación física real**. Cuando un cilindro se entrega en el domicilio del cliente, el evento guarda solo `location_id = customer_id` (no el punto de entrega ni la dirección). Ver `route_operation_confirmation.py:326`.

La dirección sí existe en el sistema, pero está huérfana del cilindro:

- `lg_delivery_points.address` + `gps_coordinates` + `gps_link` (resources.py:121,141-142).
- `lg_warehouses.address` / `latitude` / `longitude`.

Fuera de alcance: el GPS del `ScanLog` (telemetría del operador) ya no se considera fuente de la ubicación real.

## Frase guía

**Un cilindro entregado en un delivery point debe conocer, de forma atómica, la dirección exacta donde fue dejado, inmune a cambios futuros de ese punto.**

## Objetivo

Que la ubicación de un cilindro se resuelva a contexto de negocio entendible (dónde exacto: dirección + coordenadas), tomando como fuente el **delivery point** de la entrega.

## No objetivos

- no usar el GPS de `ScanLog` como fuente de la ubicación real;
- no modelar posición intra-almacén (estante/bin/slot) por ahora;
- no geocodificar direcciones en esta iteración (queda como opción futura);
- no reescribir el event-sourcing existente de `lg_cylinder_events`.

## Problema exacto

1. `CUSTOMER_DELIVERY` registra `location_id = customer_id`, no el `delivery_point_id`.
2. `LogisticsCylinderEvent` no tiene campo de dirección/gps ni referencia al delivery point.
3. El endpoint `/cylinders/{id}/location` y el summary de traceability devuelven solo tipo+id o texto crudo (`cylinder.location`), no dirección/coordenadas.

## Alcance propuesto (en discusión)

### A. Capturar delivery point en el evento (núcleo)

- Columna `delivery_point_id` (FK `lg_delivery_points.id`, nullable, index) en `lg_cylinder_events`.
- Snapshot denormalizado en el evento: `address`, `gps_lat`, `gps_lng`, `gps_link` → el cilindro conoce atómicamente su dirección exacta el día de la entrega, inmune a cambios futuros del delivery point.
- Requisito: el flujo de confirmación de ruta (`route_operation_confirmation.py`) debe hacer llegar el `delivery_point_id`, hoy pasa solo `customer_id`.

### B. Resolver ubicación enriquecida (lectura)

Extender `cylinder_location.py` para devolver contexto de negocio según tipo:

- `WAREHOUSE` → nombre/código + address + lat/lng (de `lg_warehouses`).
- `VEHICLE` → placa/identificación del vehículo.
- `CUSTOMER` → nombre del cliente + dirección/gps del **snapshot del evento** (fallback: delivery point vivo).

### C. Exponer

- `/cylinders/{id}/location` → `{location_type, location_id, label, address, latitude, longitude}`.
- El summary de traceability usa el mismo resolver (hoy usa `cylinder.location`).

## Decisiones pendientes

1. **Granularidad de entrega**: ¿el cilindro se deja siempre en un `delivery_point` registrado, o a veces en dirección libre/no registrada? Si hay dirección libre, hace falta columna snapshot extra + campo en el flujo de confirmación.
2. **Fuente de verdad**: ¿snapshot en el evento (inmutable, atómico) vs resolver vía join al delivery point vivo (siempre actual)? Tendencia: **snapshot** por el objetivo atómico.
3. **Coordenadas**: ¿basta `delivery_point.gps_coordinates` (coordenadas declaradas) o se necesita geocodificar la dirección cuando el punto no tenga coordenadas?

## Criterios de aceptación (borrador)

- Entregar un cilindro en un delivery point hace que `/location` y la traceability muestren la dirección + coordenadas reales de ese punto.
- Si el delivery point cambia después de la entrega, el cilindro entregado conserva la dirección que tenía al momento de la entrega (snapshot).
- Ninguna vista operativa muestra un ID crudo sin contexto de negocio (Ley de contexto operativo).

## Dominios/modulos tocados

- `plugins/logistics` (backend): modelo `lg_cylinder_events`, servicio `cylinder_location.py`, `cylinders.py`, `route_operation_confirmation.py`, router `traceability.py`.
- Migración Alembic en `plugins/logistics/migrations/`.

## Referencias

- `docs/specs/core/0011-logistics-pilot-module.md`
- `docs/specs/core/0024-1-3-6-seriales-de-envases-en-carga-operativa.md` (patrón de snapshot/verdad operativa)
