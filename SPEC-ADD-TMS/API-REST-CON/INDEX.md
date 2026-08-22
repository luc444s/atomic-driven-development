# API-REST-CON — Índice del cambio grande

Cambio grande: **conectar Python Systutor (Termux) al legacy VB ERP-SYSTUTOR
(Win10) vía REST**, respetando la ley de frontera (Python nunca toca SQL Server;
solo consume `ERP-SYSTUTOR.API`).

Este índice agrupa las A.SPEC atómicas que lo componen. Cada una es una
transición observable independiente y falsable.

## Decisiones ya tomadas (contexto)
- **D1**: el API legacy se construye en VB — proyecto `ERP-SYSTUTOR.API`
  (VB.NET 3.5, self-host `HttpListener` en Win10), reusa `ClsConexion`.
- **D2 (corregida)**: OSS ya posee el dominio (`plugins/crm`, `plugins/logistics`).
  La rama TMS es **capa de integración**, no reconstruye másteres.
- **D3 (pendiente)**: autenticación del API legacy.
- **D4 (decidido)**: TMS es plugin aparte (`plugins/tms`), no se extiende
  `logistics`/`crm` para lo operativo. TMS contiene **jornadas** y todo lo
  operativo de entrega: vehículo, conductor, ruta, parada/visita, GPS
  histórico, telemetría, geocercas operativas, evidencia de visita/entrega, y
  los sub-estados de cilindro `EN_VEHICULO`/`EN_CLIENTE` (D6). Los adaptadores
  que decían "según D4" (0005/0006/0010/0012/0014/0016) apuntan a consumir
  desde `plugins/tms` o exponerse para que TMS orqueste vía eventos/API
  interna, nunca REST a legacy para lo operativo.
- **D5 (decidido/requerido)**: el flujo exige descontar stock legacy al cargar
  a móvil → write-back vía API (`POST /api/stock/movement`). El stock legacy es
  computado, así que descontar = insertar egreso (Movimiento) que cumple los
  filtros del reporte. Ver 0015/0016.
- **D6 (decidido)**: frontera de "Ubicación actual del cilindro". Fuente de
  verdad = **Legacy** (maestro de ubicación del cilindro). TMS NO es dueño de
  esa ubicación; solo mantiene sub-estados operativos internos derivados de
  Parada/visita + GPS: `EN_VEHICULO` (en ruta/carga) y `EN_CLIENTE` (llegó a
  destino/entregado). El único write-back TMS→Legacy sigue siendo D5/0015/0016
  (descontar al cargar móvil). Punto abierto: si al confirmar `EN_CLIENTE` debe
  escribirse la ubicación-cliente a Legacy o lo hace otro flujo.

## A.SPECs
| ID | Título | Depende |
|----|--------|---------|
| API-REST-CON-0001 | Scaffold `ERP-SYSTUTOR.API` (VB.NET 3.5, HttpListener) | — |
| API-REST-CON-0002 | Endpoint `GET /api/clientes` (JSON Cliente) | 0001 |
| API-REST-CON-0003 | Endpoint `GET /api/clientes/{id}/puntos` (delivery points) | 0001 |
| API-REST-CON-0004 | Autenticación del API legacy | 0001, **D3** |
| API-REST-CON-0005 | Cliente tipado Python (anti-corruption adapter) | 0002, **D4** |
| API-REST-CON-0006 | Mapeo clientes legacy → `crm.Customer` | 0005, 0003 |
| API-REST-CON-0007 | Despliegue y ejecución del API en Win10 (Tailscale) | 0001 |
| API-REST-CON-0008 | Endpoint `GET /api/productos` (JSON, 4671 items) | 0001 |
| API-REST-CON-0009 | Endpoint `GET /api/productos/{id}` (detalle + ADR/M3/peso) | 0001 |
| API-REST-CON-0010 | Mapeo productos legacy → `productos` (pendiente) | 0008/0009, **D4** |
| API-REST-CON-0011 | Endpoint `GET /api/stock` (fuente `vkardex`, no cache) | 0001 |
| API-REST-CON-0012 | Mapeo stock legacy → `plugins/stock` | 0011, **D4** |
| API-REST-CON-0013 | Endpoint `GET /api/almacenes` (2 almacenes) | 0001 |
| API-REST-CON-0014 | Mapeo almacenes legacy → `logistics.Warehouse` | 0013, **D4** |
| API-REST-CON-0015 | Endpoint `POST /api/stock/movement` (write-back egreso legacy) | 0001, **D5** |
| API-REST-CON-0016 | Orquestación: carga móvil descuenta legacy | 0015, 0011, **D5** |

## Ley de frontera (invariante global)
Ninguna A.SPEC de este conjunto puede conectar Python/Systutor a SQL Server
legacy. El único puente es HTTP al `ERP-SYSTUTOR.API`.

## Principio de testing (A.SPEC 0008/0010 en adelante)
Los criterios de aceptación se validan con **tests reales, no mocks**: el
pipeline completo (API legacy real → adaptador Python real → OSS real) debe
ejecutarse y verificarse contra datos reales (ej. los **4671 productos** del
legacy en el sistema nuevo). Los mocks solo para unit tests de lógica pura,
nunca para el criterio de aceptación de una A.SPEC.
