# 03 — Arquitectura del Backend FastAPI para SYSTUTOR OSS

## 1. Estructura General del Proyecto

```
systutor-oss-backend/
├── alembic/                    # Migraciones de BD
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Settings
│   ├── database.py             # SQLAlchemy async engine + session
│   ├── dependencies.py         # FastAPI dependencies
│   │
│   ├── models/                 # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py             # Base + mixins (TimestampMixin, AuditMixin)
│   │   ├── core/               # Persona, Producto, Almacen, Movimiento
│   │   ├── glp/                # ECilindroEstadoLog, ECabeceraPedido, etc.
│   │   ├── logistica/          # Agenda, Ruta, Equipos, etc.
│   │   ├── facturacion/        # Comprobante
│   │   └── catalogos/          # Linea, Marca, TipoDoc, ConfigRegional
│   │
│   ├── schemas/                # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── core/
│   │   ├── glp/
│   │   ├── logistica/
│   │   └── facturacion/
│   │
│   ├── repositories/          # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py            # BaseRepository<T> CRUD genérico
│   │   ├── core/
│   │   ├── glp/
│   │   ├── logistica/
│   │   └── facturacion/
│   │
│   ├── services/              # Business logic layer
│   │   ├── __init__.py
│   │   ├── core/
│   │   ├── glp/
│   │   │   ├── cilindro_service.py
│   │   │   ├── envase_pedido_service.py
│   │   │   ├── envase_movimiento_service.py
│   │   │   └── garantia_service.py
│   │   ├── logistica/
│   │   │   ├── planificacion_service.py
│   │   │   ├── agenda_service.py
│   │   │   ├── despacho_service.py
│   │   │   └── adr_service.py
│   │   └── facturacion/
│   │       ├── comprobante_service.py
│   │       ├── facturacion_electronica.py
│   │       └── correlativo_service.py
│   │
│   ├── api/                   # FastAPI routers
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── core/
│   │   │   │   ├── personas.py
│   │   │   │   ├── productos.py
│   │   │   │   ├── almacenes.py
│   │   │   │   └── movimientos.py
│   │   │   ├── glp/
│   │   │   │   ├── cilindros.py
│   │   │   │   ├── envases_pedidos.py
│   │   │   │   ├── garantias.py
│   │   │   │   ├── retimbrados.py
│   │   │   │   └── servicios.py
│   │   │   ├── logistica/
│   │   │   │   ├── agenda.py
│   │   │   │   ├── planificacion.py
│   │   │   │   ├── despacho.py
│   │   │   │   ├── flota.py
│   │   │   │   └── rutas.py
│   │   │   ├── facturacion/
│   │   │   │   ├── comprobantes.py
│   │   │   │   ├── cancelaciones.py
│   │   │   │   └── reportes.py
│   │   │   └── catalogos/
│   │   │       ├── tipos_documento.py
│   │   │       └── configuracion_regional.py
│   │   └── deps.py
│   │
│   ├── core/
│   │   ├── security.py        # JWT, password hashing
│   │   ├── permissions.py     # Role-based access control
│   │   └── exceptions.py      # Custom exceptions + handlers
│   │
│   └── utils/
│       ├── pdf.py             # Report generation
│       ├── csv.py             # CSV export
│       └── validators.py      # Document validators (DNI, RUC, NIF, etc.)
│
├── tests/
│   ├── conftest.py
│   ├── test_core/
│   ├── test_glp/
│   ├── test_logistica/
│   └── test_facturacion/
│
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 2. Capas y Responsabilidades (sin implementación concreta)

### 2.1 API Layer (Routers)
- Validar request con schemas
- Llamar al service correspondiente
- Retornar response sin exponer modelos ORM
- HTTP status codes: 200, 201, 204, 400, 404, 409, 500
- Documentación OpenAPI automática

### 2.2 Service Layer
- Toda la lógica de negocio
- Orquestar llamadas a repositorios
- Manejar transacciones (commit/rollback)
- Validar reglas de negocio (estados, stocks, ADR, PH)
- NO sabe nada de HTTP ni de la API

### 2.3 Repository Layer
- Queries SQL (select, insert, update, delete)
- NO contiene lógica de negocio
- Retorna modelos ORM (luego convertidos a schemas)
- Filtros dinámicos

### 2.4 Model Layer (SQLAlchemy ORM)
- Modelos que reflejan las tablas PostgreSQL
- Usar driver async (asyncpg)
- TimestampMixin: created_at, updated_at automáticos
- AuditMixin: created_by, updated_by

## 3. BaseRepository Genérico

Debe implementar CRUD genérico para cualquier modelo T:
- get_by_id(id) → T | None
- list(skip, limit, **filters) → list[T]
- create(data: dict) → T
- update(id, data: dict) → T | None
- delete(id) → bool

## 4. Manejo de Transacciones (Unit of Work)

Operaciones multi-paso requieren atomicidad. Ejemplos:
- Registrar despacho: cambiar estado de N cilindros + actualizar agenda + crear movimiento
- Escanear cilindro: validar ADR + validar PH + cambiar estado + registrar detalle
- Facturar: crear comprobante + actualizar stock + enviar FE

Patrón: todas las operaciones en un bloque transaccional, commit si todo OK, rollback si falla alguna.

## 5. Dependencias FastAPI

Inyección de dependencias:
- get_db() → sesión asíncrona de BD
- get_current_user() → usuario autenticado vía JWT
- get_X_service() → servicio específico con sus repositorios

## 6. Configuración del Sistema (variables de entorno)

Variables requeridas:
- DATABASE_URL: conexión PostgreSQL async
- SECRET_KEY: clave JWT
- ALGORITHM: algoritmo JWT (HS256)
- ACCESS_TOKEN_EXPIRE_MINUTES: expiración del token (480 por defecto)
- PAIS_CODIGO: país por defecto (PE, CR, ES)
- MONEDA_LOCAL: moneda por defecto
- NUBEFACT_API_URL + TOKEN: para FE Perú
- HACIENDA_CR_API_URL: para FE Costa Rica
- ADR_VALIDAR_POR_DEFECTO: bool

## 7. Manejo de Errores

Tipos de excepción:
- AppException: base, con message + code + status_code
- BusinessRuleError(409): violación de regla de negocio
- NotFoundError(404): entidad no encontrada
- El handler global debe retornar JSON estructurado: {error: code, detail: message}

## 8. SQLAlchemy Model Mixins

- TimestampMixin: created_at (server_default=now()), updated_at (onupdate=now())
- AuditMixin extends TimestampMixin: created_by (FK → usuarios.id), updated_by

## 9. Consideraciones de Performance

1. N+1 queries: usar eager loading (selectinload / joinedload)
2. Paginación obligatoria en listas (limit/offset o cursor)
3. Índices compuestos en ECilindroEstadoLog (serie, fecha DESC)
4. Materialized Views para reportes pesados (stock actual, estado de cilindros)
5. Redis cache opcional para catálogos estáticos (TipoDoc, ConfigRegional)

## 10. Módulos y sus Endpoints Principales

### 10.1 Core
- GET /api/v1/personas — listar con filtros
- POST /api/v1/personas — crear (cliente, proveedor, chofer, etc.)
- GET /api/v1/personas/{id} — detalle
- PUT /api/v1/personas/{id} — actualizar
- GET /api/v1/productos — listar (cilindros, gases, servicios)
- GET /api/v1/productos/{id}/estado-cilindro — estado actual del cilindro
- GET /api/v1/almacenes — listar almacenes
- POST /api/v1/movimientos — crear movimiento
- GET /api/v1/movimientos — listar
- GET /api/v1/movimientos/{id} — detalle con líneas
- PUT /api/v1/movimientos/{id} — actualizar cabecera

### 10.2 GLP
- POST /api/v1/cilindros/cambiar-estado — cambiar estado de cilindro
- GET /api/v1/cilindros/{serie}/historial — historial de estados
- GET /api/v1/cilindros/disponibles?almacen_id=&estado= — cilindros disponibles
- POST /api/v1/pedidos-envases — crear pedido de envase
- GET /api/v1/pedidos-envases/pendientes?almacen_id= — pedidos pendientes
- POST /api/v1/pedidos-envases/{id}/detalle — agregar línea al pedido
- POST /api/v1/garantias — registrar garantía
- POST /api/v1/retimbrados — registrar retimbrado
- GET /api/v1/servicios-cilindros/pendientes — servicios pendientes
- POST /api/v1/cilindros/estado-log/bulk — log batch de estados

### 10.3 Logística
- GET /api/v1/agenda?fecha=&repartidor_id= — agenda del día
- POST /api/v1/agenda — crear tarea
- PUT /api/v1/agenda/{id}/estado — cambiar estado de tarea
- POST /api/v1/planificacion/preparar-carga — generar plan de carga
- POST /api/v1/despacho/escanear — escanear cilindro (usp_Scan_Procesar)
- POST /api/v1/despacho/entregar-cilindro — entregar cilindro individual
- POST /api/v1/despacho/cerrar — cerrar despacho
- GET /api/v1/flota/equipos — listar vehículos
- POST /api/v1/flota/movimientos-asignar — asignar chofer/equipo
- POST /api/v1/adr/validar — validar ADR de un movimiento
- POST /api/v1/adr/seleccionar-camion — seleccionar camión compatible
- GET /api/v1/movimientos/{id}/carta-porte — datos Carta Porte

### 10.4 Facturación
- POST /api/v1/comprobantes — emitir comprobante
- GET /api/v1/comprobantes/{id} — consultar
- POST /api/v1/comprobantes/{id}/enviar-fe — enviar a FE
- POST /api/v1/comprobantes/{id}/anular — anular comprobante
- GET /api/v1/cancelaciones — listar pagos/cancelaciones
- GET /api/v1/reportes/ventas — reporte de ventas
- GET /api/v1/reportes/envases — reporte de envases
- GET /api/v1/reportes/cilindros/estado-actual — reporte cilindros

### 10.5 Catálogos
- GET /api/v1/tipos-documento — tipos de documento con reglas de envase
- GET /api/v1/configuracion-regional — configuración del país activo
- GET /api/v1/menu — menú dinámico por usuario/rol
- GET /api/v1/catalogos/{nombre} — listar catálogo (lineas, marcas, etc.)

### 10.6 Auth
- POST /api/v1/auth/login — login {username, password} → {access_token, token_type, expires_in}
- GET /api/v1/auth/me — datos del usuario autenticado
- GET /api/v1/auth/menu — menú filtrado por rol
- GET /api/v1/auth/almacenes — almacenes asignados al usuario
