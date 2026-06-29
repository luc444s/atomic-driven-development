# Módulo Clientes — Datos Sensibles

## Clasificación de Columnas

### Tabla Persona_Nuevo

| Columna | Clasificación | Tipo de Dato | Notas |
|---------|--------------|-------------|-------|
| `Cod_Persona` | Interno | int (PK) | ID interno del sistema |
| `Nro_Persona` | Interno | nvarchar(50) | Código externo del cliente |
| `Nom_Persona` | Interno | nvarchar(200) | Razón social |
| `Dni_Persona` | **Sensible — Identificación personal** | nvarchar(20) | DNI Perú |
| `Ruc_Persona` | **Sensible — Identificación fiscal** | nvarchar(20) | RUC / NIF / Cédula |
| `Cod_TipoPersona` | Interno | int | 1=Cliente, 2=Proveedor... |
| `Sexo_Persona` | **Sensible — Dato personal** | nvarchar(10) | |
| `FNac_Personal` | **Sensible — Dato personal** | date | Fecha de nacimiento |
| `mail_Persona` | **Sensible — Contacto** | nvarchar(100) | Correo electrónico |
| `Telefono_Persona` | **Sensible — Contacto** | nvarchar(50) | Teléfono |
| `Activo` | Interno | bit | 1=Activo |
| `Login_Persona` | **Crítico — Credencial** | nvarchar(50) | Login del sistema |
| `Pass_Persona` | **Crítico — Credencial** | nvarchar(50) | **MD5 (inseguro)** |
| `Nick_Persona` | Interno | nvarchar(50) | Apodo |
| `Fotografia` | **Sensible — Imagen personal** | nvarchar(50) | Ruta de archivo |
| `id_clave_Operacion` | Interno | int (FK) | Clave de operación España |
| `clave_op_intracomunitaria` | Interno | bit | Intracomunitario EU |
| `nombre_comercial` | Interno | varchar(100) | Nombre comercial |
| `observaciones` | Interno | nvarchar(MAX) | Notas internas |
| `Documento_Principal` | **Sensible — Identificación** | nvarchar(50) | Documento principal |
| `Tipo_facturacion` | Interno | nvarchar(50) | "mensual", "por_operacion" |
| `Id_FormaPago` | Interno | int (FK) | Forma de pago por defecto |
| `Id_Direccion_Fiscal` | Interno | int (FK) | Dirección fiscal |
| `PaisCodigo` | Interno | varchar(5) | PER, ESP, CRI |
| `TipoIdentificacionFiscal` | **Sensible — Identificación** | varchar(20) | RUC, DNI, NIF, etc. |
| `NumeroIdentificacionFiscal` | **Sensible — Identificación fiscal** | varchar(30) | Documento fiscal |
| `CodigoActividadPrincipal` | Interno | varchar(20) | Código SUNAT/Hacienda |
| `DescripcionActividadPrincipal` | Interno | nvarchar(300) | Descripción de actividad |
| `ActividadValidada` | Interno | bit | Validación fiscal |
| `FechaValidacionActividad` | Interno | datetime | Cuándo se validó |
| `FuenteValidacionActividad` | Interno | varchar(50) | SUNAT, HACIENDA_CR, MANUAL |

### Tabla Direccion

| Columna | Clasificación | Notas |
|---------|--------------|-------|
| `Linea1` | Sensible — Domicilio | Dirección exacta |
| `Linea2` | Sensible — Domicilio | Complemento |
| `Codigo_Postal` | Interno | |
| `Latitud` | Sensible — Geolocalización | Coordenadas exactas |
| `Longitud` | Sensible — Geolocalización | Coordenadas exactas |
| `Formatted_Address` | Sensible — Domicilio | Dirección completa Google |

### Tabla Vehiculo_cliente_nuevo

| Columna | Clasificación | Notas |
|---------|--------------|-------|
| `Direccion` | Sensible — Domicilio | Dirección del punto |
| `Contacto` | Sensible — Contacto | Nombre del contacto |
| `Telefono` | Sensible — Contacto | Teléfono del punto |
| `Correoresp` | Sensible — Contacto | Correo del responsable |
| `Enlace_GPS` | Sensible — Geolocalización | Link a Maps |

### Tabla Creditos

| Columna | Clasificación | Notas |
|---------|--------------|-------|
| `Linea_Credito` | **Sensible — Financiero** | Línea de crédito |
| `Dias_Credito` | Sensible — Financiero | Plazo de crédito |

### Tabla DatosBancarios (no DDL disponible en docs)

| Columna | Clasificación | Notas |
|---------|--------------|-------|
| `Numero_Cuenta` | **Crítico — Financiero** | Número de cuenta/IBAN/CCI |
| `Codigo_BIC` | **Crítico — Financiero** | Código BIC/SWIFT |
| `Forma_Pago` | Sensible — Financiero | Forma de pago asociada |

---

## Resumen de Clasificación

| Nivel | Columnas | Riesgo |
|-------|----------|--------|
| **Crítico** | `Pass_Persona`, datos bancarios (cuenta, BIC) | Exposición financiera/credenciales — MD5 inseguro |
| **Sensible** | DNI, RUC, mail, teléfono, dirección, coordenadas, foto, contacto, crédito | Datos personales y fiscales — requiere cifrado |
| **Interno** | Códigos, flags, fechas de sistema, IDs | Bajo riesgo, uso interno |
