---
id: "0026"
title: "Cotización vía Consola DSL — Draft-First"
domain: ventas
module: cotizacion
status: propuesta
requires:
  - docs/adr/0022-adopcion-monaco-editor-consola-operativa.md
  - docs/adr/0012-crm-plugin-clientes.md
  - docs/adr/0015-productos-plugin.md
  - docs/adr/0010-logistics-como-plugin-piloto.md
---

# SPEC 0026 — Cotización vía Consola DSL, Draft-First

## Estado

Propuesta

## Frase guía

**No estás creando cotizaciones. Estás creando la forma más rápida de crearlas.**

## Contexto

El sistema tiene los módulos base necesarios para operar: clientes (CRM), productos (catálogo), vehículos y almacenes (logistics), y planificación de capacidad. Lo que no existe es una forma rápida de registrar una **intención de venta** mientras el operador está en una llamada, leyendo un correo o atendiendo a un cliente en planta.

El ADR 0022 definió Monaco Editor como consola operativa del sistema. Esta spec define el primer módulo que la consume: **Cotización**.

A diferencia del legacy (formularios multi-paso, modales, búsquedas separadas), este módulo usa un DSL en español con autocompletado que convierte entrada textual en datos estructurados y persiste el resultado como borrador.

### Relación con otras specs

- `0023S` (Gestión Comercial) menciona "presupuesto/cotización" como dominio futuro de `ventas`/`comercial`, explícitamente fuera de su alcance.
- `0023XA` (Condiciones Comerciales) referencia cotización como feeding de `facturacion` futura.
- `0017` (SearchDialog genérico) no aplica aquí — la consola reemplaza el search dialog para este flujo.

## Objetivo

Crear el módulo `ventas` con el sub-módulo `cotizacion` que permita:

1. Escribir una intención de venta en lenguaje natural estructurado (DSL español).
2. Obtener autocompletado contextual sobre clientes, productos y vehículos.
3. Parsear la entrada a un `QuoteDraft` estructurado.
4. Persistir el borrador.
5. Mostrar una confirmación visual inmediata.

## No objetivos (ETAPA 1)

- ❌ Sin PDF de cotización
- ❌ Sin pricing complejo (precio se posterga a ETAPA 2)
- ❌ Sin workflow de aprobación
- ❌ Sin conversión automática a pedido
- ❌ Sin condiciones comerciales (descuentos, impuestos, crédito)
- ❌ Sin Ruta, Carta Porte ni conceptos de logistics operativa
- ❌ Sin multi-tenant avanzado (el tenant_id se hereda del contexto de sesión)
- ❌ Sin formulario visual alternativo ("disguised form")

## Principios obligatorios

1. **Draft-first**: toda cotización nace como borrador.
2. **DSL nativo**: la consola es el único mecanismo de entrada; no se crea un formulario paralelo.
3. **Core-first**: `ConsoleEditor` ya existe en `shared/ui`; la lógica de dominio vive en el plugin `ventas`.
4. **Velocidad > features**: el operador debe poder crear un borrador en menos de 10 segundos desde que empieza a escribir.
5. **Autocompletado contextual**: cliente desde CRM, producto desde catálogo, vehículo desde logistics.
6. **Validación temprana**: el parser rechaza entradas no interpretables; el command handler valida existencia de entidades referenciadas.
7. **Separación de concerns**: `ventas` = intención; `logistics` = ejecución. No se mezclan.
8. **Comando mínimo válido**: una cotización válida debe contener cliente resuelto, al menos 1 item válido, y fecha válida. Sin estos 3 elementos, el parser rechaza la ejecución.
9. **Determinismo**: si una entidad (cliente, producto) resuelve a más de un match, el sistema NO ejecuta — retorna la lista de matches para que el usuario precise. Nunca adivina.

> **Nota de vigencia**: las referencias a futuros sub-módulos `pricing/` y `pedidos/` en esta spec están **superadas**. El flujo real es `QuoteDraft → CONFIRMED → PlanningEntry → VehicleSession`. No existe entidad "pedido" separada. Ver spec 0027, `plugin.json` y `README.md` actuales de `plugins/ventas/`.

