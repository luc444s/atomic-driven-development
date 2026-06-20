# ADR 0006 - Migración Legacy CSV Manifest

## Estado

Aceptado

## Contexto

SYSTUTOR Legacy contiene lógica repartida entre SQL Server, VB.NET, Crystal Reports, stored procedures, triggers, vistas y formularios.

No existe documentación completa del comportamiento real del legacy.

Una sincronización directa inicial entre la base legacy y la base OSS introduce riesgo alto de:

* efectos secundarios invisibles;
* dual-write;
* corrupción operativa;
* pérdida de trazabilidad;
* dependencia prematura de tablas legacy;
* interpretación incorrecta del dominio;
* propagación de errores históricos hacia OSS.

Por esta razón, la migración inicial no se realizará mediante sincronización directa entre bases de datos.

## Decisión

La migración inicial desde SYSTUTOR Legacy hacia SYSTUTOR OSS se realizará mediante un protocolo explícito de intercambio basado en:

* exportación controlada;
* archivos CSV explícitos;
* `manifest.json`;
* validación estructural;
* validación de dominio;
* transformación controlada;
* persistencia en PostgreSQL;
* auditoría de importación.

La migración será por dominio, no por tabla.

Ejemplos de dominios:

* clientes;
* créditos;
* logística;
* inventario;
* documentos;
* facturación;
* catálogos.

## Reglas obligatorias

* No habrá sync DB-to-DB inicial.
* No habrá dual-write.
* FastAPI no escribirá en SQL Server.
* SQL Server será tratado como sistema legacy de origen.
* PostgreSQL será el centro de datos de SYSTUTOR OSS.
* Cada dominio tendrá un solo writer a la vez.
* Toda importación deberá quedar auditada.
* Las migraciones serán por dominio, no por tabla.
* Ninguna importación debe sobrescribir datos silenciosamente.
* Toda transformación debe ser explícita y testeable.
* Todo archivo importado debe conservar trazabilidad.

## Flujo aprobado

```text
Legacy export
  -> CSV + manifest
  -> validación estructural
  -> validación de dominio
  -> transformación
  -> staging
  -> persistencia en PostgreSQL
  -> auditoría de importación
```

## Estructura de bundle

Cada exportación legacy deberá generar un bundle de importación.

Ejemplo:

```text
legacy_export_2026_06_20_153000/
├── manifest.json
├── customers.csv
├── credits.csv
├── logistics_orders.csv
└── README.txt
```

El bundle debe ser tratado como un artefacto auditable.

## Contrato mínimo de `manifest.json`

Cada bundle debe incluir un `manifest.json`.

Ejemplo:

```json
{
  "manifest_version": "1.0",
  "domain": "customers",
  "source_system": "systutor_legacy",
  "generated_at": "2026-06-20T15:30:00Z",
  "generated_by": "legacy_exporter",
  "schema_version": "1.0.0",
  "files": [
    {
      "name": "customers.csv",
      "rows": 1520,
      "checksum_sha256": "..."
    }
  ],
  "notes": "Exportación controlada desde legacy"
}
```

## Reglas para CSV

Los CSV deben ser explícitos.

Reglas:

* usar encabezados claros;
* no usar columnas anónimas;
* mantener encoding definido;
* mantener formato de fecha definido;
* conservar `legacy_id` cuando aplique;
* evitar campos ambiguos;
* no exportar columnas innecesarias;
* documentar significado de columnas cuando no sea evidente.

Ejemplo:

```csv
legacy_customer_id,document_type,document_number,name,phone,address,is_active,updated_at
1550,RUC,20123456789,Cliente Demo,999999999,Lima,true,2026-06-20T15:00:00Z
```

## Staging

El migrador no debe insertar directamente en tablas finales sin validación previa.

Flujo recomendado:

```text
CSV
-> parse
-> staging
-> validación
-> transformación
-> persistencia final
```

El staging puede ser físico o lógico, según la complejidad del dominio.

## Idempotencia

Las importaciones deben ser idempotentes cuando corresponda.

Esto significa que procesar el mismo bundle más de una vez no debe duplicar datos ni generar efectos incorrectos.

Para lograrlo se usará:

* `import_job_id`;
* checksum de archivo;
* `legacy_id`;
* claves naturales;
* control de imports ya procesados;
* reglas explícitas de insert/update/reject.

## Claves de trazabilidad

Cuando aplique, las entidades importadas deberán conservar relación con el sistema legacy.

