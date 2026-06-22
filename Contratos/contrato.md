# contrato.md

# Contrato Fundacional de SYSTUTOR OSS

**Versión:** 0.1  
**Estado:** Documento inicial de dirección técnica y filosófica  
**Proyecto:** SYSTUTOR OSS  
**Empresa futura:** Censoria / TutoraBusiness Group  
**Autoría conceptual:** Lucas y equipo SYSTOR:Propósito 

---

## 0. Propósito del documento

Este documento establece el contrato inicial para el nacimiento de **SYSTUTOR OSS**, la nueva generación de SYSTUTOR.

Su objetivo es definir la filosofía, arquitectura, tecnologías, metodología de programación, estrategia de migración y etapas de desarrollo del proyecto.

SYSTUTOR OSS no nace como una simple reescritura del sistema legacy en otra tecnología. Nace como una evolución profunda del producto, tomando todo el conocimiento operativo acumulado en SYSTUTOR Legacy y transformándolo en una plataforma moderna, abierta, auditable, observable, modular y preparada para crecer durante décadas.

Este documento debe servir como guía para programadores, agentes de IA, colaboradores, futuros mantenedores y clientes técnicos que necesiten comprender hacia dónde se dirige el proyecto.

---

# 1. Filosofía de SYSTUTOR OSS

## 1.1. SYSTUTOR OSS no es solo un ERP

SYSTUTOR OSS no debe entenderse únicamente como un ERP tradicional.

El objetivo es construir una **plataforma empresarial modular**, capaz de alojar múltiples dominios de negocio como logística, inventario, ventas, facturación, CRM, reportes, automatización, IA e integraciones.

El ERP será una consecuencia de los módulos instalados, no la definición completa del sistema.

SYSTUTOR OSS debe funcionar como una base extensible sobre la cual puedan construirse soluciones empresariales específicas sin depender de estructuras rígidas ni de lógica oculta.

---

## 1.2. El legado no se descarta: se absorbe

SYSTUTOR Legacy, construido en VB.NET, SQL Server y Crystal Reports, no debe verse como un error.

SYSTUTOR Legacy representa años de conocimiento real de negocio, flujos operativos, casos borde, reglas empresariales y experiencia acumulada en producción.

La meta de SYSTUTOR OSS no es borrar ese pasado, sino **absorberlo progresivamente**, de forma controlada y sin poner en riesgo la operación actual.

El proceso debe parecerse a una transición progresiva de plataforma:

```text
SYSTUTOR legacy
Coexistenci
Coexistencia controlada
    ↓
Absorción progresiva por dominios
    ↓
SYSTUTOR OSS como núcleo principal
```

La migración no será un cambio brusco. Será una evolución gradual.

---

## 1.3. Soberanía tecnológica empresarial

SYSTUTOR OSS promueve que las empresas mantengan control real sobre su tecnología.

El proyecto rechaza la dependencia de:

- software cerrado imposible de auditar;
- licencias abusivas;
- proveedores cautivos;
- bases de datos llenas de lógica oculta;
- sistemas que no pueden ser modificados ni entendidos;
- software crackeado como base operativa empresarial;
- tecnologías con telemetría invasiva o dependencia innecesaria de terceros.

La empresa debe poder:

- conocer cómo funciona el sistema;
- auditar sus datos;
- modificar el software;
- alojarlo donde desee;
- migrar cuando sea necesario;
- mantener continuidad aunque cambie de proveedor.

---

## 1.4. Anti Stored Procedures y anti Triggers como filosofía final

SYSTUTOR OSS nace con una filosofía clara:

> La lógica de negocio debe vivir en código auditable, observable, testeable y versionable.

Por lo tanto, como arquitectura final, se rechaza depender de:

- Stored Procedures con lógica de negocio crítica;
- Triggers ocultos;
- automatismos invisibles en base de datos;
- efectos secundarios no documentados;
- reglas repartidas entre SQL, UI y reportes.

Esto no significa que el legacy pueda eliminar esa lógica desde el primer día. Significa que la dirección final del proyecto será extraer progresivamente esa lógica hacia servicios claros en Python.