## Reglas de negocio

### Comando mínimo válido

Toda cotización requiere 3 elementos presentes y resueltos:

| Elemento | Requerido | Validación |
|---|---|---|
| Cliente | Sí | Debe resolver a exactamente 1 cliente en CRM |
| Al menos 1 item | Sí | Producto resuelto + cantidad > 0 |
| Fecha de entrega | Sí | Fecha válida (hoy o futura, no pasada) |

Si falta cualquiera de estos 3, el sistema rechaza la ejecución con un mensaje descriptivo indicando qué falta.

### Ambigüedad múltiple — cero tolerancia

Si una entidad tiene múltiples matches, el sistema **no ejecuta** y retorna las opciones:

```
> cotizar cliente Juan 400 cilindros mañana 14h

✗ cliente "Juan" tiene múltiples matches:
  1. Juan Pérez — RUC 20100000001
  2. Juan García — RUC 20100000002
  3. Juan Martínez — DNI 12345678
> _
```

El usuario debe reescribir con suficiente precisión para resolver a un match único. Ejemplo: `cotizar cliente "Juan Pérez" 400 ...`

### Modo preview (sin persistir)

El comando `preview` parsea, resuelve entidades y muestra el resultado **sin guardar**:

```
> preview cotizar cliente Juan 400 cilindros mañana 14h

✓ Cliente     Juan Pérez
✓ Producto    Cilindro 10kg
✓ Cantidad    400
✓ Entrega     2026-07-25  14:00

→ preview — no guardado
> _
```

Útil para verificar resolución de entidades y fechas antes de confirmar.

### Control de duplicados

Se implementa idempotencia por hash del comando normalizado + ventana de tiempo:

- Hash = sha256(`tenant_id|cliente_id|items|fecha|hora|vehiculo_id|condiciones`)
- Ventana = 60 segundos desde el último comando idéntico
- Si se detecta duplicado dentro de la ventana, el sistema advierte: `→ comando duplicado (ejecutado hace 23s). Usá 'confirmar' para forzar.`

Esto previene doble ejecución accidental (doble Ctrl+Enter, delay de red, etc.).

### Timezone

Toda resolución de fechas y horas usa el timezone del tenant. Si el tenant no tiene timezone configurado, se usa `America/Lima` por defecto.

Edge case: `mañana 14h` ejecutado a las 15:00 — "mañana" sigue siendo mañana (fecha + 1), la hora es 14:00 de mañana. Si la hora ya pasó hoy, no afecta la resolución de "mañana".

### Feedback incremental

Mientras el usuario escribe, el parser emite resolución parcial. La UI muestra debajo del prompt, en tiempo real:

```
> cotizar cliente Juan 400 cilindros mañana 14h

  ✓ cliente    Juan Pérez
  ⬡ producto   Cilindro 10kg
  ⬡ fecha      mañana → 2026-07-25
  ○ hora       14:00
```

Estados visuales:
- `✓` resuelto (match único)
- `⬡` detectado pero pendiente de resolución final (el parser lo reconoce pero aún no confirma contra backend)
- `○` detectado, sin ambigüedad
- `✗` error o múltiples matches

Este feedback es solo visual, no bloquea la escritura. Solo en el momento de ejecutar (Ctrl+Enter) se validan todas las resoluciones.

## Arquitectura del módulo

### Core (apps/web/src/shared/ui/)

```
apps/web/src/shared/ui/
├── console-editor/                     # ADR 0022 — Monaco wrapper
│   ├── ConsoleEditor.tsx
│   ├── ConsoleEditor.types.ts
│   ├── ConsoleEditor.theme.ts
│   ├── ConsoleEditor.completion.ts
│   ├── ConsoleEditor.tokens.ts
│   ├── ConsoleEditor.validation.ts
│   └── index.ts
└── console-shell/                      # Layout reutilizable: consola + resultado + historial
    ├── ConsoleShell.tsx                # Shell genérico, recibe providers + renderers como props
    ├── ConsoleShell.types.ts           # Props: resultRenderer, historyRenderer, placeholder, etc.
    └── index.ts
```

