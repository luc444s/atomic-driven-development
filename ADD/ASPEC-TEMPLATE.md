# A.SPEC [ID] — [Título: verbo + objeto observable]

> Ejemplo de título: `Discover existing WordPress containers`

## WHY

<!-- ¿Qué problema concreto existe? -->

## WHAT

<!-- ¿Qué comportamiento observable o verdad estructural cambia? Una sola transición o una sola verdad independiente y falsable. "Preparar para luego" no basta. -->

## SCOPE

<!-- ¿Qué entra? -->

## OUT OF SCOPE

<!-- ¿Qué explícitamente NO entra? -->

## CONTRACT

<!-- Precondiciones, postcondiciones. ¿Qué debe cumplirse? -->

## INVARIANTS

<!-- ¿Qué comportamiento existente no puede romperse? Si uno falla: A.SPEC FAILED -->

```yaml
invariants: []
```

## VERIFICATION

<!-- ¿Cómo demostramos objetivamente que esta verdad ya existe ahora? Comandos, tests, checks. No delegar prueba real a futuras A.SPEC. -->

## ROLLBACK

<!-- Si es reversible: ¿cómo lo deshacemos? Si es irreversible: ¿cómo compensamos, contenemos, evitamos replay y auditamos? -->

## Change Surface

```yaml
change_surface:
  allowed: []
  prohibited: []
```

## Blast Radius

```yaml
blast_radius:
  direct: []
  indirect: []
  must_not_affect: []
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
- [ ] Invariants preserved
- [ ] Verification passed
- [ ] No unrelated changes
- [ ] Structural constraints respected
- [ ] Traceability established
