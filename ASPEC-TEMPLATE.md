# A.SPEC [ID] — [Título: verbo + objeto observable]

> Ejemplo de título: `Discover existing WordPress containers`

## WHY

<!-- ¿Qué problema concreto existe? -->

## WHAT

<!-- ¿Qué comportamiento observable, verdad estructural o garantía operacional cambia? Una sola transición o una sola verdad independiente y falsable. "Preparar para luego" no basta. -->

## SCOPE

<!-- ¿Qué entra? -->

## OUT OF SCOPE

<!-- ¿Qué explícitamente NO entra? -->

## CONTRACT

<!-- Precondiciones, postcondiciones. ¿Qué debe cumplirse y qué verdad nueva queda establecida ahora mismo? -->

## INVARIANTS

<!-- ¿Qué comportamiento existente no puede romperse? Si uno falla: A.SPEC FAILED. Regla de completitud: toda superficie declarada en blast_radius.must_not_affect DEBE tener aquí su invariante correlativo evaluable. -->

```yaml
invariants: []
```

## VERIFICATION

<!-- ¿Cómo demostramos objetivamente que esta verdad ya existe ahora? Comandos, tests, checks. No delegar prueba real a futuras A.SPEC. Incluir checks de composición si esta A.SPEC depende de una capability mayor. -->

## ROLLBACK

<!-- Si es reversible: ¿cómo lo deshacemos? Si es irreversible: ¿cómo compensamos, contenemos, evitamos replay y auditamos? -->

## Change Surface

```yaml
change_surface:
  allowed: []
  prohibited: []
```

## Blast Radius

<!-- Debe declarar must_not_affect de forma coherente con INVARIANTS: cada superficie listada aquí requiere invariante correlativo (ver SPECIFICATION §7.1). -->

```yaml
blast_radius:
  direct: []
  indirect: []
  must_not_affect: []
```

## Composition

<!-- Si esta A.SPEC participa en una capability mayor, declarar dependencias reales y checks del conjunto. No usar esta sección para justificar verdad parcial. -->

```yaml
composition:
  requires_aspecs: []
  must_compose_with: []
  systemic_invariants: []
  composition_checks: []
```

## Structural Constraints

<!-- Cohesion first. File size is only warning signal. -->

```yaml
structural_constraints:
  primary_rule: one coherent responsibility and one main reason to change
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations: []
```

## Traceability

<!-- Requirement → esta A.SPEC → code → migration → test → commit → deployment -->

- Requirement:
- Commit:
- Deployment:

## Definition of Done

- [ ] Objective satisfied
- [ ] Scope respected
- [ ] Contract satisfied
- [ ] Independent falsable truth exists now
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] Rollback / compensation is honest
- [ ] Composition checks passed when applicable
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