`ConsoleShell` es el layout estándar para cualquier plugin que use `ConsoleEditor`. Encapsula:

- Área de consola (Monaco)
- Área de resultado/preview (debajo de la consola)
- Historial de comandos (opcional, debajo del resultado)
- Estado de ejecución (idle, parsing, success, error)

No contiene lógica de dominio. Los plugins y sub-módulos la configuran mediante props:

```ts
<ConsoleShell
  language="cotizacion"
  completionProvider={cotizacionCompletion}
  tokenProvider={cotizacionTokens}
  validationProvider={cotizacionValidation}
  onExecute={handleCotizar}
  renderResult={(data) => <CotizacionResult draft={data} />}
  renderHistory={(items) => <CotizacionHistory items={items} />}
  placeholder="cotizar cliente ..."
/>
```

### Plugin (plugins/ventas/)

### Plugin (plugins/ventas/)

```
plugins/ventas/
├── plugin.json                        # Identidad global, permisos, entrypoints de sub-módulos
├── README.md
│
├── _shared/                           # Componentes y utilidades internos del módulo ventas
│   ├── backend/
│   │   └── base.py                    # Modelo base, helpers de validación cross-sub-módulo
│   └── frontend/
│       ├── components/
│       │   ├── QuoteStatusBadge.tsx   # Badge de estado reutilizado por cotización, pedidos, etc.
│       │   └── QuoteItemList.tsx      # Lista de items reutilizada en preview y detalle
│       ├── hooks/
│       │   └── useResolveEntity.ts    # Hook genérico de resolución cliente/producto/vehículo
│       └── utils/
│           └── date-resolver.ts       # Resolución de fechas relativas (hoy, mañana, lunes, etc.)
│
├── cotizacion/                        # Sub-módulo ETAPA 1
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── router.py                  # FastAPI router: POST /cotizaciones, GET /cotizaciones/{id}
│   │   ├── schemas.py                 # Pydantic: QuoteDraftCreate, QuoteDraftResponse, QuoteItem
│   │   ├── models.py                  # SQLAlchemy: QuoteDraft, QuoteItem
│   │   └── services/
│   │       ├── __init__.py
│   │       └── cotizacion.py          # handle_cotizar(command) → QuoteDraft
│   ├── frontend/
│   │   ├── api.ts                     # API client + query keys + tipos TS
│   │   ├── types.ts                   # Tipos locales: ParsedCommand, QuoteDraftDTO
│   │   ├── pages/
│   │   │   └── CotizacionPage.tsx     # Página thin: solo configura ConsoleShell con providers del dominio
│   │   ├── dsl/
│   │   │   ├── parser.ts              # Tokenizador y parser del DSL español
│   │   │   ├── tokens.ts              # Definición de keywords y patrones
│   │   │   └── autocomplete.ts        # CompletionProvider + resolución de entidades
│   │   └── components/
│   │       ├── CotizacionResult.tsx   # Render de preview del QuoteDraft creado
│   │       └── CotizacionHistory.tsx  # Render de historial de comandos
│   └── migrations/
│       └── 001_initial_cotizacion.py  # Tablas: ventas_quote_drafts, ventas_quote_items
│
└── (nota: los sub-módulos pricing/pedidos/condiciones planeados originalmente no existen — superados por el flujo QuoteDraft → CONFIRMED → PlanningEntry → VehicleSession, ver spec 0027)
```

### Flujo de datos

```
Usuario escribe en Monaco
  → Autocomplete Engine sugiere (cliente, producto, vehículo)
  → Usuario completa comando (Ctrl+Enter)
  → Parser DSL tokeniza e interpreta
  → Command Handler valida entidades contra APIs (CRM, productos, logistics)
  → Se crea QuoteDraft (status=DRAFT)
  → Se persiste en PostgreSQL
  → UI muestra resultado estructurado
```

### Separación de capas

#### Capa Core — Editor (ya existe)

```
apps/web/src/shared/ui/console-editor/
```

