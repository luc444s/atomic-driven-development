# SYSTUTOR OSS — Especificación Técnica para Migración

## Propósito

Documento de especificación técnica detallada para que una sesión independiente de opencode construya **SYSTUTOR OSS** desde cero: un backend **FastAPI + PostgreSQL** que reemplace el legacy **SysTutor VB.NET + SQL Server 2014**.

---

## Índice de Documentos

| # | Archivo | Contenido |
|---|---------|-----------|
| 01 | `01_logica_negocio.md` | Toda la lógica de negocio del sistema legacy: GLP, cilindros, facturación, planificación, ADR, servicios |
| 02 | `02_mapeo_bd.md` | Mapeo completo SQL Server → PostgreSQL: tablas, columnas, tipos, constraints, vistas, TVPs |
| 03 | `03_arquitectura_api.md` | Arquitectura del backend FastAPI: módulos, capas, servicios, repositorios, DTOs |
| 04 | `04_sp_a_api.md` | Traducción de cada stored procedure legacy a endpoints REST, servicios y repositorios |
| 05 | `05_flujos_criticos.md` | Máquinas de estado detalladas, transacciones multi-paso, reglas de validación |
| 06 | `06_seguridad_roles.md` | Autenticación JWT, roles, permisos, menú dinámico por usuario |
| 07 | `07_pendientes_riesgos.md` | Riesgos de migración, datos no documentados, supuestos, deuda técnica |

---

## Stack Objetivo

| Capa | Tecnología |
|------|-----------|
| API | FastAPI (Python 3.12+) |
| ORM | SQLAlchemy 2.0 (async) |
| Migraciones | Alembic |
| BD | PostgreSQL 16 |
| Auth | JWT (python-jose) + OAuth2 |
| Validación | Pydantic v2 |
| Documentación | OpenAPI/Swagger (auto) |
| Tests | pytest + httpx |
| Cache | Redis (opcional, para sesiones) |

---

## Stack Legacy (a reemplazar)

| Capa | Tecnología |
|------|-----------|
| Frontend | VB.NET WinForms (218 forms) |
| Backend | CAtencion DLL (55 clases, ~1,300 métodos) |
| BD | SQL Server 2014 Enterprise |
| Reportes | Crystal Reports (~50 .rpt) |
| Fact. Electrónica | Nubefact/SUNAT API (Perú) |
| FE Costa Rica | Hacienda API (CR) |

---

## Convenciones en este documento

- **`[TABLA.campo]`** → tabla y columna en la BD legacy
- **`→ endpoint()`** → endpoint FastAPI recomendado
- **`// Comentario`** → observación técnica
- **`⚠️`** → riesgo o punto crítico

---

## Orden recomendado de implementación

1. **Core (auth + personas + productos + almacenes)** → base del sistema
2. **Catálogos maestros** → clientes, proveedores, líneas, series, configuraciones
3. **Movimiento + DetalleMovimiento** → núcleo transaccional (reemplaza 70% de la lógica)
4. **Cilindros/Envases** → máquina de estados, trazabilidad, garantías, retimbrado
5. **Planificación + Logística** → agenda, rutas, preparación de carga
6. **Facturación** → comprobantes, FE, reportes
7. **Reportes** → endpoints de datos para dashboards (Crystal → JSON/CSV)
8. **SOLYGAS específico** → carga peligrosa, flota, servicios de cilindros
