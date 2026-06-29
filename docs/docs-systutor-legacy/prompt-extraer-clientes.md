# Prompt para extraer el módulo Clientes del legacy

```
Extrae la informacion completa del modulo CLIENTES del sistema legacy (SQL Server + VB6).

Este modulo esta centrado en la tabla Persona_Nuevo, que es una tabla universal que almacena
clientes (Cod_TipoPersona=1), proveedores (2), empleados (3), repartidores (4) y agentes (5).

## 1. Esquema de base de datos

Para cada tabla del modulo clientes, extrae el DDL completo (CREATE TABLE):

### 1.1 Persona_Nuevo
- Todas las columnas con tipo exacto, nullable, default, identity
- PK, FKs (a Formas_pago, Direccion, EClaves_operacion, etc.)
- Todos los CHECK constraints (especialmente Cod_TipoPersona IN (1,2,3,4,5))
- Indices (especialmente por DNI, RUC, Nom_Persona, Login_Persona)
- Triggers:
  - AFTER INSERT, UPDATE, DELETE
  - Cuerpo completo del trigger
  - Actualiza alguna tabla adicional? (ej: log_auditoria, stock_actual)

### 1.2 Direccion
- DDL completo
- FKs a ZONA, Localidad
- CHECK constraints en Fuente_Geocod, Country_Code
- Triggers si existen

### 1.3 Vehiculo_cliente_nuevo (Puntos de Entrega)
- DDL completo
- FKs a Persona_Nuevo (Id_ClientePersona, Id_Agente_Asignado), ZONA, Almacen, Direccion, Ruta, DatosBancarios
- CHECK constraints en Principal, Activo, Dreparto (dias validos), VentanaHorario (formato HH:MM-HH:MM)

### 1.4 Cliente_Sucursal
- DDL completo
- PK compuesta
- Triggers de auditoria (existe Cliente_Sucursal_Auditoria como tabla separada)

### 1.5 Formas_pago
- DDL completo con todos los registros del catalogo

### 1.6 EClaves_operacion
- DDL completo (solo Espana/EU)

### 1.7 Telefonos, Correos
- DDL de tablas de telefonos/correos adicionales

### 1.8 Creditos
- DDL con columnas de linea de credito, dias de credito, saldo

### 1.9 Direcciones_NoClientes
- DDL completo

## 2. Stored Procedures

Para CADA stored procedure del modulo clientes, extrae el cuerpo completo:

### CRUD Persona (~28 SPs)
- Insertar_Persona_Nuevo -- valida unicidad de RUC/DNI? maneja transaccion? inserta en Direccion tambien?
- Modificar_Persona_Nuevo -- que columnas permite modificar? restringe cambio de Cod_TipoPersona?
- PERSONA_Buscarxcod, xNom, xNom1, xNomVendedor, xdni, xruc, xrucTipo
- Persona_BuscarXfiltro -- CRITICO: parametros exactos, como arma el WHERE dinamico
- MOSTRAR_PERSONA -- JOINs exactos, filtros
- sp_Persona_ActividadFiscal_Guardar -- llama a API externa (SUNAT/Hacienda)?
- Insertar_ClienteProveedor -- diferencia entre cliente y proveedor?
- Personal_Insertar -- asigna automaticamente Cod_TipoPersona=3?
- Actualizar_TARIFAPERSONA -- actualiza Tarifa_cliente?
- BuscarClientesAnotificar -- que condicion define "notificable"?
- Actualizar_estadoOCCliente -- que campo de Persona_Nuevo actualiza?

### CRUD Puntos de Entrega (~12 SPs)
- Insertar_Establecimiento -- como valida que Id_ClientePersona existe? como asigna la zona?
- Vehiculo_cliente_nuevo_SetPrincipal -- logica: setea Principal=0 en los demas puntos del mismo cliente?
- sp_Despacho_ListarPuntosEntrega -- JOINs con rutas, zonas, filtra por activo + habilitado para despacho?

### CRUD Direccion (~8 SPs)
- Direccion_CapturaEnSitio -- llama a API de Google Maps? como almacena lat/lng?
- Direccion_ListarCoordenadasPorCliente -- JOIN Persona_Nuevo + Direccion + Vehiculo_cliente_nuevo

### CRUD Cliente_Sucursal (~8 SPs)
- InsertarClienteSucursal -- valida que el cliente existe y que la sucursal existe?
- ValidarIntegridadClienteSucursal -- que validaciones hace?
- ConsultarAuditoriaClienteSucursal -- JOIN con tabla de auditoria

### Datos Bancarios (~5 SPs)
- DatosBancarios_CambiarCuentaCliente -- mantiene historico?

### Geografia (~2 SPs)
- SucursalGeo_GetDefaults -- que columnas devuelve?

## 3. Vistas y funciones

Para cada vista y funcion que TOQUE Persona_Nuevo, extrae definicion completa:

- Todas las vistas que tengan JOIN a Persona_Nuevo, Direccion o Vehiculo_cliente_nuevo
- Especialmente: vistas usadas por reportes Crystal
- v_ClientesEnRiesgo (mencionada en analisis)
- Cualquier funcion UDF que devuelva datos de persona

## 4. Forms VB6

### FrmCatClientes (818KB -- el mas importante)
Extrae:
- Todos los controles (TABlas, pestanas, textboxes, comboboxes, grids)
- Evento Form_Load: que SPs llama, como inicializa
- Boton Guardar: que validaciones hace ANTES de llamar al SP
- Boton Buscar: que SPs de busqueda usa, como maneja resultados
- Cualquier SQL inline (NO pasado por SP)
- Logica condicional por pais (If pais = "PER" / "CRI" / "ESP")
- Como maneja lblcodigo3 (variable global de contexto)
- Como maneja la geolocalizacion (Google Maps API)

### FrmRegClientePRO (545KB)
- Lo mismo que FrmCatClientes pero especifico para version PRO
- Que campos fiscales adicionales tiene
- Diferencias con FrmCatClientes

### FrmRegClientePLUS (199KB)
- Version simplificada: que campos OMITE vs PRO

### Forms de busqueda:
- FBusPacPRO, FBusPacPLUS, FBusPacPROcr: como arman la busqueda, que columnas muestran
- FBusPacProv: como filtra solo proveedores (Cod_TipoPersona=2)

## 5. Reportes Crystal (.rpt)

Para cada reporte que filtre por cliente:

- CRreporte_persona.rpt
- CRAlmacen_EnvasesXcliente.rpt
- CRDeudasxCobrar.rpt / BACK
- CRAlmacen_EnvasesVencen4a8cliente.rpt
- CRAlmacen_EnvasesVencen9amascliente.rpt
- CRAlmacen_DevolucionesAtiempoXcliente.rpt
- CRFacturacion.rpt / CRFacturacion1.rpt
- CREstadoCtaAdm.rpt
- CRLetras.rpt
- vTICKETFACcliente.rpt

Extrae de cada uno:
- SQL o vista que usa
- Parametros (especialmente filtros por Cod_Persona, fechas)
- Formulas calculadas

## 6. Reglas de negocio

Identifica y describe en texto plano:

### Validacion fiscal por pais
- RUC Peru: algoritmo modulo 11, digito verificador
- DNI Peru: 8 digitos exactos
- Cedula Costa Rica: formato N-NNNN-NNNN
- NIF Espana: modulo 23, letra de control
- Donde esta implementada esta validacion? En SPs, en los forms VB6, o en ambos?

### Reglas de integridad
- Un cliente puede existir sin direccion fiscal? (Id_Direccion_Fiscal nullable)
- Un punto de entrega puede existir sin zona? (Id_Zona NO nullable)
- Se puede cambiar Cod_TipoPersona despues de creado?
- Se puede eliminar un cliente con movimientos asociados?

### Reglas de flujo
- Que pasa cuando se marca un punto como Principal=1?
- Como se determina cliente "en riesgo" (v_ClientesEnRiesgo)?
- Como se asigna un cliente a una sucursal?
- Que validaciones hace CContab.vb cuando hace UPDATE directo a Persona_Nuevo? (bypasea SPs)

## 7. Datos sensibles

Clasifica cada columna:

| Columna | Clasificacion |
|---------|--------------|
| Nom_Persona | Interno |
| Dni_Persona / Ruc_Persona | Sensible -- datos personales |
| mail_Persona / Telefono_Persona | Sensible -- contacto |
| Fotografia | Sensible -- imagen personal |
| Login_Persona / Pass_Persona | Critico -- credenciales (MD5) |
| Datos bancarios (tabla DatosBancarios) | Critico -- financiero |
| Creditos (saldo, linea) | Sensible -- financiero |

## 8. Riesgos de migracion

Para cada elemento, marca con:

- [OK] -> Se mapea 1:1 al nuevo diseno
- [TRANSFORMAR] -> Persona_Nuevo se separa en customers, suppliers, employees, drivers
- [VALIDAR] -> SPs sin body extraido, no sabemos logica exacta
- [OBSOLETO] -> SP_PERSONA_MOSTRARMOZO, crear_personalm, eliminar_personalm
- [DUDA] -> CContab.vb haciendo UPDATE directo; Eliminar_persona_vehiculo inline
- [PENDIENTE] -> No se encontraron triggers ni bodies de SPs; vistas Crystal

## Formato de salida

Devuelve TODO en secciones numeradas, con bloques de codigo SQL para DDL y SPs completos.
No resumas ni interpretes -- transcribe textual. Omite solo si el elemento no existe.
```
