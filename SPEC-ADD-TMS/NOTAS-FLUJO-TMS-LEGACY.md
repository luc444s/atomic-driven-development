# Notas — Flujo TMS vs Legacy (mapeo operativo)

> Anotación libre de los hallazgos sobre el legacy VB ERP-SYSTUTOR (OXIPUR/GMS)
> para el diseño del módulo TMS. No es una spec: es contexto derivado del código
> (Win10, `C:\Nueva carpeta\extraido\OXIPUR\AAASYSTUTOR GMultiSuc Octubre  OXIPUR PLUS\`)
> y de las decisiones tomadas en sesión.

## Reglas de arquitectura (leyes TMS)

- El legacy es **fuente única de verdad** para el MVP.
- **Maestros (producto, stock, clientes): solo GET.** OSS nunca escribe catálogo
  ni existencias sobre el legacy.
- **MVP: la salida a cliente se ejecuta en el legacy.** OSS lee del legacy y
  **materializa la jornada** localmente (snapshot). Dirección legacy → OSS.
- **Write-back OSS→legacy** para crear salidas: **fuera del MVP**.
- **Pesito/cantidad de egreso lo decide el legacy** (`EDetalle_cpedido.total`).
  OSS no lo inventa.

## Formas/menús del legacy (relación con TMS)

| Form | Menú/Botón | Rol | Movimiento/Kardex | Stock |
|------|-----------|-----|-------------------|-------|
| `FrmOrdenSalidaADMIN` | Button40 "Salida a Cliente" | Salida real a cliente | `sp_Movimiento_Insertar` (tipo 3, "Venta") | `UPDATE_StockProducto(2)` **resta** |
| `FrmOrdenSalida` | "ENVIAR GUIAS FACTURADAS" | Enviar/facturar guías | **No** (KardexGas comentado) | No |
| `FrmOrdenIngresoC` | Button18 / "RECEPCION DE ENVASES CLIENTES" | Recojo del vacío del cliente | **No** | No (solo pedido+estado) |
| `FrmOrdenIngresoP` / `Pnarva` | Button16 / "RECEPCION DE ENVASES PROVEEDORES" | Ingreso de stock | `sp_Movimiento_Insertar` (tipo 1, "Ingreso") | `UPDATE_StockProducto(1)` **suma** |

## Flujo "Salida a Cliente" (egreso, con stock)

1. `MOV` = "Venta" (RadioButton4) o "Prestamo" (default).
2. `InsertarECabeceraPedido(... forma_mov="Salida", motivo=MOV ...)` → `ECabecera_pedido` (solo pedido, no toca stock).
3. Por item: `InsertardetallePedido(...)` → `EDetalle_cpedido`; `consultar_detalle_envase` + `actualizar_REPORTEDETENVASE`.
4. `KardexGas()` (form ADMIN):
   - `sp_Movimiento_Insertar(TipoAtencion=1, inventario=1, Nroguia=NULL si vacío)` → `Movimiento`
   - `sp_DetalleMovimiento_Insertar(StkEgreso=pesito)` → `DetalleMovimiento`
   - `UPDATE_StockProducto(2, cod, pesito)` → `Producto.stock -= pesito` (solo si TipoAtencion=1)
   - `actualizar_guia` / `actualizar_ResponsableVenta` / `actualizar_TCmovi` / `actualizar_gastos_envio`

**Pesito** = `EDetalle_cpedido.total` del último pedido de ese envase (capacidad nominal:
"OXIGENO 10M3" → 10, "GAS CARBONICO 33KGM" → 33). **NO es -1 por unidad.**

## Flujo "Recepción de Envases Clientes" (recojo, SIN stock)

1. Valida envase: `consultar_envase_venta(serial)` debe dar `motivo=Lleno|Devolución`,
   `forma_mov="Salida"`, `tipo="Cliente"`, `persona=cliente`. Sino rechaza.
2. `Producto_BuscarxNroSerieCilindros(serial)` → serial→`cod_producto`, `Desc_Producto`,
   `condicion`, `peso_producto` (busca por `Nro_Producto`, case/trim-insensitive).
3. `InsertarECabeceraPedido(... forma_mov="Ingreso", motivo="Venta" ...)` → `ECabecera_pedido`.
4. `InsertardetallePedido(... motivo="Vacio", condicion, estado=1, ubicacion="ALMACEN" ...)` → `EDetalle_cpedido`.
5. `actualizar_estado(id_detalle, 1)` → proc `Actualizar_Estado_Env` (UPDATE EDetalle_cpedido.estado).
6. `actualizar_REPORTEDETENVASE1` / `act_detalleEnvaseICL`.

**No crea Movimiento ni stock en este form.** El stock del envase que vuelve vacío
se maneja en la recepción de proveedores, no acá.

## Condiciones de envase (`Producto.condicion`)

- `CILPROV` (2087): cilindro del proveedor.
- `CILPRO` (1935): cilindro del proveedor.
- `CILCLI` (416): cilindro del cliente.
- `CILGAR` (4): cilindro en garantía.
- `PRODUCTO` (221): no-envase.

## Serial

Formato libre, prefijo+correlativo: `TS-2210698`, `20K463078`, `21k464028`.
`Nro_Producto` es único por envase; `cod_producto` es el id del cilindro físico.
En recepción, el mismo serial que salió lleno vuelve vacío (ej. "001 102024").

## Campos de transporte/guía

Bloque común en los forms: Nro Guía Rem, Nombre/Razón Social, RUC, Transportista (chofer),
CÉDULA (DNI chofer), Vehículo (placa), Partida + ubigeo, Llegada + ubigeo, Cant. bultos.
En `FrmOrdenSalida.vb` se autocompleta desde `mostrar_mozo` (choferes con `Celular="Chofer"`);
en `FrmOrdenSalidaADMIN` van manuales y opcionales (validación comentada).
Campos → `sp_Movimiento_Insertar`: `Transportista, Placa, dnichofer, ubigeopartida, ubigeollegada, cbultos`.

## Estructura TMS (cómo se ve en OSS)

```
JORNADA (LogisticsVehicleSession) — por vehículo + chofer del día
│  estados: DRAFT → LOADING → READY_TO_DEPART → OUTBOUND → MOBILE → RETURNING → CLOSED
│
├── OPERACIÓN salida  (CUSTOMER_DELIVERY / sale_out = egreso)  ← materializa la salida legacy
│      seriales DELIVERY_SELECTED/CONFIRMED
│      stock_bridge.sale_out_stock
│      tracking: CARGA_EN_VEHICULO → EN_RUTA → ...
│
└── OPERACIÓN recojo  (CUSTOMER_PICKUP / return_in = ingreso)  ← recepción cliente
       seriales pickup → stock_bridge.return_in_stock
       responsable/fecha/códigos envase auto-llenados (envase→producto)
```

- Jornada por vehículo (NO por salida). Cada salida/recojo es una operación dentro de la jornada.
- `envase→producto` ya existe: `LogisticsCylinder.product_id` + fallback `_resolve_product_id` en stock_bridge.
- Responsable/fecha = `action_context` (actor_user_id, created_at).

## Contrato API (borrador conceptual)

- **Maestros (GET)**: producto, stock, clientes. Read-only.
- **Materializar jornada (GET)**: listar salidas del legacy → OSS crea jornada + operaciones (snapshot).
- **Salida**: se ejecuta en el legacy (fuera del MVP el write-back OSS→legacy).
- **Recepción cliente (POST)**: auto-guardado replicando `FrmOrdenIngresoC`:
  - Input OSS: cliente, responsable, fecha, serial, transporte.
  - Legacy valida envase + infiere producto/condición; guarda pedido+estado. Sin stock.

## Referencias en BD/procs

- `ECabeceraPedido_Insertar` → INSERT `ECabecera_pedido` (sin stock).
- `EDetallePedido_Insertar` → INSERT `EDetalle_cpedido`.
- `sp_Movimiento_insertar` → INSERT `Movimiento` (Nroguia NULL si vacío).
- `sp_DetalleMovimiento_Insertar` → INSERT `DetalleMovimiento` (StkIngreso/StkEgreso).
- `UPDATE_StockProducto` → `Producto.stock +/- cantidad` (Tipoingreso 1=suma, 2=resta si TipoAtencion=1).
- `consultar_envase_venta` / `consultar_envaseAct` → traza del último estado del envase.
- `Producto_BuscarxNroSerieCilindros` → serial→producto/condición.
- `Actualizar_Estado_Env` → UPDATE `EDetalle_cpedido.estado`.

## Accesos útiles

- SQL Server: `100.67.5.50` (Linux Mint), `sqlcmd=/opt/mssql-tools18/bin/sqlcmd`,
  `-C` (trust cert), DB `Sys_gas2_pLUS`, `sa` (creds en `app.config` del ERP, no duplicar aquí).
- Win10 (código fuente): `100.68.121.21`, usuario `LUCAS`, SSH `cmd /c "..."`.
- Copia local temporal de fuentes/procs: `/data/data/com.termux/files/usr/tmp/opencode/oxipur/`.