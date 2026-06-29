# Módulo Clientes — Reglas de Negocio

## 1. Validación Fiscal por País

### 1.1 Perú — RUC (11 dígitos)

- **Formato:** 11 dígitos exactos
- **Algoritmo:** Módulo 11 con dígito verificador
- **Validación:** Implementada en `ClsValidaciones.ValidarDocumento()` (llamado desde FrmCatClientes y FrmRegClientePRO)
- **SP relacionado:** `PERSONA_Buscarxruc` busca por RUC

### 1.2 Perú — DNI (8 dígitos)

- **Formato:** 8 dígitos exactos
- **Validación:** Longitud y numérico en `ClsValidaciones.ValidarDocumento()`
- **SP relacionado:** `PERSONA_Buscarxdni` busca por DNI
- **DAL:** `obj.BuscarDNI(txtDni.Text)` en `GuardarDatosBasicos_Nuevo()` evita duplicados

### 1.3 Costa Rica — Cédula

- **Cédula Física:** Formato `N-NNNN-NNNN` (1 dígito - 4 dígitos - 4 dígitos)
- **Cédula Jurídica:** Formato `N-NNN-NNNNNN` (1 dígito - 3 dígitos - 6 dígitos)
- **Validación:** En `ClsValidaciones.ValidarDocumento()`
- **Diferencia en UI:** FBusPacPROcr usa `BuscarClientexnomFiscal` (no `BuscarClientProvxnom`)

### 1.4 España — NIF (8+1 letra)

- **Formato:** 8 dígitos + letra de control
- **Algoritmo:** Módulo 23 (letra se calcula del resto)
- **Letras válidas:** "TRWAGMYFPDXBNJZSQVHLCKE"
- **NIE:** X/Y/Z + 7 dígitos + letra de control
- **Validación IBAN:** España usa IBAN de 24 caracteres (ES + 22 dígitos con MOD 97-10)
- **Implementación:** En `ValidarIBAN_Pro()` y `EsIBAN_ES_Valido()` dentro de FrmCatClientes/FrmRegClientePRO

### 1.5 ¿Dónde se implementan las validaciones?

| Validación | En SPs | En Forms VB | En DAL (CPaciente) |
|-----------|--------|------------|-------------------|
| RUC 11 dígitos | ❌ (solo busca) | ✅ ClsValidaciones | ❌ |
| DNI 8 dígitos | ❌ (solo busca) | ✅ ClsValidaciones | ❌ (solo busca) |
| Cédula CR | ❌ | ✅ ClsValidaciones | ❌ |
| NIF España | ❌ | ✅ ClsValidaciones | ❌ |
| IBAN España | ❌ | ✅ ValidarIBAN_Pro | ❌ |
| CCI Perú | ❌ | ✅ ValidarCCI_Peru_Real | ❌ |

**Conclusión:** TODA la validación fiscal está implementada exclusivamente en los forms VB (capa de presentación), NO en SPs ni en la DAL.

---

## 2. Reglas de Integridad

### 2.1 Cliente sin dirección fiscal

- `Id_Direccion_Fiscal` en `Persona_Nuevo` es NULLable
- **SÍ puede existir** un cliente sin dirección fiscal
- El form advierte: `"Este será el punto principal (Dirección fiscal)"` al crear el primer punto de entrega
- `ClienteTieneDireccionFiscal()` verifica con `SELECT TOP 1 1 FROM Persona_Nuevo WHERE Cod_Persona = @cod AND Id_Direccion_Fiscal IS NOT NULL`

### 2.2 Punto de entrega sin zona

- `Id_Zona` en `Vehiculo_cliente_nuevo` es **NOT NULL**
- **NO puede existir** un punto de entrega sin zona asignada
- La zona es obligatoria al insertar un establecimiento

### 2.3 Cambio de Cod_TipoPersona

- El SP `Modificar_Persona_Nuevo` permite cambiar `Cod_TipoPersona`
- No hay restricción explícita en el SP
- **Riesgo:** Un cliente (tipo 1) podría convertirse en proveedor (tipo 2) o viceversa
- En los forms, `opc = 1` siempre inserta como cliente (Cod_TipoPersona=1)