- Entrada de texto, autocompletado, tokens, validación visual.
- No contiene lógica de dominio.
- Reutilizado tal cual por cualquier plugin que requiera consola.

#### Capa Core — Shell (nueva)

```
apps/web/src/shared/ui/console-shell/
```

- Layout estándar: consola + resultado + historial.
- `ConsoleShell` recibe providers (completion, tokens, validation) y renderers (result, history) como props.
- El sub-módulo solo configura, no construye layout desde cero.
- Ejemplo de uso: `CotizacionPage` es ~15 líneas: importa `ConsoleShell`, le pasa providers del dominio y renderers específicos.

#### Capa Interna del Módulo (nueva — `ventas/_shared/`)

```
plugins/ventas/_shared/
```

- Componentes, hooks y utilidades compartidos **entre sub-módulos de ventas**.
- No son genéricos del core — contienen conceptos del dominio `ventas` (cotizaciones, pedidos, items, estados).
- Ejemplos:
  - `QuoteStatusBadge` — badge de estado (`DRAFT`, futuro `APPROVED`, `CONVERTED`, etc.)
  - `QuoteItemList` — lista de items con producto, cantidad, peso
  - `useResolveEntity` — hook genérico de resolución cliente/producto/vehículo contra APIs externas
  - `date-resolver` — resolución de fechas relativas (`hoy`, `mañana`, `lunes`, etc.)
- **Regla**: lo que es genérico del dominio ventas va en `_shared/`; lo que es específico de un sub-módulo va en el sub-módulo.

#### Capa DSL (nueva, en el sub-módulo)

```
plugins/ventas/cotizacion/frontend/dsl/
```

- Tokenizador y parser del lenguaje español.
- Keywords: `cotizar`, `cliente`, `producto`, `vehículo`, `mañana`, `cancelar`, `condición`, `entonces`.
- Convierte texto → `ParsedCommand`.

#### Capa Backend (nueva, en el sub-módulo)

```
plugins/ventas/cotizacion/backend/
```

- Servicio `handle_cotizar(command)`.
- Valida existencia de cliente, producto y vehículo.
- Crea `QuoteDraft` + `QuoteItem`.
- Emite evento `ventas.cotizacion.created`.

## Modelo de dominio (mínimo ETAPA 1)

### QuoteDraft

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | UUID | sí | PK |
| `tenant_id` | UUID | sí | Heredado del contexto |
| `customer_id` | UUID | sí | FK a `crm.customers` |
| `customer_name` | string | no | Snapshot del nombre al momento de crear |
| `status` | enum | sí | `DRAFT` (único valor en ETAPA 1) |
| `delivery_date` | date | sí | Fecha de entrega solicitada |
| `delivery_time` | time | no | Hora de entrega solicitada |
| `vehicle_id` | UUID | no | FK a `logistics.vehicles` (opcional) |
| `vehicle_plate` | string | no | Snapshot de la placa |
| `conditions` | text | no | Condiciones en texto libre |
| `notes` | text | no | Notas internas |
| `created_by` | UUID | sí | Usuario que creó la cotización |
| `created_at` | timestamp | sí | Fecha de creación |
| `updated_at` | timestamp | sí | Fecha de última modificación |

### QuoteItem

| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| `id` | UUID | sí | PK |
| `quote_draft_id` | UUID | sí | FK a `ventas_quote_drafts` |
| `product_id` | UUID | sí | FK a `productos.products` |
| `product_name` | string | no | Snapshot del nombre |
| `quantity` | integer | sí | Cantidad solicitada |
| `unit_weight_kg` | decimal | no | Peso unitario (snapshot) |
| `created_at` | timestamp | sí | Fecha de creación |

### Enums

```python
class QuoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    # Futuros: PENDING_REVIEW, APPROVED, REJECTED, CONVERTED_TO_ORDER, CANCELLED
```

## DSL — Lenguaje de dominio

### Formato general

```
<accion> cliente <nombre|referencia> <items> [fecha] [hora] [vehiculo <placa>] [condicion <texto>]
```

### Acciones soportadas (ETAPA 1)

