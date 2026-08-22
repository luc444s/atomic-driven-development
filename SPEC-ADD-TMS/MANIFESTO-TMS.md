# MANIFESTO TMS — Rama `TMS`

## Finalidad de la rama

Esta rama aloja el módulo **TMS (Transport Management)** y la **capa de integración**
que conecta Python Systutor con el legacy VB **ERP-SYSTUTOR (OXIPUR / GMS)**, bajo
una ley de frontera estricta entre ambos mundos.

No es una rama de migración masiva ni de reescritura del legacy: es el lugar donde
el sistema nuevo **crece alrededor** del existente.

## Estado de los dos mundos

- **Mundo VB (legacy)**: ERP-SYSTUTOR estable, system-of-record. SQL Server en
  Windows 10 (`DESKTOP-T8R9INR`). Código fuente en
  `C:\Nueva carpeta\extraido\OXIPUR\AAASYSTUTOR GMultiSuc Octubre  OXIPUR PLUS\`.
- **Mundo Python (Systutor)**: estable, crece alrededor del legacy. Corre en
  **Termux** (este dispositivo), no en Linux Mint.
- **Linux Mint (`100.67.5.50`)**: corre **solo SQL Server** (la base de datos
  legacy GMS / `Sys_Gas2_Plus`). No ejecuta el Python de desarrollo.
- Nota: el doc `SYS_GAS2_PLUS_HALLAZGOS.md` dice "SQL Server localhost" en Win10;
  la topología autoritativa es SQL Server en Linux Mint. Win10 es el cliente OXIPUR.

## Ley de frontera (invariante central)

> El sistema nuevo **NO conoce la base de datos legacy**.
> Solo usa el **API del sistema legacy** (aún por crear) para conocer los datos.

Prohibido:
- conexión directa de Python a SQL Server legacy;
- sync DB-to-DB o dual-write;
- lectura de tablas legacy desde el backend Python;
- replicar tablas GMS en Python sin estrategia de snapshot.

## Ley TMS: legacy first, maestros read-only

> El legacy **es la fuente única de verdad** para el MVP. El sistema nuevo no
> decide ni reescribe datos del legacy; consume y registra en torno a él.

- **Maestros legacy (producto, stock, clientes): solo GET.** Nunca PUT/POST/PATCH
  desde OSS. OSS lee, no corrige catálogo ni existencias.
- **MVP: la salida a cliente se ejecuta en el legacy** (egreso, pesito, pedido y
  movimiento en VB/API). OSS **lee del legacy y materializa** la salida como una
  jornada real, con su tracking; no la crea ni dispara el egreso.
- **Dirección de datos legacy → OSS (lectura/materialización).** El write-back
  OSS→legacy para crear salidas queda **fuera del MVP**: el operador actúa en el
  legacy y OSS lo refleja (snapshot).
- **La cantidad de egreso (pesito/capacidad del envase) la decide el legacy**
  (`EDetalle_cpedido.total` vía API). OSS la usa tal cual, nunca la inventa.
- **Excepción a la regla de maestros GET**: una operación de egreso/ingreso que
  OSS deba registrar transaccionalmente es una escritura al API legacy, no un
  maestro. No confundir ambos casos.

## Ownership (quién es dueño de qué)

- **Legacy (VB)** es dueño de: clientes, productos, almacenes/sucursales, pedidos,
  stock y cualquier dato GMS.
- **TMS (Python)** es dueño de: flota/vehículos, rutas, despachos y su propio estado
  operativo en PostgreSQL del sistema nuevo.

## Patrón de integración

- **REST** (convención `api-rest-connector`): Python consume endpoints del legacy.
- **Anti-corruption layer**: un adaptador Python traduce el contrato del API legacy
  a modelos canónicos TMS. El dominio TMS no acopla a esquemas internos de VB.
- **Live read** para catálogos y datos operativos actuales.
- **Snapshot** en tablas transaccionales de TMS para histórico y auditoría.
- **Eventos** para notificación/propagación cuando no se requiera dato inmediato.

## Prohibiciones (anti-patrones)

- tocar la BD legacy desde Python;
- copiar catálogos GMS a Python sin estrategia de snapshot/migración;
- import directo de lógica interna del legacy;
- ad-hoc frontend imports entre dominios;
- que el consumidor TMS se vuelva source-of-truth de datos que son del legacy.

## Alcance de esta rama

- definir la capa de integración legacy ↔ TMS;
- modelar el dominio TMS (flota/vehículos primero);
- consumir el API legacy (cuando exista) sin acoplar al esquema interno de VB;
- dejar trazabilidad: cada A.SPEC atada a commit, respetando ADD.

## Relación con el resto del repo

- Respeta `AGENTS.md`: lógica de negocio en Python auditable, eventos entre módulos,
  sin stored procedures de negocio.
- La migración por dominio (CSV + `manifest.json`) sigue vigente para datos que
  TMS deba poseer de forma permanente; lo operativo se lee por API.
