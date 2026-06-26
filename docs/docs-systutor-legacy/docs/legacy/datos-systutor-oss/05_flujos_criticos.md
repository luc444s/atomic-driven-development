# 05 — Flujos Críticos y Máquinas de Estado

## 1. Máquina de Estados del Cilindro (ECilindroEstado)

### 1.1 Diagrama de Estados

```
                    ┌──────────────┐
                    │  CREADO_VACIO │
                    └──────┬───────┘
                           │
                           ▼
                   ┌───────────────┐
            ┌──────│EN_ALMACEN_VACIO│◄──────────────────────────────┐
            │      └───┬───┬────┬──┘                                │
            │          │   │    │                                    │
            │    ┌─────┘   │    └──────┐                             │
            │    ▼         ▼           ▼                             │
            │ ┌────────┐ ┌──────┐ ┌─────────┐                       │
            │ │LLENADO │ │EN_MANT│ │ DE_BAJA │                       │
            │ │  _OK   │ │_TO    │ │ (FINAL) │                       │
            │ └───┬────┘ └──────┘ └─────────┘                       │
            │     │                                                  │
            │     ├──────────────────────┐                           │
            │     ▼                      ▼                           │
            │ ┌──────────┐       ┌──────────────┐                    │
            │ │EN_CLIENTE│       │CARGA_EN_VEH  │                    │
            │ │ _LLENO   │       │              │                    │
            │ └┬──────┬──┘       └──────┬───────┘                    │
            │  │      │                 │                            │
            │  │      ▼                 ▼                            │
            │  │  ┌──────────┐    ┌──────────┐                       │
            │  │  │EN_CLIENTE│    │ EN_RUTA  │                       │
            │  │  │ _VACIO   │    └┬────┬────┘                       │
            │  │  └┬────┬────┘     │    │                            │
            │  │   │    │          │    │                            │
            │  │   │    ▼          │    ▼                            │
            │  │   │ ┌────────┐    │ ┌──────────────┐                │
            │  │   │ │ PERDIDO│    │ │DESCARGADO_POR│                │
            │  │   │ │(FINAL) │    │ │_RECEPCIONAR  │                │
            │  │   │ └────────┘    │ └──────┬───────┘                │
            │  │   │               │        │                        │
            │  │   └───────┬───────┘        ▼                        │
            │  │           │          ┌─────────────┐                │
            │  │           └─────────►│RECEPCIONADO │                │
            │  │                      └──────┬──────┘                │
            │  │                             │                       │
            │  └─────────────────────────────┘                       │
            │                                                        │
            └────────────────────────────────────────────────────────┘
```

### 1.2 Transiciones Detalladas con Reglas

| Desde | Hasta | Trigger | Validaciones |
|-------|-------|---------|-------------|
| CREADO_VACIO | EN_ALMACEN_VACIO | Alta de cilindro nuevo | Datos de fabricación completos |
| EN_ALMACEN_VACIO | LLENADO_OK | Planta de llenado | PH vigente, ADR vigente |
| EN_ALMACEN_VACIO | EN_MANTENIMIENTO | Envío a taller | Registrar orden de mantenimiento |
| EN_ALMACEN_VACIO | DE_BAJA | Baja administrativa | Aprobación requerida |
| EN_ALMACEN_VACIO | PERDIDO | Reporte de pérdida | Documentar incidencia |
| LLENADO_OK | EN_CLIENTE_LLENO | Despacho directo (sin ruta) | Asignación a movimiento |
| LLENADO_OK | CARGA_EN_VEHICULO | Preparación de carga | Verificar capacidad del vehículo |
| CARGA_EN_VEHICULO | EN_RUTA | Inicio de ruta | Chofer asignado, guía impresa |
| EN_RUTA | EN_CLIENTE_LLENO | Entrega exitosa | Escaneo en destino, firma |
| EN_RUTA | DESCARGADO_POR_RECEPCIONAR | Recepción en almacén destino | Guía de recepción |
| DESCARGADO_POR_RECEPCIONAR | RECEPCIONADO | Conformidad de recepción | Verificación de cantidad |
| RECEPCIONADO | EN_ALMACEN_VACIO | Ubicación en almacén | Registrar ubicación física |
| EN_CLIENTE_LLENO | EN_CLIENTE_VACIO | Consumo/uso por cliente | Interno (cliente vacía el cilindro) |
| EN_CLIENTE_LLENO | VACIO_EN_ALMACEN | Devolución directa a almacén | Guía de devolución |
| EN_CLIENTE_VACIO | EN_RUTA | Recojo programado | Ruta de recogida asignada |
| EN_CLIENTE_VACIO | PERDIDO | Cliente no devuelve | Gestión de cobro |
| EN_MANTENIMIENTO | EN_ALMACEN_VACIO | Mantenimiento completado | OK técnico |
| VACIO_EN_ALMACEN | EN_ALMACEN_VACIO | Recepción formal en almacén | Inventario |

