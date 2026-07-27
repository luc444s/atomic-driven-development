---
id: "0027"
title: "Cotización — Consola y Formulario con visor de drafts"
domain: ventas
module: cotizacion
status: vigente
requires:
  - docs/adr/0022-adopcion-monaco-editor-consola-operativa.md
  - docs/adr/0023-dsl-comandos-consola-patrones-seguros.md
  - docs/adr/0028-single-use-case-multiples-adaptadores.md
  - docs/specs/core/0026-cotizacion-consola-dsl-draft-first.md
---

# SPEC 0027 — Cotización: Consola y Formulario

## Estado

Vigente — implementada en `plugins/ventas/cotizacion/frontend/ui/`

## Principio arquitectónico

La consola y el formulario son dos vistas distintas sobre el mismo caso de uso.
No deben existir diferencias funcionales entre ambas.
Toda validación, construcción del draft y ejecución ocurre en la capa de dominio compartido.

## Problema

La spec 0026 definió la consola DSL como único mecanismo de entrada. En la práctica hay dos perfiles:

- **Operador rápido**: escribe el comando en <10s, prefiere la consola.
- **Operador visual**: prefiere seleccionar cliente de una lista, ver calendario, usar comboboxes.
- Ambos necesitan ver las cotizaciones creadas sin salir de la pantalla.

## Propuesta

Una página con dos modos conmutables que comparten:

1. **Capa de dominio** (`shared/application/`) — el caso de uso, no habla directo a API.
2. **DraftExplorer** siempre visible debajo del editor activo.
3. **QuotePreview** para preview, draft, detalle, readonly e impresión.

## Layout general

```
┌────────────────────────────────────────────────────────────┐
│ Cotización                    [⌨ Consola] [📋 Formulario] │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─ Editor activo ───────────────────────────────────────┐ │
│  │  Consola o Formulario                                 │ │
│  │  → shared/application/prepareQuote()                  │ │
│  │  → confirm() → shared/application/createQuote()       │ │
│  │  → POST                                               │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌─ DraftExplorer ──────────────────────────────────────┐  │
│  │  #CTZ  Cliente    Items  Entrega     Estado          │  │
│  │  0042  Bohdan     —      mañana      DRAFT     ▼    │  │
│  │  0041  Gas Norte  —      hoy         DRAFT     ▼    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## Capa de dominio (`shared/`)

```
shared/
├── application/
│   ├── prepareQuote.ts    # Valida campos, construye QuoteDraft parcial
│   ├── confirmQuote.ts    # Marca como lista para enviar
│   └── createQuote.ts     # POST al backend, retorna QuoteDraft final
│
├── api/
│   └── index.ts           # Llamadas HTTP (solo usadas por application/)
│
├── types/
│   ├── index.ts           # QuoteDraft, QuoteItem, DraftStatus
│   └── commands.ts        # QuoteCommand (output del parser)
│
└── hooks/
    └── useDraftList.ts    # Lista + invalidate + refetchOnWindowFocus
```

La UI y la consola nunca llaman `apiRequest` directamente. Llaman `prepareQuote()` o `createQuote()`.

```
Consola              Formulario
   │                     │
   ▼                     ▼
   parser → QuoteCommand │
               │         │
               ▼         ▼
         prepareQuote()
               │
               ▼
         confirm() + createQuote()
               │
               ▼
            api/ (POST)