La base de datos debe almacenar datos e imponer integridad estructural. La lógica de negocio debe estar en servicios de dominio, eventos, validadores, políticas y workflows observables.

---

## 1.5. Observabilidad como característica principal

SYSTUTOR OSS debe poder responder siempre:

- qué ocurrió;
- cuándo ocurrió;
- quién lo hizo;
- desde dónde se hizo;
- qué datos cambiaron;
- qué módulo ejecutó la acción;
- qué evento se generó;
- qué proceso se disparó después.

La observabilidad no será un agregado posterior. Será una característica base.

Toda acción importante debe generar auditoría y eventos.

---

## 1.6. Kernel pequeño, módulos grandes

El núcleo de SYSTUTOR OSS no debe contener lógica pesada de negocio.

El Kernel debe proveer infraestructura:

- autenticación;
- permisos;
- usuarios;
- tenants;
- configuración;
- runtime de plugins;
- event bus;
- auditoría;
- observabilidad;
- almacenamiento;
- WebSockets;
- tareas en segundo plano;
- API Gateway;
- sistema de migraciones de módulos.

El Kernel no debe saber qué es una factura, una entrega, un cilindro, un cliente o una ruta.

Esos conceptos pertenecen a módulos.

---

## 1.7. Todo debe ser modular

SYSTUTOR OSS debe permitir instalar, activar, desactivar y evolucionar módulos de forma controlada.

Ejemplos de módulos:

- logística;
- inventario;
- ventas;
- facturación;
- CRM;
- reportes;
- IA;
- workflows;
- integraciones;
- LibreFact/OpenFact.

Cada módulo debe declarar:

- rutas backend;
- pantallas frontend;
- permisos;
- eventos;
- migraciones;
- configuraciones;
- dependencias;
- documentación mínima.

---

## 1.8. Eventos antes que acoplamiento

Los módulos no deben comunicarse mediante imports directos innecesarios.

La comunicación entre dominios debe ocurrir mediante eventos.

Ejemplos:

```text
customer.created
invoice.created
logistics.delivery.completed
inventory.stock.updated
payment.received
```

Esto permitirá:

- desacoplar módulos;
- agregar automatizaciones;
- conectar IA;
- construir dashboards en tiempo real;
- auditar flujos;
- crear integraciones externas.

---

## 1.9. Open Core real

SYSTUTOR OSS debe nacer con una filosofía abierta real.

La edición abierta no debe ser una versión mutilada artificialmente. Debe ser útil, seria y respetada.

La monetización futura no debe basarse en esconder lo esencial, sino en ofrecer valor adicional:

- cloud oficial;
- soporte;
- implementaciones;
- módulos premium;
- IA avanzada;
- observabilidad avanzada;
- integraciones enterprise;
- marketplace;
- capacitación;
- mantenimiento.

---

## 1.10. Diseño global desde el día cero

SYSTUTOR OSS no debe ser diseñado como un sistema de un solo país.

Debe poder funcionar en Perú, Costa Rica, España, Australia o cualquier otro país mediante configuración y módulos regionales.

El Kernel debe ser neutral respecto a:

- impuestos;
- monedas;
- idiomas;
- formatos legales;
- facturación electrónica;
- reglas fiscales locales.

Las reglas regionales deben vivir en módulos o adaptadores.

---

## 1.11. LibreFact/OpenFact como proyecto independiente

La facturación electrónica no debe quedar enterrada dentro del ERP.

LibreFact/OpenFact debe existir como infraestructura fiscal independiente, reutilizable por SYSTUTOR OSS y por otros sistemas.

SYSTUTOR OSS podrá consumir LibreFact como módulo o servicio, pero no debe acoplar todo su núcleo a una normativa fiscal específica.

---

# 2. Tecnología a usar

## 2.1. Backend

El backend principal de SYSTUTOR OSS será construido con:

- **Python** como lenguaje principal;
- **FastAPI** como framework web;
- **Pydantic** para validación y contratos de datos;
- **SQLAlchemy 2.x** como ORM principal;
- **Alembic** para migraciones;
- **PostgreSQL** como base de datos principal del nuevo sistema;
- **Redis** para colas, cache, locks ligeros y coordinación cuando sea necesario;
- **WebSockets** para tiempo real;
- **workers async** para importaciones, reportes, tareas pesadas y procesos de fondo;
- **pytest** para pruebas automatizadas.

PostgreSQL será el centro de gravedad de SYSTUTOR OSS.

SQL Server será tratado como fuente legacy durante la etapa de transición, no como base final de la nueva arquitectura.

---

## 2.2. Frontend

El frontend será construido con:

- **React** como biblioteca principal de interfaz;
- **Vite** como herramienta de build;
- **TypeScript** como lenguaje del frontend;
- **TanStack Query** para sincronización cliente-servidor;
- **Zustand** para estado local modular;
- **React Router** para navegación;
- **Tailwind CSS** para estilos;
- **shadcn/ui** o sistema similar para componentes base;
- arquitectura preparada para módulos frontend registrables.

El frontend no debe ser una colección rígida de pantallas.

Debe funcionar como una shell extensible donde cada módulo pueda registrar:

- rutas;
- menús;
- dashboards;
- widgets;
- permisos visuales;
- páginas;
- acciones rápidas.

---

## 2.3. Base de datos

La base principal del nuevo sistema será PostgreSQL.

Se usará PostgreSQL para:

- datos del Kernel;
- usuarios;
- permisos;
- módulos;
- auditoría;
- eventos;
- configuraciones;
- nuevos dominios migrados;
- datos operativos OSS.

SQL Server se mantendrá durante la transición como base de SYSTUTOR Legacy.

No se permitirá que FastAPI modifique directamente datos de SQL Server salvo que exista una fase excepcional aprobada explícitamente.

La regla base será:

```text
FastAPI lee/importa desde SQL Server mediante contratos.
FastAPI escribe en PostgreSQL.
VB sigue operando sobre SQL Server hasta que el dominio sea absorbido.
```

---

## 2.4. Reportes

Crystal Reports no será parte de la arquitectura final.

SYSTUTOR OSS debe reemplazar reportes legacy mediante:

- reportes HTML imprimibles;
- generación PDF server-side;
- exportación Excel;
- dashboards React;
- jobs de reporte en segundo plano;
- plantillas versionadas.

Los reportes deben ser auditables y reproducibles.

---

## 2.5. Programación agéntica y Spec-Driven Development

SYSTUTOR OSS se desarrollará con una metodología de **programación agéntica guiada por especificaciones**.

Esto significa que ninguna característica importante debe agregarse solo escribiendo código directamente.

Primero se define la especificación. Luego se implementa.

El flujo base será:

```text
Idea
  ↓
Spec
  ↓
Diseño técnico
  ↓
Contrato de datos/API
  ↓
Implementación
  ↓
Pruebas
  ↓
Revisión
  ↓
Merge
```

Los agentes de IA podrán ayudar a:

- analizar código legacy;
- generar propuestas;
- escribir tests;
- documentar módulos;
- revisar consistencia;
- crear migradores;
- detectar riesgos;
- generar scaffolding.

Pero el contrato final de cada característica debe estar escrito y versionado.

---

## 2.6. Cómo se agregará cada característica en trabajo grupal

Cada nueva característica debe entrar mediante un proceso controlado.

### Paso 1: Feature Proposal

Cada característica inicia como una propuesta en Markdown.

Debe incluir:

- nombre de la característica;
- problema que resuelve;
- módulo afectado;
- usuarios afectados;
- datos involucrados;
- permisos necesarios;
- eventos emitidos;
- pantallas necesarias;
- riesgos;
- criterios de aceptación.

Ejemplo:

```text
docs/specs/logistics/crear-ruta-entrega.md
```

---

### Paso 2: Diseño técnico

Antes de programar, se define:

- entidades;
- servicios;
- endpoints;
- eventos;
- migraciones;
- validaciones;
- pruebas requeridas;
- impacto en otros módulos.