Ejemplo:

```text
legacy_system = systutor_legacy
legacy_table = Persona_Nuevo
legacy_id = 1550
```

Esto permitirá:

* auditoría;
* soporte;
* comparación entre sistemas;
* resolución de conflictos;
* migraciones incrementales.

## Ownership por dominio

Cada dominio deberá tener un writer oficial.

Ejemplo inicial:

```text
Clientes      -> Legacy
Créditos      -> Legacy
Logística     -> OSS cuando se migre el módulo
Auth          -> OSS
Auditoría     -> OSS
Plugins       -> OSS
```

Mientras un dominio siga perteneciendo a Legacy, OSS solo deberá consumirlo mediante importación controlada.

Cuando un dominio pase a OSS, la escritura principal deberá ocurrir en PostgreSQL.

## Estados de importación

Cada importación deberá registrar estado.

Estados mínimos:

```text
pending
validating
validated
importing
completed
completed_with_warnings
failed
rejected
rolled_back
```

## Auditoría de importación

Toda importación debe registrar:

* `import_job_id`;
* dominio;
* archivo;
* checksum;
* fecha de inicio;
* fecha de fin;
* usuario o proceso que importó;
* cantidad de filas leídas;
* cantidad de filas insertadas;
* cantidad de filas actualizadas;
* cantidad de filas rechazadas;
* errores;
* warnings;
* resultado final.

## Rechazos y errores

Los registros inválidos no deben detener necesariamente toda la importación si el dominio permite importación parcial.

Debe existir salida de errores.

Ejemplo:

```text
import_results/
├── accepted.csv
├── rejected.csv
├── warnings.csv
└── report.json
```

Cada rechazo debe indicar:

* fila;
* columna;
* valor;
* motivo;
* severidad.

## Dry-run

El migrador debe soportar modo `dry-run`.

El modo `dry-run` debe:

* leer el bundle;
* validar estructura;
* validar dominio;
* calcular cambios esperados;
* generar reporte;
* no persistir en tablas finales.

Esto permite revisar una migración antes de ejecutarla realmente.

## Validaciones mínimas

El migrador debe validar:

* existencia de archivos declarados en manifest;
* checksum;
* columnas requeridas;
* tipos de datos;
* fechas;
* nulos;
* duplicados;
* referencias inexistentes;
* claves naturales;
* consistencia de tenant;
* consistencia de sucursal cuando aplique.

## Herramienta migrator

El proyecto requerirá una herramienta separada del backend principal:

```text
tools/migrator/
```

Responsabilidades:

* leer bundles legacy;
* validar manifest;
* cargar CSV;
* transformar datos;
* aplicar reglas de dominio;
* persistir en PostgreSQL;
* generar reportes;
* registrar auditoría.

El migrador no debe depender de la API web principal para ejecutar importaciones críticas.

## Uso de pandas y openpyxl

El migrador podrá usar pandas para:

* lectura de CSV;
* validación tabular;
* limpieza;
* joins;
* deduplicación;
* generación de reportes intermedios.

openpyxl podrá usarse para:

* reportes de errores en Excel;
* archivos revisables por usuarios;
* informes de migración;
* validación humana.

El formato oficial de intercambio seguirá siendo CSV + manifest.

## Eventos de migración

Las importaciones relevantes podrán generar eventos.

Ejemplos:

```text
legacy.customer.imported
legacy.customer.rejected
legacy.import.completed
legacy.import.failed
```

Estos eventos deben estar ligados al `import_job_id`.

## Seguridad

Los bundles de migración pueden contener información sensible.

Reglas:

* no subir bundles reales al repositorio;
* no exponer datos reales en pruebas;
* usar datos anonimizados para fixtures;
* controlar acceso a carpetas de importación;
* registrar quién ejecuta importaciones.

## Consecuencias

* El proyecto requerirá un `migrator` separado del backend principal.
* Los bundles de importación deberán tener esquema estable y versionado.
* Las importaciones deberán ser repetibles, trazables e idempotentes cuando corresponda.
* La convivencia Legacy/OSS se gestionará con ownership por dominio, no con escrituras simultáneas.
* La migración será más lenta que una sincronización directa, pero mucho más segura.
* El sistema podrá absorber el legacy gradualmente sin depender de entender toda la maraña de SP, triggers y formularios desde el día uno.
* Cualquier cambio mayor al protocolo CSV + manifest requerirá un nuevo ADR.