```

## Parser → QuoteCommand (no QuoteDraft)

El parser del DSL produce un `QuoteCommand`, no un `QuoteDraft`.

```typescript
// shared/types/commands.ts
interface QuoteCommand {
  action: "cotizar" | "preview";
  cliente: string;       // raw text
  items: Array<{ cantidad: number; producto: string }>;
  fecha: string;         // raw text
  hora?: string;
  vehiculo?: string;
  condiciones?: string;
}
```

`prepareQuote(QuoteCommand)` lo valida, resuelve entidades contra la API y construye un `QuoteDraft` parcial para preview.

Esto desacopla el DSL del dominio. Mañana podríamos cambiar el DSL sin tocar `prepareQuote`.

## Estructura del frontend

```
plugins/ventas/cotizacion/frontend/
├── shared/
│   ├── application/
│   │   ├── prepareQuote.ts
│   │   ├── confirmQuote.ts
│   │   └── createQuote.ts
│   ├── api/
│   │   └── index.ts
│   ├── types/
│   │   ├── index.ts
│   │   └── commands.ts
│   └── hooks/
│       └── useDraftList.ts
│
├── console/                 # Experiencia Consola (DSL)
│   ├── parser/
│   │   ├── lexer.ts         # Tokenización
│   │   └── parser.ts        # QuoteCommand
│   ├── autocomplete.ts      # CompletionProvider
│   ├── commands/
│   │   ├── draft.ts         # draft list, draft open, draft show, draft refresh
│   │   └── index.ts         # Registro de comandos
│   └── shell.ts             # Shell wrapper, historial, aliases
│
├── ui/                      # Experiencia Formulario
│   ├── CustomerSelect.tsx
│   ├── ProductLinesEditor.tsx
│   ├── DateTimePicker.tsx
│   └── VehicleSelect.tsx
│
├── components/              # Presentación reutilizable
│   ├── QuotePreview.tsx     # Preview / draft / detalle / readonly / impresión
│   └── DraftExplorer.tsx    # Tabla + expand + preview + navegación
│
└── pages/
    └── CotizacionPage.tsx   # Toggle Consola/Formulario + split con DraftExplorer

register.ts
```

## Modo Consola

El parser produce `QuoteCommand` → `prepareQuote()` → preview + y/n → `createQuote()`.

**Sistema de comandos consistente:**

```
draft list                  # Lista drafts recientes
draft open 42               # Abre detalle
draft show 42               # Sinónimo
draft refresh               # Recarga lista
```

Escalable a otros dominios:
```
stock list
stock show 42
pedido list
pedido open 55
```

## Modo Formulario

Campos visuales → construye `QuoteCommand` manualmente → `prepareQuote()` → preview + y/n → `createQuote()`.

Mismos pasos, mismo `QuoteCommand`, mismo `prepareQuote()`.

| Campo | Componente | Fuente |
|---|---|---|
| Cliente | Combobox con búsqueda | `GET /customers/search` |
| Items | Lista editable (producto + cantidad) | `GET /products/search` |
| Fecha | DatePicker + shortcuts | — |
| Hora | Select (mañana/tarde/noche/HH:MM) | — |
| Vehículo | Combobox con búsqueda (opcional) | `GET /vehicles` |
| Condiciones | TextArea (opcional) | — |

Botones: `[Previsualizar]` → `prepareQuote()` → `QuotePreview` → `[Crear]` (con y/n).

## DraftExplorer

- Tabla compacta debajo del editor activo.
- Columnas: #, Cliente, Items, Entrega, Estado.
- Click en fila → expande detalle inline con `QuotePreview`.
- Click en otra fila → cierra la anterior, abre la nueva (navegación).
- Auto-refresh: `invalidateQueries` al crear + `refetchOnWindowFocus`.
- Sin polling fijo.

## QuotePreview

Un solo componente para todo estado de visualización de un draft:

| Estado | Uso |
|---|---|
| Preview | Antes de confirmar |
| Draft | Recién creado |
| Detalle | Desde DraftExplorer |
| Readonly | Consulta externa |
| Impresión | Layout para PDF (futuro) |

## Flujo de creación

```
Consola:                              Formulario:
  usuario escribe                       usuario completa campos
       │                                     │
       ▼                                     │
  QuoteCommand ◀──── parser ──────────── QuoteCommand
       │                                     │
       ▼                                     ▼
  prepareQuote(QuoteCommand)           prepareQuote(QuoteCommand)
       │                                     │
       ▼                                     ▼
  QuotePreview + y/n                   QuotePreview + y/n
       │                                     │
       ▼                                     ▼
  confirmQuote() → createQuote()       confirmQuote() → createQuote()
       │                                     │
       ▼                                     ▼
  POST → invalidateQueries              POST → invalidateQueries