---

### Paso 3: Contratos de API y datos

Cada endpoint importante debe tener contrato claro.

Ejemplo:

```text
POST /api/logistics/routes
GET /api/logistics/routes/{id}
```

Cada evento también debe tener contrato.

Ejemplo:

```json
{
  "event": "logistics.route.created",
  "payload": {
    "route_id": "uuid",
    "created_by": "uuid",
    "created_at": "datetime"
  }
}
```

---

### Paso 4: Implementación aislada

Cada programador trabajará en ramas separadas.

No se permitirá mezclar cambios grandes sin revisión.

Toda característica debe tener:

- backend;
- frontend si aplica;
- migración si aplica;
- tests;
- documentación mínima;
- registro de eventos si aplica.

---

### Paso 5: Pull Request obligatorio

Todo cambio debe pasar por PR.

El PR debe responder:

- qué cambia;
- por qué cambia;
- cómo se prueba;
- qué riesgos tiene;
- qué módulos toca;
- qué migraciones agrega;
- qué eventos nuevos emite.

---

### Paso 6: Revisión técnica y funcional

Cada PR debe revisarse bajo dos perspectivas:

1. Técnica:
   - arquitectura;
   - seguridad;
   - tests;
   - performance;
   - mantenibilidad.

2. Funcional:
   - si realmente resuelve el flujo de negocio;
   - si respeta el dominio;
   - si no rompe procesos legacy o migración.

---

### Paso 7: Merge y registro

Cada feature aceptada debe quedar registrada en:

```text
CHANGELOG.md
```

y si implica una decisión arquitectónica, también en:

```text
docs/adr/
```

ADR significa Architecture Decision Record.

---

# 3. Migración de datos

## 3.1. Contexto real del legacy

SYSTUTOR Legacy contiene:

- VB.NET;
- SQL Server;
- Crystal Reports;
- Stored Procedures;
- Triggers;
- Views;
- lógica en formularios;
- lógica distribuida entre UI, SQL y reportes;
- poca o nula documentación formal.

Por esta razón, una sincronización directa entre SQL Server y PostgreSQL sería peligrosa.

No se debe asumir que las tablas legacy representan claramente el dominio.

---

## 3.2. Decisión principal

La migración inicial no se hará mediante sync DB-to-DB automático.

La estrategia oficial será:

> Migración mediante contratos explícitos de dominio basados en archivos exportados, validados y auditables.

El formato inicial recomendado será:

```text
CSV + manifest.json
```

---

## 3.3. Por qué no sync directo

No se usará sync directo como primera estrategia porque existen riesgos altos:

- triggers con efectos secundarios desconocidos;
- SP que escriben en varias tablas;
- views que ocultan lógica;
- datos duplicados o inconsistentes;
- lógica en UI que no está en la base de datos;
- falta de documentación;
- riesgo de race conditions;
- posibilidad de romper producción.

---

## 3.4. Protocolo de intercambio

Cada exportación desde legacy debe producir un paquete controlado.

Ejemplo:

```text
export_2026_06_18_190000/
    manifest.json
    customers.csv
    credits.csv
    logistics_orders.csv
```

El archivo `manifest.json` debe contener:

```json
{
  "domain": "customers",
  "schema_version": "1.0.0",
  "source": "systutor_legacy",
  "generated_at": "2026-06-18T19:00:00Z",
  "row_count": 1000,
  "checksum": "sha256"
}
```

Cada CSV debe tener columnas explícitas, nombres estables y documentación asociada.

---

## 3.5. Migrator Engine

Se creará un componente separado llamado inicialmente:

```text
systutor-migrator
```

Este componente no debe estar mezclado directamente con el backend principal.

Responsabilidades:

- leer paquetes de exportación;
- validar manifest;
- cargar CSV;
- validar estructura;
- detectar duplicados;
- normalizar datos;
- transformar legacy data hacia modelos OSS;
- registrar errores;
- insertar o actualizar PostgreSQL;
- generar reportes de migración.

