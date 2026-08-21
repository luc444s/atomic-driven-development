# A.SPEC [TMS-014] — Todos los mapas apuntan a Trujillo-Perú (default geográfico)

> Verdicto speccer: `ACCEPT_ONE`. Verdad independiente falsable: el centro geográfico por
> defecto de los mapas del plugin logistics es **Trujillo, Perú** (`-8.115994, -79.029858`),
> no Madrid ni Andalucía. Cuando un mapa no tiene marcadores ni ruta que lo enfoque, se
> centra en Trujillo.

## WHY

El sistema opera en Perú (legacy ERP OXIPUR, rutas de reparto en Trujillo). Sin embargo:

- `map-defaults.ts` → `DEFAULT_MAP_CENTER = { lat: 40.4168, lng: -3.7038 }` (Madrid).
- `CreateJornadaDialog.tsx:220` y `planning-reservation-form.tsx:230` → `{ lat: 37.18, lng: -4.75 }`
  (Andalucía) como fallback cuando no hay marcadores.

Al abrir un mapa vacío (crear jornada, planificación, builder de ruta, mapa de contexto) el
operador peruano ve Europa. El default correcto es donde opera la flota.

## WHAT

Existe un comportamiento observable: todo mapa sin marcadores ni ruta asignada se centra en
Trujillo, Perú. Los centros hardcodeados europeos se reemplazan por una constante única,
reutilizable, definida en `map-defaults.ts`.

## SCOPE

- Backend: ninguno.
- Frontend logistics:
  - `components/route-builder/map-defaults.ts` — `DEFAULT_MAP_CENTER = { lat: -8.115994, lng: -79.029858 }`.
  - `components/vehicle-sessions/CreateJornadaDialog.tsx:220` — fallback `{ lat: 37.18, lng: -4.75 }`
    → importar `DEFAULT_MAP_CENTER` (o el mismo valor inline si no conviene importar).
  - `planning/dialogs/planning-reservation-form.tsx:230` — idem.
- No se toca `vendor/systutor-shell` (el `LocationPicker` del Core conserva su default Madrid;
  queda declarado fuera de scope — ver OUT OF SCOPE).

## OUT OF SCOPE

- `vendor/systutor-shell/src/ui/location-picker.tsx` (Core externo, submodule): su default
  `{ 40.4168, -3.7038 }` persiste. Cambiarlo exige PR al repo shell + bump de pin — decisión
  separada.
- Reposicionar/ajustar el zoom por defecto de los mapas.
- Mapas que reciben `value`/marcadores: si el formulario trae coordenadas, esas mandan (el
  default solo aplica cuando no hay nada que enfocar).
- Backend, tests de infraestructura, geocoding.

## CONTRACT

- Precondición: un mapa del plugin logistics se renderiza sin `markers[]` con posición, sin
  ruta planificada y sin valor inicial.
- Postcondición: el centro del mapa es `{ lat: -8.115994, lng: -79.029858 }`.
- `DEFAULT_MAP_CENTER` mantiene su nombre y contrato (consumidores existentes no cambian API).
- Cuando existen marcadores, ruta planificada o valor de formulario, el mapa usa ESOS datos
  (comportamiento actual intacto).

## INVARIANTS

```yaml
invariants:
  - "el default solo aplica cuando no hay marcadores/ruta/valor que enfoque el mapa"
  - "no se toca el Core (vendor/systutor-shell) en este cambio"
  - "la constante conserva el nombre DEFAULT_MAP_CENTER (consumidores existentes intactos)"
  - "no cambia zoom ni comportamiento de pan/centrado automático"
```

## VERIFICATION

- Frontend (Vitest, lógica pura): test que `DEFAULT_MAP_CENTER` de `map-defaults.ts` es
  `{ lat: -8.115994, lng: -79.029858 }`.
- Grep: sin ocurrencias de `37.18` ni `40.4168` en `plugins/logistics/frontend` (los pickers
  del Core quedan fuera por scope).
- E2E manual: abrir "Crear jornada" y "Planificación" sin coordenadas → mapa centrado en
  Trujillo.

## DECISIONES REGISTRADAS

- **D-TMS-014-1**: Trujillo como default único. Reemplaza Madrid (map-defaults) y Andalucía
  (fallbacks de diálogos) por el mismo valor.
- **D-TMS-014-2**: el `LocationPicker` del Core queda fuera de scope (submodule); su default
  Madrid persiste hasta un cambio en el repo `systutor-shell`.

## ROLLBACK

- Reversible: revertir los valores en `map-defaults.ts` y los dos fallbacks de diálogos a sus
  coordenadas europeas. Sin migración ni datos.

## Change Surface

```yaml
change_surface:
  allowed:
    - "editar plugins/logistics/frontend/components/route-builder/map-defaults.ts"
    - "editar plugins/logistics/frontend/components/vehicle-sessions/CreateJornadaDialog.tsx"
    - "editar plugins/logistics/frontend/planning/dialogs/planning-reservation-form.tsx"
    - "crear apps/web/src/lib/map-defaults.test.ts"
  prohibited:
    - "tocar vendor/systutor-shell"
    - "tocar backend"
    - "cambiar zoom/pan/autoFit"
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - "centro por defecto de mapas logistics (ruta, jornada, planificación, contexto)"
  indirect:
    - "clientes del mapa logísticos que no traen coordenadas"
  must_not_affect:
    - "mapas con marcadores/ruta/valor (usan sus datos, no el default)"
    - "LocationPicker del Core"
```

## Composition

```yaml
composition:
  requires_aspecs:
    - "ninguna (cambio autonómo de configuración de UI)"
  must_compose_with:
    - "LocationMap / LocationPicker (solo reciben center, no se modifica el contrato)"
  systemic_invariants:
    - "el default no pisa datos reales"
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: un único default geográfico para los mapas del plugin
  entrypoints_must_stay_thin: true
  preferred_new_logic_locations:
    - "plugins/logistics/frontend/components/route-builder/map-defaults.ts (constante única)"
```

## Traceability

- Requirement: mapas del plugin apuntan a Trujillo-Perú por defecto
- Commit: pendiente
- Deployment: main (+ TMS lo absorbe por rebase/merge)

## Definition of Done

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Independent falsable truth exists now (default Trujillo en mapas sin datos)
- [x] Invariants preserved
- [x] Verification passed (verifier-ADD run)
- [x] Rollback / compensation is honest
- [x] Composition checks passed when applicable
- [x] No unrelated changes
- [x] Structural constraints respected
- [x] Traceability established

## Verifier ADD — coverage map

```
contract.default-trujillo        -> test map-defaults (1, passed)
contract.consumidores-intactos   -> DEFAULT_MAP_CENTER mantiene nombre; tsc limpio
invariant.sin-centros-europa     -> grep vacío de 40.4168/37.18/-3.7038/-4.75 en logistics frontend
invariant.no-core                -> vendor/systutor-shell sin cambios (git status)
invariant.no-zoom-pan            -> solo se cambió el valor del centro (diff)
contract.no-pisar-datos          -> fallbacks usan ?? (solo aplica sin marcadores/ruta/valor)

VERDICT: PASS
```