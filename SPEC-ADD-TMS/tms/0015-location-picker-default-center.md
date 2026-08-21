# A.SPEC [TMS-015] — LocationPicker del Core acepta defaultCenter (almacenes/clientes → Trujillo)

> Verdicto speccer: `ACCEPT_ONE`. Verdad independiente falsable: el `LocationPicker` del Core
> es configurable con un centro por defecto (`defaultCenter`) en lugar de hardcodear Madrid.
> Los formularios de almacenes, puntos de entrega (clientes) y escaneo de cilindros del plugin
> logistics le pasan Trujillo, Perú. Sin markers ni valor previo, el mapa abre en Trujillo.

## WHY

TMS-014 fijó `DEFAULT_MAP_CENTER = Trujillo` para los mapas operativos del plugin, pero quedó
un hueco: **almacenes, puntos de entrega y escaneo usan `LocationPicker` del Core**
(`vendor/systutor-shell/src/ui/location-picker.tsx:202`), cuyo default es Madrid hardcodeado:

```ts
const defaultCenter: LatLng = value ?? { lat: 40.4168, lng: -3.7038 };
```

El picker no acepta un centro configurable y forzar `value={Trujillo}` marcaría un punto
"seleccionado" (falso dato en almacén/cliente). La solución limpia es Core-first: el
`LocationPicker` acepta `defaultCenter` opcional; el plugin le pasa Trujillo.

## WHAT

Existe un comportamiento observable: `LocationPicker` recibe una prop **opcional** `defaultCenter:
{ lat, lng }`. Si `value` es `null`, el mapa se centra en `defaultCenter`; si `defaultCenter`
también es `undefined`, usa el default histórico (Madrid) para no romper consumidores que no lo
definen. El plugin logistics pasa `DEFAULT_MAP_CENTER` (Trujillo) en sus formularios de
almacén, punto de entrega y escaneo.

## SCOPE

- Core (`vendor/systutor-shell/src/ui/location-picker.tsx`):
  - Tipo `LocationPickerProps` gana `defaultCenter?: { lat: number; lng: number }`.
  - `const defaultCenter = value ?? props.defaultCenter ?? { Madrid }`.
  - `console.log` de geocoding (`[GEOCODE-*]`) se elimina o se conserva según juicio (fuera del
    contrato; se revisa en implementación).
- Plugin logistics (3 call sites `LocationPicker`):
  - `pages/WarehousesPage.tsx` → `defaultCenter={DEFAULT_MAP_CENTER}`.
  - `pages/DeliveryPointsPage.tsx` → `defaultCenter={DEFAULT_MAP_CENTER}`.
  - `cylinders/dialogs/ScanDialog.tsx` → `defaultCenter={DEFAULT_MAP_CENTER}`.
- Import de `DEFAULT_MAP_CENTER` desde `components/route-builder/map-defaults` en esos 3 archivos.
- **Actualización del submodule**: el cambio a `vendor/systutor-shell` requiere commit en el
  repo shell y bump del pin del submodule en este repo (flujo formal ADR 0030). Como el
  submodule apunta a una rama desadjuntada con commit vigente, la implementación local edita
  el archivo del submodule y el repo padre registra el nuevo commit del pin.

## OUT OF SCOPE

- Backend.
- Otros componentes del shell (location-search no tiene default de centro; no se toca).
- El default histórico de Madrid no se elimina del Core (backwards-compat para consumidores
  que no pasen `defaultCenter`).
- Cambiar zoom/pan del picker (`DEFAULT_ZOOM`, `zoom={value ? 13 : 6}`).
- Los `console.log` de geocode (son debugging existente; solo se retiran si no altera flujo).

## CONTRACT

- Precondición: `LocationPicker` se renderiza con `value === null` y `defaultCenter` provisto.
- Postcondición: el mapa se centra en `defaultCenter` (zoom sin cambio: 6).
- Precondición (compat): consumidor sin prop `defaultCenter` → comportamiento idéntico al
  actual (Madrid).
- Precondición: `value !== null` → `value` manda (cambios de vista al seleccionar se mantienen).
- `defaultCenter` es opcional y no altera `onChange`, `onAddressResolved`, ni el drag/click.

## INVARIANTS

```yaml
invariants:
  - "backwards-compat: consumidores sin defaultCenter conservan Madrid"
  - "value no-null manda sobre defaultCenter"
  - "el picker no crea datos falsos (defaultCenter NO es value)"
  - "el plugin usa una sola constante (DEFAULT_MAP_CENTER) para todos los mapas"
  - "el core se modifica SOLO con prop nueva opcional (sin breaking change)"
```

## VERIFICATION

