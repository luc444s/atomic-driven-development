# A.SPEC API-REST-CON-0001 — Scaffold ERP-SYSTUTOR.API (VB.NET 3.5, HttpListener)

## WHY
Python TMS necesita leer datos legacy sin tocar SQL Server. Se requiere una
superficie de API en VB que sea el único puente permitido.

## WHAT
Nuevo proyecto VB.NET 3.5 `ERP-SYSTUTOR.API` dentro de la solución ERP-SYSTUTOR,
auto-host con `HttpListener` en `http://+:8080/api/`, que reusa
`ClsConexion.ConnectionString()` para llegar a SQL Server (Linux Mint).

## SCOPE
- Creación de `ERP-SYSTUTOR.API.vbproj` + `Program.vb` con listener arrancado.
- Endpoint de salud `GET /api/health` → `200 {"status":"ok"}`.

## OUT OF SCOPE
- Lógica de negocio y transformación de datos (A.SPEC 0002+).
- Autenticación (A.SPEC 0004).
- Endpoints de datos (A.SPEC 0002, 0003).

## CONTRACT
- Al iniciar, el listener acepta conexiones en `:8080`.
- `GET /api/health` responde `200 application/json` con `{"status":"ok"}`.

## INVARIANTS
- No modifica el ERP existente (solo proyecto hermano en la solución).
- No conecta TMS/Systutor a SQL Server; el API sí, porque es el legacy.
- Reusa únicamente `ClsConexion` en modo lectura.

## VERIFICATION
- Build del `.vbproj` (VB.NET 3.5) sin errores.
- Ejecutar el exe en Win10; `curl http://localhost:8080/api/health` → `200`.

## ROLLBACK
- Quitar el proyecto del `.sln` y detener el exe. Sin efecto en BD legacy.

## CHANGE SURFACE
```yaml
allowed:
  - ERP-SYSTUTOR.API/Program.vb
  - ERP-SYSTUTOR.API/ERP-SYSTUTOR.API.vbproj
  - ERP-SYSTUTOR.API/app.config
prohibited:
  - plugins/**
  - kernel/**
  - apps/api/app/kernel/**
```

## BLAST RADIUS
```yaml
direct:
  - superficie API en Win10 (:8080)
indirect:
  - consumidores futuros en Systutor
must_not_affect:
  - app ERP-SYSTUTOR (WinForms)
  - datos SQL Server
  - Python/Systutor runtime
```
