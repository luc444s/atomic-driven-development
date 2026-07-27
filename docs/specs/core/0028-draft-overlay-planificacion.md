---
id: "0028"
title: "DraftOverlay — Drafts de ventas proyectados en el calendario de planificación"
domain: ventas + logistics
module: cotizacion + planning
status: vigente
requires:
  - docs/specs/core/0027-cotizacion-ui-tui-hibrida.md
  - docs/adr/0028-single-use-case-multiples-adaptadores.md
  - docs/specs/core/0025-planificacion-calendar-first-y-reserva-de-capacidad.md
---

# SPEC 0028 — DraftOverlay: drafts proyectados en planificación

## Estado

Vigente — implementación en curso

## Problema

Un operador crea una cotización en ventas. El planificador no la ve. Tiene que cambiar de pantalla, ir a Cotización, buscar el draft, confirmarlo manualmente, volver a Planificación, y recién ahí planificar. Esto rompe el flujo y genera fricción entre dominios.

## Principio arquitectónico

**Overlay, no entidad real.** Los drafts no están en el calendario de planificación. Se proyectan sobre él como contexto visual. No ocupan capacidad, no bloquean recursos, no se persisten en planning.

```
Layer 1: Calendar real (PlanningEntry)     → eventos sólidos, ocupan slots
Layer 2: DraftOverlay (QuoteDraft)         → bloques translúcidos, solo atención
```

## Propuesta

Un componente `DraftOverlay` que se renderiza debajo del calendario de planificación, mostrando los drafts de cada fecha como una tira sutil. Dos estados visuales:

| Estado | Visual | Interacción |
|--------|--------|-------------|
| `DRAFT` | Gris translúcido | Click → diálogo de confirmación → `PATCH /cotizaciones/{id}/status` → pasa a CONFIRMED |
| `CONFIRMED` | Verde pálido + ⚡ icono | Click → abre diálogo "Crear PlanningEntry desde cotización" |

**Hover**: tooltip rápido con cliente, items, condiciones — sin necesidad de click.

**Futuro**: drag & drop de CONFIRMED directo al slot del calendario; overlay alineado por fecha dentro del grid (inline).

## Flujo de interacción

```
DRAFT (gris)
  │
  │ click → diálogo: "¿Confirmar cotización #CTZ-0042?"
  │         muestra: cliente, items, fecha, condiciones
  │         botones: [Cancelar] [Confirmar]
  │
  ▼
PATCH /cotizaciones/{id}/status  →  status = CONFIRMED
  │
  ▼
CONFIRMED (verde pálido)
  │
  │ click → diálogo: "Crear planificación desde cotización"
  │         campos pre-llenados: vehículo, productos, cantidades, fecha
  │         botones: [Cancelar] [Crear PlanningEntry]
  │
  ▼
POST /planning/reservations  →  PlanningEntry creada
  │
  ▼
PATCH /cotizaciones/{id}/status  →  status = CONVERTED
  │
  ▼
Evento real en calendario (sólido)
```

## Layout

```
┌─── Planificación ──────────────────────────────────────────┐
│ [Mes] [Semana] [Día]     < Jul 2026 >     [Vehículo ▾]    │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─── Calendario real (PlanningEntry) ──────────────────┐  │
│  │  Mar 25        Mar 26        Mar 27                  │  │
│  │  ┌──────────┐  ┌──────────┐                          │  │
│  │  │ PL-001   │  │ PL-002   │                          │  │
│  │  │ 200 u    │  │ 150 u    │                          │  │
│  │  └──────────┘  └──────────┘                          │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                            │
  │  ┌─── DraftOverlay (capa independiente) ──────────────────┐  │
  │  │  Mar 25                        Mar 26                │  │
  │  │  ┌ ⬜ #CTZ-42 Juan 400u ────┐  ┌ ⚡ #CTZ-43 Ana ──┐  │  │
  │  │  │ DRAFT · confirmar        │  │ CONFIRMED · planif │  │  │
  │  │  └──────────────────────────┘  └───────────────────┘  │  │
  │  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## DraftOverlay — diseño visual

Cada draft se renderiza como una tarjeta compacta:

```
┌─────────────────────────────────────────────┐
│ ⬜ #CTZ-0042  Juan Pérez      DRAFT         │
│    400 cilindros · 2026-07-25               │
│    Cond: pago contra entrega                │
│                          [Confirmar]        │
└─────────────────────────────────────────────┘
```

- **DRAFT**: fondo `bg-white/5`, borde izquierdo `border-l-2 border-muted-foreground/30`
- **CONFIRMED**: fondo `bg-emerald-500/5`, borde izquierdo `border-l-2 border-emerald-500/40`, icono ⚡ y tooltip "Listo para planificar"
- Hover: tooltip con cliente, items, condiciones
- Sin altura fija — el calendario real mantiene su espacio
- Máximo 3 drafts visibles por fecha; "+N más" si excede

## Diálogo de confirmación (DRAFT → CONFIRMED)

Al hacer clic en un draft DRAFT:

```
┌─── Confirmar cotización ───────────────────────────────────┐
│                                                             │
│  ¿Confirmar #CTZ-0042 para planificación?                   │
│                                                             │
│  Cliente      Juan Pérez                                    │
│  Items        400 × Cilindro 10kg                           │
│  Entrega      2026-07-25                                    │
│  Condiciones  pago contra entrega                           │
│                                                             │
│  Al confirmar, la cotización estará disponible para         │
│  planificar. Ya no será un borrador.                        │
│                                                             │
│              [Cancelar]    [Confirmar]                      │
└─────────────────────────────────────────────────────────────┘
```

## Diálogo de creación de PlanningEntry (CONFIRMED → planificado)

Al hacer clic en un draft CONFIRMED, se abre el diálogo de creación de PlanningEntry con campos pre-llenados desde el draft: vehículo (si asignado), productos y cantidades, fecha.

Al crear la PlanningEntry, el draft pasa automáticamente a `CONVERTED`.

## API

### Endpoints nuevos/modificados

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/v1/plugins/ventas/cotizaciones?status=DRAFT&status=CONFIRMED&date_from=...&date_to=...` | Listar drafts filtrados por estado y rango de fechas |
| `PATCH` | `/api/v1/plugins/ventas/cotizaciones/{id}/status` | Cambiar estado de un draft (body: `{"status": "CONFIRMED"}`) |

