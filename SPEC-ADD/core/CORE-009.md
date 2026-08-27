# A.SPEC CORE-009 — Verificación proporcional: vía mecánica y jueces-lite

> `risk: normal` — norma de proceso del canon; reversible (docs), sin señales
> high §4.1, pero modifica el routing de todo el ciclo → merece más que `low`.

## WHY

La ceremonia del ciclo ADD es hoy binaria por A.SPEC: o corre el tren completo
de jueces vía Task (SPECCER→REVIEWER→GENERATOR→VERIFIER→TRACE, ~5.000 tokens de
canon cada uno) o se desvía ad-hoc narrando la excepción en Traceability (lo
hecho en CORE-008 con aprobación del approver). Faltan dos cosas:

1. **Escala intra-ciclo**: §4.1 gradúa la ceremonia *por A.SPEC*, pero no sabe
   variar dentro del ciclo según la naturaleza de las proofs. Dos líneas en
   código transaccional del core exigen jueces; cien líneas de prosa normativa
   verificables 100% con grep/wc no ganan nada con contexto limpio — un comando
   determinista no tiene sesgo que aislar.
2. **Honestidad anti-abuso**: sin gatillo normado, la "desviación" es siempre
   tentadora. La vía mecánica debe exigir condiciones objetivas declaradas,
   no criterio del momento.

Casos reales que motivan esto: CORE-008 (+8/−6, proofs 100% grep/diff-stat,
ejecutado sin jueces por instrucción del approver); ajustes triviales de
código de 2 líneas tratados hoy como si fueran COMPRAS-012.

## WHAT

Una verdad estructural nueva: **el ciclo ADD admite dos modos de ejecución
declarados por el host antes de IMPLEMENT, según la naturaleza objetiva de las
proofs declaradas en VERIFICATION y del blast radius**:

### Modo A — Vía mecánica (main-thread, sin jueces)

Aplica cuando TODAS estas condiciones son verdaderas y quedan declaradas
explícitamente en la A.SPEC:

1. `risk: low` derivado honestamente per §4.1 (reversible, sin señales).
2. Todas las cláusulas de VERIFICATION son comandos deterministas ejecutables
   localmente (grep/wc/diff-stat/tsc/pytest/ruff o equivalentes) con resultado
   binario.