```

## Criterios de aceptación

1. Consola y formulario producen el mismo `QuoteCommand` y pasan por el mismo `prepareQuote()`.
2. El parser produce `QuoteCommand`, no `QuoteDraft`.
3. El operador puede crear una cotización en <10s desde cualquier modo.
4. El toggle Consola/Formulario persiste la preferencia en sessionStorage.
5. `invalidateQueries` refresca el DraftExplorer inmediatamente después de crear.
6. Click en una draft expande su detalle (QuotePreview) sin recargar; click en otra cierra la anterior.
7. `draft list` y `draft open` funcionan en modo consola.
8. El preview es el mismo componente (`QuotePreview`) en preview, draft, detalle.
9. La UI nunca llama `apiRequest` directamente — solo via `shared/application/`.

## Ciclo de vida del QuoteDraft

```
[Consola / Formulario]
        │
        ▼
   QuoteDraft (status=DRAFT)       ← se crea acá
        │
        │  (confirmar — siempre en ventas)
        ▼
   QuoteDraft (status=CONFIRMED)   ← intención firme, disponible para planificar
        │
        │  (usuario crea PlanningEntry explícitamente)
        ▼
   QuoteDraft (status=CONVERTED)   ← ya planificado
        │
        ▼
   PlanningEntry (quote_id único)  ← creado manualmente desde planning
        │
        ▼
   VehicleSession                  ← ejecución real
```

### Principios

1. **Planning no modifica drafts.** Planning solo lee drafts en estado `DRAFT` (demanda estimada) y puede disparar la acción de confirmar, pero el cambio de estado ocurre en ventas.
2. **La confirmación no es planificación.** Confirmar un draft cambia su estado en ventas (`DRAFT → CONFIRMED`). Recién ahí está disponible para planificar, pero no se crea un `PlanningEntry` automáticamente.
3. **La creación de PlanningEntry es explícita.** El usuario decide cuándo crear una entrada de planificación. No se genera automáticamente al confirmar.
4. **Planning no es dueño del draft.** El draft pertenece a ventas. Planning solo referencia su ID como `source: "quote_confirmed"`.

### Autoridad de confirmación

La confirmación (`DRAFT → CONFIRMED`) **siempre ocurre en el dominio de ventas**, aunque el botón esté en la interfaz de planning. planning dispara la acción, ventas cambia el estado. Esto evita que planning tome decisiones que no le corresponden.

### Estados del QuoteDraft

| Estado | Significado | Visible en planning | PlanningEntry |
|---|---|---|---|
| `DRAFT` | Intención, tal vez | Sí, como **demanda estimada** (solo lectura) | No |
| `CONFIRMED` | Se va a ejecutar | Sí, **disponible para planificar** | No (aún no creado) |
| `CONVERTED` | Ya planificado | No (reemplazado por PlanningEntry) | Sí (único por quote) |
| `CANCELLED` | Descartado | No | No |

### Reglas de integridad

1. **Un QuoteDraft CONFIRMED no puede generar más de un PlanningEntry.** Al crear un `PlanningEntry`, el draft pasa a `CONVERTED` y se impone `unique(quote_id)` en la tabla de planning.
2. **CONVERTED no significa ejecutado.** Solo significa que fue planificado. La ejecución real ocurre en `VehicleSession`.
3. **Si un CONFIRMED se cancela y ya tiene PlanningEntry**, la cancelación debe propagarse a planning (nota: implementación futura, no en este borrador).

### Demanda estimada (DRAFT en planning)

Los drafts en estado `DRAFT` visibles en planning **no afectan**:
- ❌ Capacidad calculada
- ❌ Disponibilidad de vehículos
- ❌ Asignación de recursos

Son solo una referencia visual de intención de compra.

### Acción: confirmar para planificación

Desde la vista de planning, el usuario ve los drafts `DRAFT` como "Demanda pendiente" (solo lectura) y puede ejecutar:

```
[Confirmar para planificación]  ← botón en planning
        │
        ▼  (llamada API a ventas: PATCH /cotizaciones/{id}/status)
   QuoteDraft.status = CONFIRMED   ← el cambio lo hace ventas
        │
        ▼  (usuario crea PlanningEntry manualmente)
   PlanningEntry.create(source="quote_confirmed", quote_id=...)
   QuoteDraft.status = CONVERTED   ← ventas actualiza
```

Esto no rompe la separación de dominios:
- **Ventas** decide la intención y cambia el estado
- **Logística** decide la ejecución y crea `PlanningEntry`
- Planning nunca escribe sobre el draft
