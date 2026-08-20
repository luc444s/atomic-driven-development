# PLAN TMS — Visión de planificación

Rama `TMS`. Baseline: dos mundos estables (VB legacy + Python Systutor). El nuevo
sistema crece alrededor del legacy y solo lo toca vía API.

## Red (Tailscale)

Las tres máquinas están en la **misma red Tailscale** (las IPs `100.x.x.x` son de
Tailscale, no públicas). Conectividad ya verificada: SSH Termux→Win10 y
Termux→Linux Mint funcionan.

- Termux (Python) ↔ Win10 (API legacy): directo por Tailscale, cifrado.
- Win10 (API VB) ↔ Linux Mint:1433 (SQL Server): directo por Tailscale.
- Sin exposición pública; firewall puede restringir a la subnet Tailscale.
- Usar MagicDNS (`desktop-t8r9inr`, `lucas-thinkpad`) en vez de IPs fijas.

Esto elimina la incógnita de alcance de red: el API legacy en Win10 es
alcanzable desde Termux por defecto.

## Ejes de la planificación

### Eje 1 — Contrato del API legacy (VB, por crear)
TMS no puede avanzar sin saber qué endpoints consume. Antes de código Python de
integración, se define el contrato (request/response) de lo que el legacy debe
exponer:
- catálogo de clientes (`Persona` + `TipoPersona`);
- catálogo de productos/almacenes;
- pedidos (`ECabecera_pedido` / `EDetalle_cpedido`);
- stock operativo (desde `Movimiento`, no `Producto.stock`);
- (futuro) entidades de flota si viven en GMS.

El API legacy es system-of-record; TMS solo lee (y escribe solo lo que le pertenece).

### Eje 2 — Dominio TMS (Python, PostgreSQL propio)
Modelar lo que TMS posee:
- `Vehiculo` / flota (primera entidad);
- `Ruta`, `Despacho`, estados operativos.
Tablas propias, migraciones Alembic, sin referencia a tablas legacy.

### Eje 3 — Adapter / Anti-corruption layer (Python)
- clientes tipados por endpoint legacy;
- mappers legacy→canónico TMS;
- cache/snapshot en tablas transaccionales cuando el histórico importe;
- resolución de nombres (no mostrar IDs crudos al usuario).

### Eje 4 — Features TMS
CRUD flota, UI, despacho. Consumen el adapter, nunca el API legacy en crudo.

## Secuencia sugerida (aún sin A.SPECs)
1. Definir contrato API legacy necesario para TMS (documento de contrato).
2. Scaffold plugin TMS (backend/frontend/migrations/plugin.json).
3. Modelo + migración `Vehiculo`.
4. Adapter layer con client tipado al API legacy.
5. CRUD + UI flota.
6. Integración live-read de catálogos GMS vía API.

## Invariantes a preservar
- Python nunca conecta a SQL Server legacy.
- Legacy sigue dueño de GMS.
- Cada cambio trazable a commit (ADD).

## Decisiones tomadas

### D1 — El API legacy se construye en VB (ERP-SYSTUTOR.API)
- Nuevo proyecto VB.NET 3.5 en la solución ERP-SYSTUTOR, self-host `HttpListener`
  en Win10, reusa `ClsConexion.vb`.
- No se usa wrapper externo: evita drift de reglas de negocio y honra la ley
  "api del sistema legacy (VB)".
- Wrapper queda como plan B solo si VB 3.5 REST resulta inviable.

### D2 — Flota y Chofer son másteres nuevos de TMS (legacy no los tiene)
- Verificado en `Sys_gas2_pLUS` (SQL Server, Linux Mint): NO existen tablas máster
  de flota/camión/chofer/conductor/ruta.
- El legacy modela chofer y placa solo como referencias en documentos de despacho:
  columnas `dnichofer` (DNI) y `Placa` en `ECabecera_pedido`, `Movimiento`,
  `Guia_despacho`, `Orden_compra`, `VTICKET`, etc.
- `Persona` (1891 filas) tiene `Dni_Persona` (el "numero"), `Nom_Persona`,
  `Cod_TipoPersona`. No hay rol "chofer" en `TipoPersona` (solo
  Cliente/Personal/Cocinero/Empresa/Mozo); el chofer es una `Persona` (tipo
  Personal) referenciada por `dnichofer` en los docs.
- Única entidad vehicular legacy aparte: `vehiculo_cliente` = vehículos de
  **cliente** (puntos de entrega; 769 filas), no flota del transportista.
- Por tanto TMS posee los másteres **`Vehiculo`** (con `placa`) y **`Chofer`**
  (con `dni` → `Persona.Dni_Persona`) en su PostgreSQL.
- Enlace legacy↔TMS por claves: `Placa` (vehículo) y `Dni_Persona`/`dnichofer`
  (chofer), expuestas por `ERP-SYSTUTOR.API` al leer pedidos/movimientos/guías.

> **CORRECCIÓN (descubierto en código OSS):** el dominio TMS ya existe en
> `plugins/logistics`. No hay que crear `Vehiculo`/`Chofer`/`Jornada` desde cero:
> - `LogisticsVehicle` = flota (`plugins/logistics/backend/models/`, migración
>   `002_phase_2_3.py`)
> - `LogisticsVehicleSession` = **Jornada** con state machine
>   (DRAFT→LOADING→READY_TO_DEPART→OUTBOUND→RETURNING→AWAITING_RECONCILIATION→
>   CLOSED) en `services/rules.py`
> - `DriverParameter` = chofer; más rutas, delivery points, waybill, reconciliación,
>   telemetría (`LogisticsVehicleLocationEvent`)
>
> Por tanto el valor de la rama TMS es la **capa de integración legacy↔OSS**
> (consumir `ERP-SYSTUTOR.API` y enlazar por `Placa`/`DNI`), no reinventar el
> dominio.

## Pendientes de decisión
- **D3** — ¿Autenticación del API legacy? (token/usuario systutor)
- **D4** — ¿La rama TMS extiende el plugin `logistics` existente, o crea un
  plugin `tms` aparte que consuma `ERP-SYSTUTOR.API`?