- Core: smoke build del shell (`vendor/systutor-shell`) SIN errores de tipos TS.
- Plugin: typecheck (`tsc --noEmit`) de los 3 call sites + import `DEFAULT_MAP_CENTER`.
- Grep: `defaultCenter=` presente en los 3 call sites del plugin.
- Frontend (Vitest, lógica pura): test de `DEFAULT_MAP_CENTER` Trujillo (ya existe, TMS-014)
  se mantiene verde.
- E2E manual: abrir alto cito "Nuevo almacén"/"Nuevo punto de entrega"/"Escaneo" sin coordenadas
  → el mapa abre en Trujillo (comportamiento actual: Madrid).
- Negativo (I2): en el mismo form, hacer clic en el mapa → `onChange` recibe coords del click
  (no Trujillo aunque `value` siga null hasta el click).

## DECISIONES REGISTRADAS

- **D-TMS-015-1**: prop nueva **opcional** `defaultCenter` — no cambiar el default hardcodeado
  del Core a Trujillo (eso rompería otros consumidores no-Perú y contradice Core-first).
- **D-TMS-015-2**: submodule se edita in-place y el pin se actualiza vía commit del submodule +
  commit padre (flujo ADR 0030), no branch nueva.

## ROLLBACK

- Core: quitar la prop `defaultCenter` de `LocationPickerProps` y volver a
  `value ?? { Madrid }`; el pin del submodule vuelve al commit anterior.
- Plugin: quitar `defaultCenter={DEFAULT_MAP_CENTER}` de los 3 call sites.
- Sin migración ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - "editar vendor/systutor-shell/src/ui/location-picker.tsx (prop defaultCenter)"
    - "editar plugins/logistics/frontend/pages/WarehousesPage.tsx"
    - "editar plugins/logistics/frontend/pages/DeliveryPointsPage.tsx"
    - "editar plugins/logistics/frontend/cylinders/dialogs/ScanDialog.tsx"
  prohibited:
    - "tocar backend"
    - "borrar el default Madrid del Core"
    - "alterar onChange / onAddressResolved / drag / click"
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - "LocationPicker del Core (prop nueva, additive)"
    - "3 formularios logistics: almacén, punto de entrega, escaneo"
  indirect:
    - "cualquier consumidor futuro del picker puede usar defaultCenter"
  must_not_affect:
    - "consumidores existentes sin la prop (Madrid sigue)"
    - "geocode reverse/forward (no cambia)"
```

## Composition

```yaml
composition:
  requires_aspecs:
    - "TMS-014 (DEFAULT_MAP_CENTER Trujillo en map-defaults)"
  must_compose_with:
    - "LocationMap / LocationPicker del Core (contrato center/handler intacto)"
  systemic_invariants:
    - "todos los mapas de logistics apuntan a Trujillo cuando no hay datos"
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: el Core permite configurar su default de centro; el plugin configura Trujillo
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  preferred_new_logic_locations:
    - "vendor/systutor-shell/src/ui/location-picker.tsx (prop defaultCenter)"
```

## Traceability

- Requirement: almacenes, clientes y escaneo abren sus mapas en Trujillo (default configurable)
- Commit: pendiente (submodule shell + repo padre)
- Deployment: main (+ TMS lo absorbe por rebase/merge)

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (defaultCenter configurable + Trujillo en los 3 forms)
- [x] Invariants preserved
- [x] Verification passed (verifier-ADD run)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established

## Verifier ADD — coverage map

```
contract.defaultCenter-configurable -> location-picker.tsx inicialCenter = value ?? defaultCenter ?? Madrid (code)
contract.compat-madrid             -> defaultCenter opcional; sin prop conserva Madrid (code)
contract.plugin-trujillo           -> defaultCenter={DEFAULT_MAP_CENTER} en WarehousesPage/DeliveryPointsPage/ScanDialog (3)
invariant.value-manda              -> value ?? defaultCenter (code: value prioriza)
invariant.sin-datos-falsos         -> defaultCenter NO es value; ClickMarker usa value solo (code)
invariant.backend-no-toca          -> git diff: solo frontend + submodule
invariant.core-additivo            -> prop nueva opcional, sin romper tipo (tsc limpio)
composition.tms-014                -> DEFAULT_MAP_CENTER Trujillo probado (test map-defaults pasado)
composition.submodule-pin          -> fca1c27 -> 0a6e3dc (solo location-picker, diff verificado)

VERDICT: PASS
```

## Nota de implementación

- El cambio del Core vive en el repo `systutor-shell` (commit `0a6e3dc`) y se consume fijando
  el pin del submodule. Regla ADR 0030 respetada: no se edita el kernel desde el repo padre,
  se corrige el pin al commit aprobado.