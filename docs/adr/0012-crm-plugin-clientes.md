# ADR 0012 - CRM Plugin de Clientes

## Estado

Aceptado

## Contexto

SYSTUTOR OSS tiene un plugin `logistics` completamente funcional con 20+ modelos, maquina de
estados de cilindros, pedidos, rutas, movimientos, agenda, escaneo movil y frontend completo.

Sin embargo, el modulo de clientes no existe. Las tablas de logistics referencian al cliente
como texto libre (`customer_name`) o con un `customer_id` varchar sin FK real. Esto impide:

- rastrear que cilindros pertenecen o han pasado por un cliente especifico;
- validar datos fiscales (RUC, DNI, NIF, Cedula) por pais;
- relacionar ordenes, movimientos y agenda con un cliente real;
- que futuros modulos (facturacion, finanzas, reportes) puedan operar con integridad referencial.

El analisis legacy (`docs/docs-systutor-legacy/modulo_clientes.md`) documenta que
`Persona_Nuevo` es la tabla central del sistema legacy, referenciada por ~30 formularios,
15+ tablas y ~30 reportes Crystal. En el nuevo sistema no existe equivalente.

La seccion 10 del analisis propone separar `Persona_Nuevo` en tablas especificas.
Este ADR concreta esa separacion unicamente para **clientes**, dejando proveedores,
empleados y repartidores para fases posteriores.

## Decision

Se crea el plugin `crm` como modulo de clientes de SYSTUTOR OSS.

### Reglas de diseno

**Alcance (clientes solamente, listo para produccion):**
- el plugin modela clientes (`customers`) con todos los datos fiscales, direcciones,
  contactos, catalogos y validaciones que el sistema legacy tenia para clientes;
- no incluye proveedores, empleados ni repartidores;
- el kernel `users` ya cubre empleados/repartidores para autenticacion;
- proveedores se postengan hasta que exista un modulo `purchasing`;
- el modulo debe ser completo, funcional y validado con pruebas antes de darse por terminado.

**No es tabla universal:**
- a diferencia del legacy `Persona_Nuevo`, no existe una sola tabla para todos los tipos;
- `customers` tiene columnas especificas de cliente (RUC, DNI, actividad fiscal, etc.);
- si en el futuro se necesita `suppliers`, se crea otra tabla separada.

**El plugin es requisito obligatorio de logistics:**
- logistics declara `"requires": ["crm"]` en su `plugin.json`;
- el runtime de plugins debe instalar y habilitar `crm` antes que `logistics`;
- las 6 tablas de logistics con `customer_name` texto se migran a FK real.

**Direcciones como tabla separada con geolocalizacion:**
- `customer_addresses` es la fuente de verdad de todas las direcciones del cliente,
  incluida la direccion fiscal;
- `crm_customers.fiscal_address_id` apunta a una fila de `crm_customer_addresses`;
- soporta geolocalizacion completa: latitud, longitud, place_id Google Maps,
  formatted_address, street_name, street_number, country_code, admin areas;
- una direccion pertenece a un solo cliente;
- el cliente tiene exactamente una direccion fiscal via `fiscal_address_id`.

**Puntos de entrega siguen viviendo en logistics:**
- el equivalente operativo de `Vehiculo_cliente_nuevo` permanece en `logistics`;
- `crm` no crea una tabla paralela de puntos de entrega;
- `crm` provee el cliente y sus direcciones; `logistics` administra la operacion
  de entrega (zona, ruta, almacen, ventana horaria, demanda, etc.);
- `lg_delivery_points.customer_name` se elimina;
- `lg_delivery_points.customer_id` pasa a ser FK real NO NULL a `crm_customers`;
- se agrega `lg_delivery_points.address_id` FK opcional a `crm_customer_addresses`;
- se agregan o consolidan los campos legacy faltantes: `warehouse_id`,
  `contact_name`, `contact_phone`, `contact_email`, `visit_day`, `time_window`,
  `service_time_min`, `demand_units`, `demand_weight_kg`, `instructions`,
  `agent_user_id`, `fiscal_operation_document`, `fiscal_operation_type`.

