# SPEC 0032 — Señalización visual de carga ADR en jornadas

## Estado

Implementado (2026-07-28)

## Contexto

El sistema calcula puntos ADR por producto, por cilindro y totales por jornada. Pero el operador nunca ve una señal visual de que el camión transporta mercancía peligrosa. Los puntos ADR se muestran como un número más, sin distinción visual de un camión con carga normal.

Esto es un riesgo operativo real: un operador puede no saber que está manejando una carga ADR hasta que revisa la carta porte en detalle, o peor, hasta que ocurre un incidente.

### Situación actual

| Componente | ADR visible | Señal visual |
|---|---|---|
| Carta Porte | `ADR total: 1250` | Ninguna |
| Composición | `ADR: 150 puntos` por línea | Ninguna |
| Planning | `adr_required: true/false` | Checkbox en formulario |
| Cilindro | `adr_category`, `adr_un_number` | Texto en ficha |

## Solución

### Principio

**Si `total_adr_points > 0`, el operador debe verlo sin tener que buscarlo.**

### Componentes afectados

```
plugins/logistics/frontend/components/vehicle-sessions/
├── OperationalSummaryInline.tsx    — badge ADR en el resumen
├── SessionWorkspaceHeader.tsx      — badge ADR en cabecera
├── RouteCompositionCard.tsx        — highlight en líneas con ADR
└── SessionWaybillCard.tsx          — highlight en carta porte
```

### Cambios concretos

#### 1. SessionWorkspaceHeader — Badge ADR

Si la sesión tiene composición con `total_adr_points > 0`, mostrar un badge ámbar junto al título o estado:

```tsx
{composition?.totals?.total_adr_points > 0 && (
  <span className="rounded bg-amber-500/15 px-2 py-0.5 text-xs font-semibold text-amber-400">
    ADR {composition.totals.total_adr_points} pts
  </span>
)}
```

#### 2. OperationalSummaryInline — Fila ADR

Agregar una fila al resumen que muestre los puntos ADR con color condicional:

```tsx
total_adr_points > 0 → texto ámbar con label "ADR"
total_adr_points === 0 → sin fila (no mostrar)
```

#### 3. RouteCompositionCard — Líneas con ADR

Las líneas de composición que tienen `adr_points > 0` se muestran con un indicador visual (badge o color de fondo):

```tsx
{line.adr_points && line.adr_points > 0 && (
  <span className="text-amber-400">⚡ ADR {line.adr_points}</span>
)}
```

#### 4. SessionWaybillCard — Totales ADR

El total ADR en la carta porte se muestra con color condicional (ámbar si > 0, muted si 0 o null).

### No incluye

- No modifica el backend (los datos ya existen)
- No modifica el cálculo de puntos ADR
- No agrega validaciones ADR (eso es parte del state machine, ya implementado)
- No modifica el formulario de planning (ya tiene `adr_required`)

## Criterios de aceptación

1. Sesión con `total_adr_points > 0` → badge "ADR N pts" visible en el header del workspace.
2. Sesión con `total_adr_points === 0` → sin badge ADR.
3. Resumen operativo muestra fila ADR solo cuando `total_adr_points > 0`.
4. Composición muestra indicador visual en líneas con `adr_points > 0`.
5. Carta porte muestra total ADR en ámbar cuando > 0.

## Referencias

- `plugins/logistics/frontend/components/vehicle-sessions/SessionWorkspaceHeader.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/OperationalSummaryInline.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/RouteCompositionCard.tsx`
- `plugins/logistics/frontend/components/vehicle-sessions/SessionWaybillCard.tsx`
- `plugins/logistics/backend/services/route_operations.py:574` — `build_current_composition` (calcula ADR)
