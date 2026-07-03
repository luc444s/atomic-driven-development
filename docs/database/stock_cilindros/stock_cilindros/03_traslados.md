# Traslados — Flujo en FrmMovTrasladoAlmacen

## Resumen del Form

- **Archivo**: `FrmMovTrasladoAlmacen.vb`
- **Líneas**: 4,300
- **Propósito**: Trasladar cilindros entre almacenes, registrar carga de vehículo

## Flujo Principal: `cmdgrabar_Click`

```
1. Validar origen ≠ destino
2. Confirmar "¿Deseas registrar la CARGA del vehículo?"
3. Validar que ListView3Carga tenga items

4. Loop por cada cilindro en la carga:
   │
   ├── Si estado = "Lleno":
   │     ├── Si primera vez: Crear ECabeceraPedido (tipo "Traslado", persona "Transferencia Lleno")
   │     │     └── InsertarECabeceraPedido(0, fecha, lblcodigo3, "Proveedor", serie, nro, "Ingreso", "Traslado", ...)
   │     ├── InsertardetallePedido con motivo="Lleno"
   │     ├── Insertarrepdetenv (REPORTEDETENVASE — tracking propio)
   │     ├── consultar_detalle_envase + actualizar_REPORTEDETENVASE1 + actualizar_REPORTEDETENVASE
   │     └── consultar_detalle_envaseUltimoId
   │
   └── Si estado = "Vacio":
         ├── Si primera vez: Crear ECabeceraPedido (tipo "Traslado", persona "Traslado Vacio")
         │     └── InsertarECabeceraPedido(0, fecha, lblcodigo3, "Cliente", ...)
         ├── InsertardetallePedido con motivo="Vacio"
         ├── Insertarrepdetenv
         ├── consultar_detalle_envase
         ├── actualizar_REPORTEDETENVASE2 + actualizar_REPORTEDETENVASE1 + actualizar_REPORTEDETENVASE
         └── Validación de error

5. Si huboLleno → RegistrarParaTraslado_Bitacora_Carga("LLENO")
6. Si huboVacio → RegistrarParaTraslado_Bitacora_Carga("VACIO")
7. BTNgrabarSalida_Click (crea movimiento de salida?)
8. Actualizar Agenda_Repartidor (sp_AgendaRepartidor_MarcarCargadoPorGuia)
```

## ¿Qué mueve: cantidades, estados o ambos?

**Solo estados (no cantidades).** El traslado:

| Acción | ¿Afecta stock? | ¿Afecta estado? |
|---|---|---|
| Crear ECabeceraPedido | No | Indirecto (pedido de traslado) |
| InsertardetallePedido | No | Sí (registra motivo=Lleno/Vacio) |
| Insertarrepdetenv | No | Sí (tracking propio de envase) |
| BTNgrabarSalida_Click | **Sí** (crea Movimiento con StkEgreso) | Quizás |
| ECilindroEstadoActual | No se actualiza directamente aquí | Debe actualizarse en otro punto |

**Conclusiones:**
1. El form **NO actualiza** `Producto.stock` ni `Stock_Actual` directamente
2. El form **NO llama** a `usp_Cilindro_CambiarEstado` (o no se ve en el extracto)
3. `BTNgrabarSalida_Click` probablemente crea el movimiento contable que afecta `DetalleMovimiento.StkEgreso`
4. El rastreo de envases usa una tabla propia: `REPORTEDETENVASE` (no documentada en schemas principales)
5. Las tablas `ECilindroEstadoActual` y `Stock_Actual` no se actualizan en este flujo — **gap de sincronización**

## ¿Diferencia llenos/vacíos?

**Sí.** Los trata como pedidos separados:
- `IDordenLlenos.Text` — pedido para cilindros llenos
- `IDordenVacios.Text` — pedido para cilindros vacíos
- Cada uno con su propia `ECabeceraPedido` y persona asociada ("Transferencia Lleno" vs "Traslado Vacio")

## Bitácora de carga

```sql
sp_AgendaRepartidor_MarcarCargadoPorGuia @Id_GuiaCarga, @Cod_Sucursal, @Usuario
```