**Ruta asignada de punto de entrega:**
- el legacy tiene `Id_RutaAsignada`, pero el `lg_routes` actual representa rutas
  operativas fechadas, no un catalogo maestro persistente;
- en esta iteracion NO se agrega `route_id` en `lg_delivery_points`;
- la relacion estable se resuelve por `zone_id` y la asignacion concreta ocurre en la
  planificacion diaria de logistics.

**Catalogos completos (no minimos):**
- `crm_document_types` — tipos de documento (RUC, DNI, NIF, Cedula Fisica,
  Cedula Juridica, NIE, DIMEX, NITE, Pasaporte, Otro);
- `crm_payment_terms` — formas de pago (Contado, Credito 15d, Credito 30d,
  Credito 60d, Tarjeta, Transferencia, Cheque);
- `crm_geography` — tabla jerarquica auto-referenciada global para paises, departamentos,
  provincias, distritos y localidades, con codigo ubigeo (Peru) y codigo ISO.

**Validacion fiscal completa:**
- se implementa en el servicio `fiscal_validator.py`, no en la BD;
- Peru: RUC (11 digitos, algoritmo modulo 11 con pesaje por posicion),
  DNI (8 digitos exactos);
- Costa Rica: Cedula Fisica (formato 0-0000-0000),
  Cedula Juridica (formato 0-000-000000);
- Espana: NIF (modulo 23, tabla de letras de control),
  NIE (X/Y/Z + 7 digitos + letra modulo 23);
- la validacion contra SUNAT/Hacienda (API externa) se postenga a fase de facturacion.

**Busqueda poderosa:**
- el endpoint de busqueda debe soportar filtros por: nombre, RUC, DNI, telefono,
  email, codigo externo, pais, tipo de documento, activo/inactivo;
- debe soportar busqueda por aproximacion (ILIKE) y paginacion;
- respuesta incluye: id, nombre, documento, tipo_documento, telefono, email,
  direccion_fiscal, pais, activo.

**Frontend completo con componente reusable de busqueda:**
- pagina de listado con tabla, filtros y paginacion;
- pagina de formulario multi-pestana (datos generales, direccion fiscal,
  puntos de entrega, contactos, observaciones);
- pagina de detalle con historial de movimientos (lectura desde logistics);
- `CustomerSearchDialog` como modal de busqueda parametrizable para que
  cualquier plugin (logistics, billing) pueda seleccionar un cliente;
- el modal debe soportar: busqueda por texto, seleccion unica, callback onSelect,
  mostrar nombre + documento + direccion en resultados.

**Refactor completo de logistics:**
- las 6 tablas con `customer_id` huerfano se migran a FK real;
- los servicios de logistics se actualizan para recibir `customer_id` en lugar de
  `customer_name` texto;
- los endpoints de logistics que crean ordenes, movimientos, agenda, etc. deben
  validar que el `customer_id` exista en `crm_customers`;
- el frontend de logistics reemplaza todos sus `<Input customer_name>` por
  el `CustomerSearchDialog`.

**Politica de denormalizacion de nombre del cliente:**
- `lg_delivery_points` deja de almacenar `customer_name` porque es un dato maestro actual;
- tablas transaccionales (`lg_orders`, `lg_movements`, `lg_agenda_tasks`,
  `lg_cylinder_warranties`, `lg_cylinder_ownership`) conservan `customer_name`
  como snapshot historico de solo lectura.

**No toca el core:**
- este cambio no modifica arquitectura global, auth, RBAC, tenancy, event bus,
  runtime de plugins ni modelos base del kernel;
- el plugin `crm` solo reutiliza infraestructura estable del core (`tenants`, `users`,
  auditoria, permisos, runtime) y extiende el dominio de negocio via plugin;
- cualquier refactor se limita a `plugins/crm/` y a los puntos de integracion de
  `plugins/logistics/` que hoy dependen de cliente.

### Arquitectura del plugin