3. Ninguna cláusula requiere juicio semántico ("¿esta prosa es coherente?",
   ¿esta UX es correcta?", "¿este dominio está bien modelado?").
4. Superficie ≤ 3 archivos modificados y blast radius acotado con invariants
   demostrables por diff directo.
5. La A.SPEC declara `mode: mechanical` en su encabezado y lista las condiciones
   cumplidas (1–4) una a una [o invoca una exención automática].

Exenciones automáticas del Modo A (sin necesidad de listar condiciones):

- **Presentación pura** (themes, tokens, colores, estilos, copy, labels,
  layout): aunque la superficie exceda 3 archivos. Proof requerida: build
  (tsc) + diff visual; cero task tools, TRACE opcional (sin migraciones ni
  contratos que anclar, normalmente NO aporta).
- **Frontend consumidor** (comportamiento observable de UI que consume
  endpoints ya probados por tests backend): la verdad dura ya fue verificada
  atrás; aquí basta build + smoke. Máximo TRACE; jueces full sobran.

### Regla backend-decide

Cuando una A.SPEC toca backend y frontend juntos, la ceremonia la fija el
**lado backend** (donde vive la verdad dura: dominio, persistencia,
transacciones); el frontend hereda el trato y nunca lo agrava. El trabajo
pesado se verifica donde el riesgo vive; la presentación no re-ceremoniza lo
ya probado.

Bajo modo A: DEFINE+IMPLEMENT+VERIFY corren en hilo principal; los jueces via
Task son OPCIONALES (host puede lanzarlos si duda); TRACE minimal (sha_anchor +
surface check) sigue OBLIGATORIO para integrar. La desviación no se narra: queda
declarada por el propio `mode:`.

### Modo B — Jueces-lite

Aplica cuando hay juicio genuino pero el blast radius no toca runtime/producto
(cambios de docs/canon/prosa):

- SPECCER + SPEC-REVIEWER sí corren (la calidad del contrato importa).
- GENERATOR corre solo si la superficie > 3 archivos o el parche es no-trivial;
  si no, main-thread lo aplica.
- VERIFIER full NO corre: verificación mecánica de proofs + inspección visual
  del diff documentada como evidence sustitutiva.
- TRACE minimal obligatorio.

Ambos modos REQUIEREN la misma Definition of Done. Lo que cambia es QUIÉN/QUÉ
ejecuta cada fase, no qué debe probarse.

### Contra-guardias (anti-abuso, aplican a ambos modos)

- Si tras integrar en modo A/B un defecto aparece que el ciclo completo habría
  atrapado, la clase de cambio queda marcada: próximas A.SPECs del mismo tema
  vuelven al ciclo completo (registro informal en memoria del proyecto; la
  primera reincidencia obliga a SPEC-REVIEWER retroactivo).
- No puede usarse modo mecánico si existe CUALQUIER señal §4.1 (stock, auth,
  dinero, tenancy, lg_*, migración destructiva) aunque el diff sea de 1 línea.
- El approver puede SIEMPRE exigir el ciclo completo sin justificación; su
  mención en Traceability cierra la discusión.
- La auto-declaración falsa de condiciones 1–5 = subvaloración → REVISE
  retroactivo del propio cambio.

## SCOPE

- `ADD/SPECIFICATION.md` — nueva subsección **§4.2 Verificación proporcional**
  (hospedada junto al risk-tiering §4.1, cohesión temática), ~40 líneas dentro
  del presupuesto F9 (589 actuales; 629 proyectadas excedería 600 — ver nota
  de presupuesto abajo).
- `ADD/task-tools/README.md` — tabla con columna "Modo por defecto"
  (cláusula de una línea por tool).
- `SPEC-ADD/core/CORE-009.md` — esta spec.

Nota de presupuesto F9: §11 queda sincronizado por esta misma enmienda (invariante
CORE-007 activa). El texto §4.2 debe escribirse compacto (~35 líneas efectivas)
para mantener el monolito ≤600; si al redactar supera, esta A.SPEC declara el
rescate: mover la definición completa a task-tools/README.md y dejar en §4.2
solo el gatillo + remisión (máx 10 líneas). Decisión mecánica medible con wc,
sin segunda verdad.

## OUT OF SCOPE

- Auditoría completa de reading-budget (alcance B de CORE-008) — futura.
- Split del canon en artículos.
- Cambiar semántica de veredictos de cualquier juez.
- Tocar otros task-tools fuera de README.md.
- Eximir TRACE (siempre corre, mínimo).

## CONTRACT

Precondiciones:

- Canon estable post-CORE-007 (F1-F9 integrados).
- Presupuesto monolito vigente (≤600 líneas).

Postcondiciones:

- §4.2 existe en el canon con gatillos Modo A/B + contra-guardias evaluables.
- task-tools/README.md declara modo por defecto por tool.
- Una A.SPEC futura puede declarar `mode: mechanical` / `mode: judges-lite`
  y eso basta como autorización del routing elegido (sin narrar desviaciones).
- Las tablas/árbol sincronizados (§1/§11) permanecen coherentes (invariante
  CORE-007).

## INVARIANTS

```yaml
invariants:
  - "Semántica de veredictos PASS/FAIL/GAP/REVISE/SPLIT/REJECT intacta."
  - "§13.5 TRACE y sus checks intactos; TRACE mínimo sigue obligatorio."
  - "Señales hard §4.1 prevalecen sobre modo mecánico SIEMPRE."
  - "task-tools/{SPECCER,SPEC-REVIEWER,GENERATOR,VERIFIER,COMPOSER,TRACE,ATOMIZER}.md byte-idénticos."
  - "MANIFESTO.md y ASPEC-TEMPLATE.md byte-idénticos."
  - "SPECIFICATION.md ≤ 600 líneas tras la enmienda (presupuesto F9)."
```

Correspondencia must_not_affect → INVARIANTS (§7.1): Blast Radius abajo.

## VERIFICATION

Comandos desde root del repo padre (`<sub>` = submodule ADD):

- Gatillo presente: `rg -n "Verificación proporcional|modo: mechanical|judges-lite" <sub>/SPECIFICATION.md` → ≥3 hits en §4.2.
- Contra-guardia hard: `rg -n "prevalece sobre modo mecánico" <sub>/SPECIFICATION.md` → ≥1 hit.
- Budget: `wc -l <sub>/SPECIFICATION.md` → ≤ 600.
- Byte-identity tools: `git -C <sub> diff --name-only HEAD~1 HEAD` → exactamente {SPECIFICATION.md, task-tools/README.md}.
- Sincronía §1: `rg -c "risk \(§4.1\)" <sub>/SPECIFICATION.md` → sin cambio (tabla §1 intacta; nueva fila "Modo (§4.2)" añadida junto a la existente).
- Árbol §11: sin cambios de estructura listada (task-tools/ ya completo post-CORE-007/F4).
- Ejecución de prueba (fixture inline): A.SPEC ficticia con `mode: mechanical`
  violando condición 5 (sin lista de condiciones) → lectura normativa arroja
  requisitos incumplidos sin lanzar jueces (auto-evaluable: la lista declarativa
  es chequeable por grep en la spec candidata).
- Fuente espejada: `rg -n "mechanical|lite" <sub>/task-tools/README.md` → columna presente.

## ROLLBACK

Reversible: revert del commit submodule + bump. Sin migraciones ni estado. Los
modos son opt-in por A.SPEC; nadie queda obligado retroactivamente.

## Change Surface

```yaml
change_surface:
  allowed:
    - ADD/SPECIFICATION.md            # §4.2 + fila §1 + sync §11 si aplica
    - ADD/task-tools/README.md        # columna modo por defecto
    - SPEC-ADD/core/CORE-009.md       # self-inclusion (§5/CORE-007-F1)
  prohibited:
    - ADD/MANIFESTO.md
    - ADD/ASPEC-TEMPLATE.md
    - ADD/task-tools/*.md             # excepto README.md
    - plugins/**
    - apps/**
    - vendor/**
```

## Blast Radius

```yaml
blast_radius:
  direct:
    - add.cycle.routing_modes (§4.2 nuevo)
    - add.tasktools.default_mode_column (README)
  indirect:
    - ceremonia de TODAS las A.SPECs futuras (opt-in declarativo)
  must_not_affect:
    - semántica de veredictos de jueces → invariant 1
    - traceabilidad SHA (§13.5) → invariant 2
    - señales hard de riesgo (§4.1) → invariant 3
    - cuerpos de los 7 task-tools → invariant 4
    - MANIFESTO/TEMPLATE → invariant 5
    - presupuesto monolito → invariant 6
```

## Composition

```yaml
composition:
  requires_aspecs:
    - CORE-003   # risk-tiering que §4.2 extiende intra-ciclo
    - CORE-007   # F1 self-inclusion + presupuesto F9 que respeta esta enmienda
  must_compose_with:
    - CORE-008   # su Traceability narró desviación ad-hoc; §4.2 la regulariza hacia adelante
    - futura auditoría reading-budget completa
  systemic_invariants:
    - "La ceremonia del ciclo es función de (señales §4.1 × naturaleza de proofs × superficie), no del tamaño ni del tipo de archivo."
  composition_checks:
    - "A.SPEC candidata trivial de prosa con mode: mechanical integra sin jueces completos y TRACE mínimo PASS."
    - "Candidata de 1 línea tocando kernel/auth con mode: mechanical declarado = inválida por señal hard (contraguardia legible en §4.2)."
    - "Toda A.SPEC del ciclo completo corre igual que hoy (retro-compatibilidad por defecto)."
```

## Structural Constraints

```yaml
structural_constraints:
  primary_rule: >-
    norma compacta hospedada junto a su prima §4.1; rescate declarado si el
    presupuesto se cruza
  entrypoints_must_stay_thin: true
  review_threshold_lines: 400
  extraction_threshold_lines: 600
  preferred_new_logic_locations:
    - ADD/SPECIFICATION.md §4.2
    - ADD/task-tools/README.md
```

## Traceability

- Requirement: decisión owner sesión 2026-08-27 — "no siempre vale matar moscas
  a cañonazos"; contraejemplo: 2 líneas core ≠ 100 líneas manifiesto; el riesgo
  vive en contenido×superficie, no en tamaño ni tipo de archivo.
- owner: Owner del canon ADD (rol)
- approver: Approver repo padre Systutor-oss (rol, presente en sesión; aprobó
  el concepto antes de esta escritura)
- Commit: f997a05 (submodule ADD: §4.2 + fila §1 + README modes) + c667909
  (bump gitlink padre, incluye CORE-009 y nota de presupuesto en CORE-007).
- Deployment: canon ADD vía submodule+bump.

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