### 1.3 Efectos de TipoDoc sobre Estados de Envase

Cuando se crea un movimiento con un TipoDoc que tiene MueveEnvases=1:

| TipoDoc | OrigenEnvase | DestinoEnvase | Efecto en cilindros del detalle |
|---------|-------------|---------------|-------------------------------|
| #5 SC (Albarán Entrega cliente) | ALMACEN | CLIENTE | Estado: EN_ALMACEN_VACIO→EN_CLIENTE_LLENO |
| #13 IC (Albarán Recepción cliente) | CLIENTE | ALMACEN | Estado: EN_CLIENTE_VACIO→EN_ALMACEN_VACIO |
| #14 IP (Albarán Recepción proveedor) | PROVEEDOR | ALMACEN | Estado: CREADO_VACIO→EN_ALMACEN_VACIO (nuevos) |
| #41 SP (Albarán Entrega proveedor) | ALMACEN | PROVEEDOR | Estado: EN_ALMACEN_VACIO→EN_RUTA (hacia proveedor) |

## 2. Flujo de Reparto Completo

### 2.1 Pipeline: Pedido → Entrega

```
ECabecera_pedido ──► Movimiento ──► AGENDA_REPARTIDOR ──► PREPARACION_CARGA ──► DESPACHO ──► ENTREGA ──► CIERRE
```

**Paso 1 — Registro de Pedido:**
1. Cliente solicita cilindros (teléfono, web, visita)
2. Se crea ECabecera_pedido con tipo_movimiento, almacén, fechas compromiso
3. Se crean líneas en EDetalle_cpedido (producto, cantidad, condición)

**Paso 2 — Vinculación a Movimiento:**
1. Desde "Atender Pedido" (FrmMovIntercambioCliente) se selecciona pedido pendiente
2. Se crea Movimiento con TipoDocumento=5 (SC), EstadoTraslado='PENDIENTE'
3. Se vincula Movimiento.Id_Cpedido = ECabecera_pedido.cod_cpedido
4. Se copian líneas del pedido a DetalleMovimiento

**Paso 3 — Planificación de Carga:**
1. Se prepara la agenda del repartidor para el día siguiente
2. Se agrupan pedidos por ruta/zona
3. Se genera AGENDA_REPARTIDOR con tareas 'ENTREGA' y 'RECOJO'
4. Se genera AGENDA_PREPARACION_CARGA con cilindros asignados

**Paso 4 — Preparación de Carga (Planta/Almacén):**
1. Se asignan cilindros específicos (por serie/Nro_Producto)
2. Se registra LLENADO_OK para cada cilindro
3. Se registra CARGA_EN_VEHICULO cuando se monta al camión
4. Se actualiza EstadoTraslado a 'EN_RUTA'

**Paso 5 — Entrega en Cliente:**
1. Repartidor escanea cilindros (usp_Scan_Procesar)
2. Por cada cilindro: se cambia estado a EN_CLIENTE_LLENO
3. Se actualiza DetalleMovimiento (cantidad entregada, serie)
4. Se recoje cilindro vacío si aplica (canje)
5. Se registra firma/evidencia