### Endpoints consumidos

| Método | Ruta | Dueño | Descripción |
|--------|------|-------|-------------|
| `POST` | `/api/v1/plugins/logistics/planning/reservations` | logistics | Crear PlanningEntry desde CONFIRMED |

### Response PATCH

```json
{
  "id": "uuid",
  "status": "CONFIRMED",
  "customer": { "id": "uuid", "name": "Juan Pérez" },
  "items": [...],
  "delivery_date": "2026-07-25",
  "delivery_time": "14:00",
  "vehicle": null,
  "conditions": "pago contra entrega",
  "created_at": "2026-07-25T15:30:00Z"
}
```

## Permisos

| Permiso | Descripción |
|---------|-------------|
| `ventas.cotizacion.confirm` | Confirmar drafts (DRAFT → CONFIRMED) |

## Eventos

| Evento | Payload |
|--------|---------|
| `ventas.cotizacion.confirmed` | `{ quote_id, previous_status: "DRAFT", new_status: "CONFIRMED", confirmed_by }` |

## Estructura del frontend

```
plugins/logistics/frontend/planning/
├── DraftOverlay/
│   ├── DraftOverlay.tsx        # Contenedor: fetch drafts, agrupa por fecha
│   ├── DraftCard.tsx           # Tarjeta individual (gris/verde según status, hover tooltip)
│   └── ConfirmDraftDialog.tsx  # Diálogo de confirmación DRAFT → CONFIRMED
```

`DraftOverlay` se renderiza en `PlanningWorkspace.tsx` debajo del calendario, como capa independiente.

## Criterios de aceptación

1. Los drafts `DRAFT` y `CONFIRMED` aparecen en una tira debajo del calendario, agrupados por fecha de entrega.
2. Los drafts `DRAFT` se ven grises translúcidos y muestran botón "Confirmar".
3. Al confirmar un DRAFT, se hace `PATCH /cotizaciones/{id}/status` y el draft pasa a verse verde (CONFIRMED).
4. Los drafts `CONFIRMED` muestran botón "Planificar" que abre el diálogo de creación de PlanningEntry con datos pre-llenados.
5. Al crear la PlanningEntry, el draft pasa a `CONVERTED` y desaparece del overlay.
6. Los drafts NO ocupan slots del calendario real — son una capa visual independiente.
7. Los drafts NO afectan el cálculo de capacidad del calendario.
8. Máximo 3 drafts visibles por fecha en el overlay; "+N más" si excede.
9. El overlay se refresca automáticamente al confirmar o al crear PlanningEntry.
10. El planificador nunca sale de la pantalla de planificación durante el flujo.

## Riesgos

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| Confundir draft con evento real | Alto | Estilo visual claramente diferenciado (translúcido vs sólido) |
| Saturar el overlay con muchos drafts | Medio | Límite de 3 por fecha + "+N más" |
| Doble confirmación accidental | Bajo | Diálogo explícito antes del PATCH |
| Crear PlanningEntry sin vehículo asignado | Medio | Si el draft no tiene vehículo, el diálogo pide seleccionar uno |