| Acción | Descripción |
|---|---|
| `cotizar` | Crear un nuevo QuoteDraft |

Futuras: `cancelar <id>`, `editar <id>`, `convertir <id>`.

### Items

```
<cantidad> <producto> [, <cantidad> <producto> ...]
```

Ejemplos:
- `400 "cilindros"`
- `200 "cilindros", 50 "balones"`
- `400 "cilindros 10kg"`

Los nombres de cliente y producto que contengan espacios o coincidan con keywords del DSL deben ir entre comillas dobles para evitar ambigüedades.

### Fechas

| Token | Resolución |
|---|---|
| `hoy` | Fecha actual |
| `mañana` | Fecha actual + 1 día |
| `pasado mañana` | Fecha actual + 2 días |
| `lunes` .. `domingo` | Próximo día de la semana |
| `YYYY-MM-DD` | Fecha explícita |

### Horas

| Token | Resolución |
|---|---|
| `14h` `14:00` `14 hrs` | Hora explícita |
| `mañana` | 06:00 |
| `tarde` | 14:00 |
| `noche` | 20:00 |

### Vehículo

```
vehiculo "<placa>"
```

Referencia opcional. Si se omite, el QuoteDraft queda sin vehículo asignado. Las patentes entre comillas evitan que caracteres especiales sean interpretados como tokens.

### Ayuda

```
cotizar --help
```

Muestra en la terminal la documentación completa del DSL: sintaxis, campos obligatorios/opcionales, ejemplos, comandos especiales y reglas de autocompletado.

### Condiciones

```
condicion <texto libre>
```

Ejemplo: `condicion si no llega a las 14h cancelar`

### Ejemplos completos

```
> cotizar cliente "Juan" 400 "cilindros" mañana 14h
> cotizar cliente "Distribuidora XYZ" 200 "cilindros 10kg", 50 "balones" hoy tarde vehiculo "H4U4-3RF78U" condicion pago contra entrega
> cotizar cliente "Maria" 400 "cilindros" mañana 14h condicion si cliente no llega 14 hrs entonces cancelar
```

## Parser DSL

### Etapas de parsing

1. **Tokenización**: separar keywords, entidades, valores, strings entrecomillados.
2. **Identificación de acción**: primera keyword (`cotizar`).
3. **Extracción de entidades**:
   - `cliente <valor>` → buscar en CRM por nombre o ID
   - `<cantidad> <producto>` → buscar en catálogo por nombre o SKU
   - `vehiculo <placa>` → buscar en logistics
4. **Resolución de fecha/hora**: tokens de tiempo relativos o absolutos.
5. **Condiciones**: texto libre después de `condicion`.

### Output del parser

```typescript
interface ParsedCommand {
  action: "cotizar";
  cliente: {
    raw: string;          // texto tal cual se escribió
    resolvedId?: string;  // UUID si se encontró en CRM
  };
  items: Array<{
    raw: string;
    cantidad: number;
    producto: string;      // nombre o keyword del producto
    resolvedId?: string;
  }>;
  fecha: {
    raw: string;
    iso?: string;          // YYYY-MM-DD
  };
  hora?: {
    raw: string;
    iso?: string;          // HH:MM
  };
  vehiculo?: {
    raw: string;           // placa
    resolvedId?: string;
  };
  condiciones?: string;
}
```

### Pipeline de validación (backend)

1. `resolveCustomer(raw)` → busca en CRM por nombre/apellido/razón_social (ILIKE). Si no encuentra, retorna error con sugerencias.
2. `resolveProduct(raw)` → busca en catálogo por nombre/SKU (ILIKE). Si no encuentra, retorna error con sugerencias.
3. `resolveVehicle(plate)` → busca en logistics por placa exacta.
4. Si todas las entidades resuelven, crea `QuoteDraft`.

## API

### Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/plugins/ventas/cotizaciones` | Ejecutar comando DSL → crear QuoteDraft |
| `GET` | `/api/v1/plugins/ventas/cotizaciones/{id}` | Obtener QuoteDraft por ID |
| `GET` | `/api/v1/plugins/ventas/cotizaciones` | Listar QuoteDrafts (paginado, filtrable) |