### 2.4 Eliminación de cliente con movimientos

- **No hay DELETE en Persona_Nuevo** — solo se marca `Activo = 0`
- Los SPs de eliminación no existen para Persona_Nuevo
- **Un cliente "eliminado"** sigue siendo referenciado por movimientos, facturas, etc.

---

## 3. Reglas de Flujo

### 3.1 Marcar punto como Principal

1. `Vehiculo_cliente_nuevo_SetPrincipal` o `sp_PuntoEntrega_EstablecerPrincipal`
2. Marca `Principal = 1` en el punto seleccionado
3. **NO desmarca automáticamente** los otros puntos del mismo cliente (según código VB: solo admin puede cambiar, `CheckPrincipal_CheckedChanged` verifica permisos)
4. El SP debería hacer `UPDATE Vehiculo_cliente_nuevo SET Principal = 0 WHERE Id_ClientePersona = @id` antes de marcar el nuevo

### 3.2 Cliente "en riesgo" (v_ClientesEnRiesgo)

- Vista no documentada (sin CREATE VIEW)
- Probable lógica: clientes cuyo saldo deudor excede la línea de crédito (`Creditos.Linea_Credito`)
- Columnas probables: `Cod_Persona`, `Nom_Persona`, `Linea_Credito`, `Saldo_Actual`, `Dias_Credito`, `Dias_Vencidos`

### 3.3 Asignación a sucursal

1. `InsertarClienteSucursal` vincula `Id_Cliente` (Codigo de Vehiculo_cliente_nuevo) con `Id_Sucursal` (Cod_Almacen)
2. La FK apunta a `Vehiculo_cliente_nuevo`, no a `Persona_Nuevo`
3. Esto significa que la asignación a sucursal se hace a través del punto de entrega, no directa al cliente

### 3.4 Actualizaciones directas (bypass)

- En `CPaciente.vb` (DAL): **NO se encontró bypass** — todos los INSERT/UPDATE a Persona_Nuevo pasan por SPs
- El riesgo documentado de `CContab.vb` no se pudo verificar (no se leyó ese archivo)
- Las únicas actualizaciones directas encontradas son en los forms:
  ```vb.net
  "Update persona Set fotografia=@fotografia WHERE cod_persona = '" & TxtCodPac.Text & "'"
  ```

---

## 4. Tipos de Persona (Cod_TipoPersona)

| Código | Tipo | Uso |
|--------|------|-----|
| 1 | Cliente | Comprador de productos/servicios |
| 2 | Proveedor | Vendedor de insumos (tabla compartida) |
| 3 | Empleado | Trabajador interno (Personal_Insertar) |
| 4 | Repartidor | Empleado con función de reparto |
| 5 | Agente/Vendedor | Fuerza de ventas externa |

---

## 5. Formas de Pago

| Id | Descripción | Tipo | Plazo | Requiere Autorización |
|----|------------|------|-------|---------------------|
| 1 | Contado | CONTADO | 0 | No |
| 2 | Crédito 15 días | CREDITO | 15 | No |
| 3 | Crédito 30 días | CREDITO | 30 | No |
| 4 | Crédito 60 días | CREDITO | 60 | No |
| 5 | Tarjeta | TARJETA | 0 | Sí |
| 6 | Transferencia | TRANSFERENCIA | 0 | No |

---

## 6. Punto de Entrega — Reglas Operativas

1. Un cliente puede tener **1..N puntos de entrega** (Vehiculo_cliente_nuevo)
2. Cada punto tiene **1 dirección** (Id_Direccion → Direccion)
3. Cada punto pertenece a **1 zona de reparto** (Id_Zona → ZONA, NOT NULL)
4. Cada punto puede tener **1 ruta asignada** (Id_RutaAsignada → Ruta)
5. `Principal = 1` marca el punto por defecto
6. `Dreparto` y `Dvisita` aceptan solo: LUNES, MARTES, MIÉRCOLES, JUEVES, VIERNES, SÁBADO, DOMINGO (CHECK constraint)
7. `VentanaHorario` almacena formato libre (sin CHECK constraint de formato)
8. La entrega física se hace en el punto de entrega, no en la dirección fiscal
