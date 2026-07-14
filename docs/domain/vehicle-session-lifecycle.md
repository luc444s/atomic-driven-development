# Vehicle Session Lifecycle

## Estado

Vigente — referencia de dominio para `SPEC 0023E1`

## Principio

El lifecycle pertenece a `VehicleSession`.

No pertenece a:

- Vehicle
- Warehouse
- Stock
- Fleet Monitor

## Diagrama

```text
                +-----------+
                |   DRAFT   |
                +-----------+
                      |
                      v
                +-----------+
                |  LOADING  |
                +-----------+
                      |
                      v
           +----------------------+
           | READY_TO_DEPART      |
           +----------------------+
                      |
                      v
                +-----------+
                | OUTBOUND  |
                +-----------+
                      |
                      v
                +-----------+
                | RETURNING |
                +-----------+
                      |
                      v
      +----------------------------------+
      | AWAITING_RECONCILIATION          |
      +----------------------------------+
                      |
                      v
                +-----------+
                |  CLOSED   |
                +-----------+

Exceptional:
DRAFT / LOADING / READY_TO_DEPART -> CANCELLED
```

## Significado de cada estado

### DRAFT

La jornada existe pero aun no entro a carga.

### LOADING

La jornada esta en preparacion y carga.

### READY_TO_DEPART

La carga real fue confirmada y la jornada ya puede salir.

### OUTBOUND

El vehiculo ya salio del almacen.

Este estado existe para distinguir claramente la salida efectiva del simple estado intermedio de preparacion.

### RETURNING

El vehiculo ya termino la etapa principal de salida y esta retornando o ya se encuentra en proceso de devolucion operativa.

### AWAITING_RECONCILIATION

La jornada ya retorno, pero aun no se realizo o cerró la conciliacion.

### CLOSED

La jornada esta operativamente terminada y conciliada.

### CANCELLED

La jornada fue anulada antes de entrar en ejecucion real irreversible.

## Reglas de transicion

### DRAFT -> LOADING

- requiere vehiculo asignado
- requiere conductor asignado
- requiere warehouse MOBILE asociado al vehiculo
- requiere warehouse origen

### LOADING -> READY_TO_DEPART

- requiere carga confirmada
- requiere resultado correcto de Stock para las transferencias de salida
- requiere validacion de capacidad

### READY_TO_DEPART -> OUTBOUND

- no puede haber errores criticos
- la sesion debe ser editable
- la carga ya debe estar confirmada

### OUTBOUND -> RETURNING

- la jornada ya salio
- el flujo operativo entra en retorno

### RETURNING -> AWAITING_RECONCILIATION

- el remanente ya fue devuelto o la jornada ya esta lista para conteo

### AWAITING_RECONCILIATION -> CLOSED

- no puede haber discrepancias abiertas
- la conciliacion debe quedar resuelta

## Regla de oro

```text
VehicleSession NO representa inventario.
VehicleSession representa una operacion logistica.
Todo inventario pertenece a Stock.
```
