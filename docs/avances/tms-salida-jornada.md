# TMS — Mapeo Salida a Cliente → Jornada (legacy → OSS)

Estado: MVP validado end-to-end (2026-08-20). Legacy dueño, OSS lee vía API y materializa.

## Insight clave (anotado por usuario)

El API legacy **ya trae la dirección del cliente** en `GET /clientes` (`direccion`).
Eso cubre el campo **llegada/destino** de la jornada TMS cuando la salida legacy
viene sin `LugarDestino` (ej. salida #42470 lo traía vacío).

Regla de mapeo:

```
operacion.llegada = Orden_compra.LugarDestino
                  ?? cliente.direccion   (fallback del API /clientes)
```

## Fuente de datos

- `GET /salidas` y `GET /salidas/{id}` → lista/detalle de salidas (legacy VB, ERP-SYSTUTOR.API).
- `GET /clientes` y `GET /clientes/{id}/puntos` → maestros cliente (incluye dirección).
- Consumido en OSS por `LegacyApiClient` (`plugins/tms/backend/legacy/client.py`).

## Mapeo salida → jornada OSS

| Campo OSS (jornada/operación) | Origen legacy |
|---|---|
| `jornada_key` | `placa \| dnichofer \| fecha.fecha()` |
| `vehiculo_placa` | `Orden_compra.Placa` |
| `chofer_dni` | `Movimiento.dnichofer` (o `Persona.Dni_Persona`) |
| `fecha` | `Movimiento.Fecha` |
| operación `tipo` | `CUSTOMER_DELIVERY` (salida/egreso) |
| `cliente` / `cod_cliente` | `Persona.Nom_Persona` / `Cod_Persona` |
| `almacen` | `Movimiento.Almacen` |
| `llegada` | `Orden_compra.LugarDestino` ?? `cliente.direccion` |
| `partida` | `Orden_compra.LugarInicio` |
| `transportista` | `Orden_compra.Transportista` |
| `cantidad_bultos` | `Movimiento.cbultos` |
| ítem `cod_producto` | `DetalleMovimiento.CodProducto` |
| ítem `pesito` | `DetalleMovimiento.StkEgreso` |
| ítem `cantidad` | `DetalleMovimiento.Cant` |
| serial/barcode | `VDETALLE_ENVASE.Nro_Producto` |

## Anomalías conocidas

- **Ítem sin producto**: salidas pueden venir con `cod_producto = 0` / `producto = ""`
  pero `pesito > 0` (ej. #42470, pesito 2). → ítem huérfano en OSS; decidir
  ignorar o registrar como "producto no resuelto".
- `Guia_despacho` (vista de carta porte) está rota en la BD (*binding errors*);
  no usar hasta corregir.

## Ejemplo real materializado

Salida #42470 (2026-08-20 14:24):

```
jornada_key: RAM/BEI-793 | 78839842 | 2026-08-20
cliente: M.H. EIRL (cod 4587), almacen 1
operacion: CUSTOMER_DELIVERY, pesito 2 (item sin producto ligado)
```

Cliente de prueba con dirección: cod 9540 = `4PRO INNOVACION AUTOMOTRIZ E.I.R.L.`
(RUC 20610878955, AV. FEDERICO VILLARREAL 551, Trujillo).

## Pendiente

- Persistir snapshot de salida en DB TMS (modelo + migración Alembic).
- Vincular a `LogisticsVehicleSession` real del core logistics.
- Decidir manejo de ítem con `cod_producto = 0`.