```
plugins/crm/
├── plugin.json
├── backend/
│   ├── __init__.py
│   ├── plugin.py                  # register()
│   ├── router.py                  # FastAPI router con todos los endpoints
│   ├── schemas.py                 # Pydantic request/response completos
│   ├── models.py                  # SQLAlchemy ORM completo
│   └── services/
│       ├── __init__.py
│       ├── customers.py           # CRUD + busqueda avanzada
│       ├── addresses.py           # CRUD de direcciones + fiscal_address_id
│       ├── fiscal_validator.py    # Validacion de documentos por pais
│       ├── geography.py           # Geografia departamental jerarquica
│       └── search.py              # Busqueda multi-criterio optimizada
├── frontend/
│   ├── register.ts                # Plugin frontend entrypoint
│   ├── api.ts                     # API client + query keys + tipos TS
│   ├── pages/
│   │   ├── CustomersListPage.tsx  # Listado con tabla y filtros
│   │   ├── CustomerFormPage.tsx   # Crear/editar con pestanas
│   │   └── CustomerDetailPage.tsx # Detalle con historial y acceso a delivery points
│   ├── components/
│   │   ├── CustomerSearchDialog.tsx   # Modal de busqueda reusable
│   │   ├── CustomerInfoCard.tsx       # Resumen visual del cliente
│   │   ├── AddressSection.tsx         # Formulario de direccion
│   │   ├── FiscalInfoSection.tsx      # Seccion de datos fiscales
│   │   ├── ContactSection.tsx         # Telefonos y correos
│   │   └── DeliveryPointsSection.tsx  # Vista embebida de delivery points desde logistics
│   └── types.ts                  # Interfaces compartidas
├── migrations/
│   ├── 001_initial_crm.py        # Tablas del CRM
│   ├── 002_geography_seed.py     # Geografia base
│   └── 003_refactor_logistics.py # Migracion de FKs y delivery points en logistics
├── permissions/
│   └── __init__.py
├── events/
│   └── __init__.py
└── README.md
```

### Migracion de datos legacy

No hay migracion de datos legacy del SQL Server en esta etapa.
El plugin opera con datos nuevos creados desde la aplicacion.

El migrador legacy (`tools/migrator/`) se actualizara separadamente con manifiestos CSV
para clientes (siguiendo ADR 0006) cuando se defina la migracion del dominio clientes.

## Consecuencias

**Positivas:**
- logistics obtiene integridad referencial real hacia clientes;
- el CustomerSearchDialog es reusable por cualquier plugin futuro (billing, purchasing);
- la validacion fiscal por pais vive en un solo lugar y es testeable unitariamente;
- la separacion cliente/proveedor/empleado evita el problema de tabla universal del legacy;
- el modulo queda listo para produccion, no como piloto experimental.

**Negativas:**
- logistics requiere migracion de datos (pasar customer_name texto a FK real);
- los datos existentes en tablas de logistics sin customer_id real requeriran creacion
  de clientes "fantasma" para mantener la integridad;
- el frontend de logistics (OrdersPage, MovementsPage, DeliveryPointsPage, AgendaPage,
  WarrantySection) debe actualizarse para usar CustomerSearchDialog;
- los servicios de logistics que hoy reciben customer_name deben cambiar su firma.

**Riesgos:**
- si la migracion de logistics no se ejecuta en el orden correcto, las FKs fallan
  y el plugin no puede habilitarse;
- la validacion fiscal sin conexion a SUNAT/Hacienda es solo de formato, no de existencia real;
- la geografia departamental puede ser extensa (194 provincias, 1874 distritos en Peru);
  se recomienda sembrar solo paises y dejar la carga de geografia para el seed de cada tenant.

## Dependencias

- runtime de plugins (existe y funciona, probado con logistics);
- kernel: auth JWT, multi-tenant, RBAC, auditoria, event bus;
- logistics plugin: debe declarar `"requires": ["crm"]`.

## Referencias

- ADR 0004: Runtime de Plugins
- ADR 0010: Logistics como Plugin Piloto
- SPEC 0011: Logistics Pilot Module
- `docs/docs-systutor-legacy/modulo_clientes.md`
- `docs/adr/0003-modelo-tenancy-permisos.md`
- `docs/adr/0006-migracion-legacy-csv-manifest.md`