**Paso 6 — Cierre:**
1. Se actualiza EstadoTraslado a 'COMPLETADO'
2. Se actualiza AGENDA_REPARTIDOR a 'REALIZADO'
3. Se genera comprobante si aplica (factura/boleta)
4. Se actualiza stock (Stock_Actual)

## 3. Flujo de Facturación Electrónica

```
Movimiento ──► Comprobante ──► FE Proveedor ──► SUNAT/Hacienda ──► CDR ──► XML firmado
```

**Para Perú (Nubefact):**
1. Crear Comprobante con estado=1
2. Enviar JSON a Nubefact: {tipoDoc, serie, numero, cliente, items, totales}
3. Recibir respuesta: {aceptado, cdrBase64, claveAcceso}
4. Actualizar Comprobante: ESTADO_SUNAT=2, ClaveElectronica=clave
5. Almacenar XML/CDR en archivo o BD

**Para Costa Rica (Hacienda CR):**
1. Crear Comprobante con estado=1
2. Generar XML según esquema Hacienda CR
3. Firmar XML con certificado digital
4. Enviar a API Hacienda
5. Recibir respuesta y actualizar estado

## 4. Flujo de Ciclo PH (Prueba Hidráulica)

```
EN_ALMACEN_VACIO ──► EN_MANTENIMIENTO ──► (retimbrado) ──► EN_ALMACEN_VACIO
```

Cada cilindro debe pasar PH cada 5 años (GLP) o según normativa local.

1. Consultar cilindros con PH próximo a vencer (v_Cilindros_Vacios_ALM_conPH)
2. Seleccionar cilindros para retimbrado
3. Cambiar estado a EN_MANTENIMIENTO
4. Realizar prueba: registrar en Edetalle_retimbrado (peso, presión, etc.)
5. Registrar nueva fecha en Eph
6. Cambiar estado a EN_ALMACEN_VACIO

## 5. Flujo de ADR (Carga Peligrosa)

Para cada movimiento que transporta GLP:

1. Por cada producto en el detalle, verificar ADR vigente en vw_EdetPB_Vigente
2. Calcular puntos ADR (fn_ADR_Points = ADR_Factor × Cantidad)
3. Seleccionar camión compatible (usp_ADR_SeleccionarCamion):
   - ADR_MaxPuntos >= puntos calculados
   - ADR_ClasesPermitidas incluye la clase del producto
   - ADR_TunelPermitido es compatible
4. Asignar chofer con certificación ADR vigente
5. Generar documentos de transporte (Carta Porte)

## 6. Manejo de Correlativos

Cada tipo de documento por almacén y año tiene su propio correlativo:

1. Al crear un nuevo movimiento/comprobante:
   - Buscar correlativo en CorrelativosDocumento WHERE Cod_TipoDoc + Cod_Almacen + Año
   - Obtener UltimoCorrelativo + 1
   - Actualizar UltimoCorrelativo
   - Asignar NroDocCorrelativo = nuevo número

**⚠️ RIESGO**: En el legacy no hay bloqueo de fila (UPDLOCK). En OSS, usar `SELECT ... FOR UPDATE` o transacción serializable para evitar duplicados.

## 7. Reglas de Validación de Documentos (Multi-País)

Cada país tiene reglas diferentes para documentos fiscales:

| País | Documento | Formato | Validación |
|------|-----------|---------|-----------|
| Perú | RUC | 11 dígitos | Módulo 11 |
| Perú | DNI | 8 dígitos | Dígito verificador |
| Costa Rica | Cédula Física | 9 dígitos | Formato 0-0000-0000 |
| Costa Rica | Cédula Jurídica | 10 dígitos | Formato 0-000-000000 |
| España | NIF | 8 dígitos+letra | Algoritmo módulo 23 |
| España | NIE | X/Y/Z+7 dígitos+letra | Algoritmo específico |