### Request (POST)

```json
{
  "command": "cotizar cliente \"Juan\" 400 \"cilindros\" mañana 14h"
}
```

### Response (POST)

```json
{
  "id": "uuid",
  "status": "DRAFT",
  "customer": {
    "id": "uuid",
    "name": "Juan Pérez"
  },
  "items": [
    {
      "id": "uuid",
      "product": {
        "id": "uuid",
        "name": "Cilindro 10kg",
        "sku": "CIL-10KG"
      },
      "quantity": 400,
      "unit_weight_kg": 10.0
    }
  ],
  "delivery_date": "2026-07-25",
  "delivery_time": "14:00",
  "vehicle": null,
  "conditions": null,
  "created_at": "2026-07-24T15:30:00Z"
}
```

### Errores

```json
{
  "error": "validation_error",
  "message": "No se encontró el cliente 'Juan'. Sugerencias: Juan Pérez, Juan García, Juan Martínez",
  "details": {
    "field": "cliente",
    "raw": "Juan",
    "suggestions": ["uuid-1|Juan Pérez", "uuid-2|Juan García"]
  }
}
```

## Autocomplete Engine

### Providers registrados

| Provider | Fuente | Trigger |
|---|---|---|
| `customer` | `GET /api/v1/plugins/crm/customers?search=` | después de keyword `cliente` |
| `product` | `GET /api/v1/plugins/productos/products?search=` | después de cantidad numérica |
| `vehicle` | `GET /api/v1/plugins/logistics/vehicles?search=` | después de keyword `vehiculo` |
| `date` | tokens fijos | después de items |
| `condition` | tokens fijos | después de `condicion` |

### Keywords para tokenización

```
cotizar, cliente, vehiculo, condicion, cancelar,
hoy, mañana, tarde, noche, hrs, h,
lunes, martes, miercoles, jueves, viernes, sabado, domingo
```

## UI

### Shell en Core (`ConsoleShell`)

El layout es **terminal pura**, sin paneles ni zonas delimitadas. Vive en `apps/web/src/shared/ui/console-shell/`. La estética es monoespaciada, fondo oscuro, prompt (`>`) y output inline. No usa cards, tabs, sidebars ni layouts multi-zona.

Cualquier plugin o sub-módulo lo reutiliza pasando providers y renderers como props.

### Página thin: `CotizacionPage`

`CotizacionPage` no construye layout — solo configura `ConsoleShell` con los providers del dominio cotización:

```tsx
// plugins/ventas/cotizacion/frontend/pages/CotizacionPage.tsx
export function CotizacionPage() {
  return (
    <ConsoleShell
      language="cotizacion"
      completionProvider={cotizacionCompletion}
      tokenProvider={cotizacionTokens}
      validationProvider={cotizacionValidation}
      onExecute={handleCotizar}
      renderResult={(data) => <CotizacionResult draft={data} />}
      placeholder="cotizar cliente ..."
    />
  );
}
```

### Layout visual (terminal bash-like)