---

## 3.6. Uso de pandas

`pandas` será usado como herramienta ETL para:

- leer CSV;
- limpiar datos;
- validar columnas;
- detectar duplicados;
- comparar datasets;
- transformar columnas;
- generar reportes intermedios.

Pandas no debe contener reglas profundas de negocio.

La regla será:

```text
CSV → pandas ETL → validación → mapeo de dominio → persistencia PostgreSQL
```

---

## 3.7. Uso de openpyxl

`openpyxl` podrá usarse para generar reportes Excel de auditoría y errores.

Ejemplos:

```text
migration_errors.xlsx
migration_summary.xlsx
```

Estos reportes podrán contener:

- filas rechazadas;
- errores por columna;
- duplicados;
- inconsistencias;
- advertencias;
- resumen de importación.

`openpyxl` no será el motor principal de migración. Será una herramienta de inspección y reporting.

---

## 3.8. Auditoría de importaciones

Cada importación debe registrarse.

Se creará una tabla o módulo de auditoría de migración con datos como:

- job_id;
- dominio;
- archivo fuente;
- hash del archivo;
- fecha;
- usuario o proceso;
- filas leídas;
- filas insertadas;
- filas actualizadas;
- filas rechazadas;
- errores;
- duración;
- estado final.

Nada debe importarse silenciosamente.

---

## 3.9. Single Writer por dominio

Durante la convivencia entre legacy y OSS se aplicará la regla:

> Solo un sistema puede escribir un dominio a la vez.

Ejemplo inicial:

| Dominio | Writer inicial | Lector secundario |
|---|---|---|
| Clientes | Legacy | OSS |
| Créditos | Legacy | OSS |
| Facturación | Legacy | OSS |
| Logística migrada | OSS | Legacy |
| Auth nuevo | OSS | Legacy no aplica |
| Auditoría OSS | OSS | Legacy no aplica |

Esto evita dual-write y reduce race conditions.

---

## 3.10. Migración por dominios, no por tablas

No se migrarán tablas 1:1 como objetivo final.

Se migrarán dominios.

Ejemplo:

Incorrecto:

```text
Movimiento → movimiento
DetalleMovimiento → detalle_movimiento
```

Correcto:

```text
Movimiento + DetalleMovimiento + reglas relacionadas
    ↓
Dominio de logística OSS
```

El nuevo modelo debe representar el dominio limpio, no repetir la deuda técnica del legacy.

---

# 4. Etapas de programación

## 4.1. Etapa 0: Preparación del repositorio

Objetivo:

Crear la base inicial del proyecto.

Entregables:

- repositorio Git;
- estructura backend;
- estructura frontend;
- `contrato.md`;
- `README.md` inicial;
- reglas de contribución;
- entorno Docker local;
- configuración base de PostgreSQL;
- configuración base de FastAPI;
- configuración base de React + Vite.

---

## 4.2. Etapa 1: Kernel mínimo

Objetivo:

Construir el núcleo mínimo de SYSTUTOR OSS.

Incluye:

- configuración central;
- conexión PostgreSQL;
- sistema de migraciones Alembic;
- autenticación básica;
- usuarios;
- roles;
- permisos;
- tenants si aplica desde el inicio;
- auditoría base;
- health checks;
- estructura de módulos;
- logging inicial.

---

## 4.3. Etapa 2: Shell frontend

Objetivo:

Crear la primera interfaz usable.

Incluye:

- login;
- layout principal;
- sidebar;
- navegación;
- sistema de rutas;
- TanStack Query configurado;
- Zustand configurado;
- pantalla de dashboard inicial;
- manejo de sesión;
- manejo de permisos visuales.

---

## 4.4. Etapa 3: Runtime de módulos/plugins

Objetivo:

Permitir que SYSTUTOR OSS crezca por módulos.

Incluye:

- registro de módulos backend;
- registro de rutas;
- registro de permisos;
- registro de eventos;
- registro de menús frontend;
- estructura estándar para plugins;
- lifecycle básico:

```text
on_install
on_enable
on_disable
on_uninstall
```

---

## 4.5. Etapa 4: Event Bus y auditoría fuerte

Objetivo:

Crear una base observable.

Incluye:

- emisión de eventos;
- listeners;
- auditoría de acciones;
- historial por entidad;
- logs estructurados;
- tabla de eventos;
- integración futura con WebSockets.

---

## 4.6. Etapa 5: Migrator Engine

Objetivo:

Crear la herramienta oficial para absorber datos desde SYSTUTOR Legacy.

Incluye:

- lectura de manifest;
- lectura de CSV;
- validaciones;
- mappers;
- reportes de error;
- auditoría de importación;
- importación inicial de clientes o catálogo simple;
- generación de reportes Excel con openpyxl.

---

## 4.7. Etapa 6: Módulo inicial de logística

Objetivo:

Empezar la absorción real del legacy por un dominio controlado.

Incluye:

- análisis del flujo logístico legacy;
- definición del modelo limpio;
- endpoints FastAPI;
- pantallas React;
- eventos logísticos;
- permisos;
- auditoría;
- importación desde CSV legacy;
- operación piloto.

La migración logística debe ser progresiva y validada con usuarios reales.

---

## 4.8. Etapa 7: Coexistencia controlada

Objetivo:

Permitir que SYSTUTOR Legacy y SYSTUTOR OSS convivan sin romper producción.

Incluye:

- exportaciones programadas desde legacy;
- importaciones controladas a OSS;
- reportes de diferencias;
- reglas de ownership por dominio;
- revisión humana de conflictos;
- pruebas por sucursal, cliente o grupo operativo.

---

## 4.9. Etapa 8: Absorción progresiva

Objetivo:

Reducir dependencia del legacy por dominios.

Orden recomendado:

1. catálogos simples;
2. clientes en modo lectura;
3. créditos en modo lectura;
4. logística piloto;
5. logística completa;
6. inventario relacionado;
7. reportes nuevos;
8. facturación cuando LibreFact/OpenFact esté suficientemente maduro.

---

## 4.10. Etapa 9: Retiro parcial del legacy

Objetivo:

Cuando un dominio esté completamente absorbido, SYSTUTOR Legacy debe dejar de ser writer para ese dominio.

El retiro debe ser por partes, no global.

Cada dominio retirado debe tener:

- validación funcional;
- validación de datos;
- auditoría;
- rollback plan;
- capacitación;
- aprobación de operación.

---

# 5. Conclusiones

SYSTUTOR OSS será la evolución natural de SYSTUTOR Legacy, no una reescritura impulsiva.

El proyecto debe avanzar con una estrategia conservadora en datos, pero ambiciosa en arquitectura.

Las decisiones principales son:

1. El legacy se absorbe, no se destruye de golpe.
2. El Kernel debe ser pequeño y modular.
3. La lógica de negocio debe moverse progresivamente a Python.
4. PostgreSQL será la base principal del nuevo sistema.
5. SQL Server será fuente legacy durante la transición.
6. No se hará sincronización directa DB-to-DB como primera estrategia.
7. La migración inicial se hará mediante contratos explícitos de dominio con CSV + manifest.
8. pandas será el motor ETL inicial.
9. openpyxl será usado para reportes de auditoría y errores.
10. Cada dominio tendrá un solo writer.
11. La programación será spec-driven y apoyada por agentes de IA.
12. Cada característica debe entrar con especificación, contrato, pruebas y revisión.
13. SYSTUTOR OSS debe ser global, modular y preparado para comunidad.
14. LibreFact/OpenFact debe evolucionar como infraestructura fiscal independiente.
15. El objetivo final no es crear otro ERP, sino una plataforma empresarial abierta, observable y extensible.

La prioridad inicial será construir una base sólida antes de migrar funcionalidades críticas.

SYSTUTOR OSS debe avanzar lentamente, pero con dirección clara.

La meta no es solo modernizar tecnología.

La meta es construir la próxima generación de infraestructura empresarial abierta bajo la futura visión de Censoria.
