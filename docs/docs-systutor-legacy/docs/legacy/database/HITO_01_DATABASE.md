# HITO 1 - Base de Datos: Sys_GMS_ESCR

## Información General

| Atributo | Valor |
|---|---|
| **Motor** | Microsoft SQL Server 2014 (12.0.2000.8) |
| **Edición** | Enterprise Edition (64-bit) |
| **Base de datos** | `Sys_GMS_ESCR` |
| **Servidor (desarrollo)** | `ACONCAGUA` |
| **Servidor (cliente)** | `.\SQLEXPRESS` |
| **Usuario** | `sa` |
| **Autenticación** | SQL Server |
| **Proyecto** | ERP-SYSTUTOR (VB.NET WinForms) |
| **Framework** | .NET Framework 4.7.2 |

## Resumen de Objetos

| Tipo | Cantidad |
|---|---|
| **Tablas** | 184 |
| **Vistas** | 144 |
| **Procedimientos almacenados** | 944 |
| **Funciones** | 22 |

## Archivos Generados

| Archivo | Contenido |
|---|---|
| `00_resumen.txt` | Conteo de objetos por tipo |
| `01_tablas.txt` | Listado completo de tablas y vistas (schema, nombre, tipo) |
| `02_stored_procedures.txt` | Todos los SPs y funciones con su definición completa |
| `03_columnas.txt` | Catálogo de columnas (nombre, tipo, longitud, nulleable, tabla) |
| `04_objetos_sys.txt` | Objetos desde `sys.objects` con tipo, fecha de creación/modificación |
| `05_constraints.txt` | Constraints (PK, FK, UNIQUE, CHECK) |

## Conexión (app.config)

```xml
<connectionStrings>
  <add name="ConexionPrincipal"
       connectionString="Data Source=ACONCAGUA;Initial Catalog=Sys_GMS_ESCR;User Id=sa;Password=RedSystutor#2026#;MultipleActiveResultSets=True;"
       providerName="System.Data.SqlClient"/>
</connectionStrings>
```

## Próximos Pasos (pendientes)

- [ ] Explorar tablas principales del negocio
- [ ] Identificar SPs críticos (facturación, cilindros, despachos)
- [ ] Documentar esquemas relacionales clave
- [ ] Analizar vistas de reportes