```
┌── Cotización ───────────────────────────────────────────────────┐
│                                                                 │
│  > cotizar cliente "Juan" 400 "cilindros" mañana 14h           │
│                                                                 │
│  ✓ Cliente     Juan Pérez                                      │
│  ✓ Producto    Cilindro 10kg                                   │
│  ✓ Cantidad    400                                             │
│  ✓ Entrega     2026-07-25  14:00                               │
│                                                                 │
│  → draft #CTZ-0042 creado                                      │
│                                                                 │
│  > █                                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

El historial no se muestra visualmente en un panel. Se accede con `↑`/`↓` como en bash, y `Ctrl+R` para búsqueda inversa. El comando `history` lista las entradas anteriores directamente en el output.

### Estados de la UI

- **Vacío**: prompt `> █` al inicio del terminal, sin output previo.
- **Escribiendo**: autocompletado activo sobre el prompt actual, sin submit todavía.
- **Parseando**: prompt se oscurece brevemente mientras se resuelve en backend.
- **Éxito**: output aparece arriba del nuevo prompt, con checkmarks (`✓`) y referencia del draft. Un nuevo `> █` espera abajo.
- **Error**: output en rojo con mensaje y sugerencias, nuevo `> █` listo para corregir.
- **Historial**: invisible por defecto. Se accede con `↑`/`↓` (bash-like) o `Ctrl+R` (reverse search). El comando `history` imprime la lista en el output.

## Permisos

| Permiso | Descripción |
|---|---|
| `ventas.cotizacion.create` | Crear cotizaciones vía consola |
| `ventas.cotizacion.read` | Ver cotizaciones propias |
| `ventas.cotizacion.read_all` | Ver todas las cotizaciones (supervisor) |

## Eventos

| Evento | Payload |
|---|---|
| `ventas.cotizacion.created` | `{ quote_id, customer_id, items_count, delivery_date, created_by }` |

## Migraciones

Nueva revisión Alembic en `apps/api/migrations/versions/`:

- `ventas_quote_drafts` — tabla principal de borradores
- `ventas_quote_items` — items de cada borrador
- Índices: `(tenant_id, status)`, `(customer_id)`, `(created_by)`, `(created_at DESC)`

## Pruebas requeridas

- **Unitarias (parser)**: tokenización de comandos válidos e inválidos, resolución de fechas relativas.
- **Unitarias (autocomplete)**: providers retornan sugerencias correctas según contexto.
- **Integración (API)**: POST con comando válido crea QuoteDraft + items + evento.
- **Integración (API)**: POST con cliente inexistente retorna error con sugerencias.
- **Integración (API)**: POST sin items retorna error de validación.
- **Frontend**: `ConsoleEditor` con autocomplete providers renderiza y sugiere correctamente.

## Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| DSL ambiguo con entidades de nombre similar | alto | Resolución exacta + sugerencias; el parser nunca adivina |
| Autocomplete lento si las APIs de CRM/productos son lentas | medio | Debounce (300ms) + caché local TanStack Query |
| Usuarios esperan "modo ChatGPT" (lenguaje libre) | medio | La consola deja claro que es un DSL, no chat; feedback visual inmediato ante entrada no interpretable |
| Scope creep hacia pricing/PDF en ETAPA 1 | alto | Esta spec define explícitamente los no-objetivos; cualquier adición requiere nueva spec |
| Múltiples `QuoteDraft` huérfanos sin conversión a pedido | bajo | Aceptable en ETAPA 1; se agrega limpieza/caducidad en spec futura |

## Criterios de aceptación

1. El operador puede escribir `cotizar cliente "X" N "producto" fecha hora` y obtener un `QuoteDraft` persistido.
2. El autocompletado sugiere clientes desde CRM mientras escribe después de `cliente`.
3. El autocompletado sugiere productos desde catálogo después de una cantidad.
4. Los nombres de cliente, producto y vehículo con espacios se insertan entre comillas dobles.
5. Si una entidad no se encuentra, el sistema retorna error con sugerencias (nunca crea un draft con referencias rotas).
6. Si una entidad resuelve a múltiples matches, el sistema NO ejecuta y retorna las opciones.
7. El comando `preview cotizar ...` parsea y muestra resultado sin persistir.
8. El comando `cotizar --help` muestra documentación completa del DSL sin crear borrador.
9. Se detecta duplicado de comando dentro de 60s y se advierte al usuario.
10. El `QuoteDraft` se crea con `status=DRAFT`.
11. Se emite evento `ventas.cotizacion.created`.
12. La UI muestra feedback incremental (✓/⬡/○) mientras el usuario escribe, sin bloquear la interacción.
13. La UI muestra el resultado estructurado inmediatamente después de ejecutar.
14. El flujo completo (escribir → ejecutar → ver resultado) toma menos de 10 segundos en condiciones normales.
15. No existe formulario alternativo para crear cotizaciones.
16. No se introducen conceptos de pricing, PDF, aprobación ni logistics operativa.
17. Las fechas se resuelven en el timezone del tenant.

