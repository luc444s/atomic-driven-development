# ADD Quickstart — canon de cabecera para agentes activos

> **Canónico.** Los agentes activos leen SIEMPRE este quickstart + `AGENTS.md`.
> El canon normativo completo (`MANIFESTO.md` + `SPECIFICATION.md`) se lee solo
> bajo demanda: duda de norma, `risk: high`, o ceremonia completa pedida por el
> approver. Ante contradicción entre este quickstart y el canon completo, gana
> el canon completo.

## Qué es ADD

- Cada cambio = una **A.SPEC**: unidad mínima, independiente, trazable y
  reversible.
- **AAA — Atomicity Applies to Change, not Ambition**: el sistema puede ser
  enorme; el cambio es pequeño.

## El ciclo

```
DEFINE → BOUND → CONTRACT → IMPLEMENT → VERIFY → INTEGRATE
```

## A.SPEC (contrato de cambio, no documentación)

Secciones obligatorias: WHY, WHAT, SCOPE, OUT OF SCOPE, CONTRACT, INVARIANTS,
VERIFICATION, ROLLBACK, Change Surface, Blast Radius, Composition, Structural
Constraints, Traceability, Definition of Done. Plantilla: `ASPEC-TEMPLATE.md`.

Regla de delta: escribir solo lo que cambia; sección vacía se declara en una
línea (`ROLLBACK: revert`, `Composition: no aplica`). No re-explicar el canon.

## Atomicidad

- Una sola transición observable / verdad independiente y falsable que aparece
  **ahora**.
- No valen "preparar para luego", "dejar base lista", "habilitar fase". Si la
  promesa necesita futuras A.SPECs para ser honesta → no es atómica (`SPLIT`).

## Risk (§4.1)

- `low`: reversible, sin señales. `normal`: default. `high`: irreversible, o
  toca stock/finanzas/auth/tenancy/seguridad/`lg_*`, o migración destructiva,
  o blast radius amplio.
- `high` exige `approver:` humano documentado en Traceability; no se integra
  sin esa aprobación.
- Declarar un nivel menor al que sugieren las señales = subvaloración → REVISE.

## Change Surface vs Blast Radius

- **Surface**: qué código podemos tocar (`allowed`/`prohibited`).
- **Blast Radius**: qué comportamiento podría verse afectado.
- Regla §7.1: toda superficie en `blast_radius.must_not_affect` DEBE tener su
  invariante correlativo evaluable con proof en VERIFICATION.

## Verificación

- Proofs explícitas e inspeccionables (comando nombrado + resultado). Nunca
  "debería estar cubierto por CI".
- Downgrade por migración: se demuestra EJECUTÁNDOLO (§9.1), no por presence
  de `def downgrade`.
- **Verificación dirigida**: correr solo los tests/checks que tocan la
  `change_surface`; registrar la proof y reusarla; no re-correr suites ya
  verdes en el mismo SHA.

## Modo de ejecución: extreme poverty (modo formal §4.2, default del approver 2026-08-28)

- Todo el ciclo en el **hilo principal** con proofs mecánicas.
- **ÚNICA toolcall Task permitida: GENERATOR** (0-1 por ciclo). La A.SPEC
  declara `mode: extreme-poverty` y `toolcalls: 0|1` en su encabezado.
- SPECCER, SPEC-REVIEWER, VERIFIER, ATOMIZER, TRACE: funciones absorbidas en
  el hilo principal; NO se lanzan como subagentes.
- **SPEC-REVIEWER NUNCA** se ejecuta como subagente (ni `risk: high`): sus
  señales se resuelven como REVISE mecánico o se escalan al approver.
- **COMPOSER es una skill** (`skills/composer-gate-add/Composer-Gate-ADD.md`):
  el agente principal actúa como COMPOSER. El compose-gate es **acción de
  primer plano** SIEMPRE para A.SPEC de integración (owner → composition_checks
  en orden → systemic_invariants → presence-check del approver). No consume
  toolcall.
- Aplica SIEMPRE (incluso señales hard §4.1) salvo pedido explícito del
  approver de ciclo full. Regla clave: las señales hard imponen **garantías
  completas obligatorias** (approver humano en `high`, proofs ejecutadas,
  gates), no toolcalls — **ceremonia ≠ subagent calls**; extreme-poverty
  conserva todas las checks/proofs y solo cambia la ejecución (main thread,
  0–1 Task).

## Gobernanza (§10.2)

- Toda A.SPEC declara `owner` y `approver` en Traceability. Ausencia → GAP.
- El agente no puede auto-asignarse como owner/approver.
- El approver es el destino de REVISE no mecánico, SPLIT y REJECT.

## Ley estructural

- Cohesión primero: una responsabilidad y una razón de cambio por archivo.
- Entrypoints (`plugin.py`/`main.py`/`router.py`): delgados, wiring no lógica.
- Tamaño como heurística: >400 líneas revisar cohesión; >600 extraer.

## Definition of Done

Una A.SPEC cierra solo cuando: objective ✓ · scope ✓ · contract ✓ · invariants
✓ · verification ✓ · rollback honesto ✓ · composition checks (si aplica) ✓ ·
sin cambios no relacionados ✓ · estructura ✓ · trazabilidad (SHA anclado) ✓.
