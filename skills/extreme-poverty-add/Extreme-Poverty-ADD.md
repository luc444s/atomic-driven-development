# Extreme Poverty ADD

## Purpose

Orquestador dentro del orquestador: colapsa el ciclo ADD completo
(`DEFINE → BOUND → CONTRACT → IMPLEMENT → VERIFY → INTEGRATE`) en el hilo
principal, presupuestando toolcalls al mínimo absoluto. La ÚNICA toolcall
Task permitida es GENERATOR (`ADD/task-tools/GENERATOR.md`).

> Una A.SPEC = un ciclo = 0 o 1 toolcall.

## Use When

- la A.SPEC es `low` o `medium` y se busca máximo ahorro de contexto/toolcalls
- el approver acepta el camino corto para cambios no-core
- una A.SPEC no requiere más que 0–1 Task tool (solo GENERATOR)

## Do Not Use When

- la A.SPEC es `high`, core, compuesta, o requiere composición/validación amplia
- el approver pide explícitamente ciclo completo (su mención prevalece)

## Core Law

El hilo principal hace TODO el ciclo; la única delegación externa es
GENERATOR para IMPLEMENT. Los demás task-tools (SPEC-REVIEWER, VERIFIER,
TRACE) NO se lanzan como subagentes: sus funciones se absorben en el hilo
principal con proofs mecánicas. Atomizer vive como skill, no como task tool.

COMPOSER no es una task tool ni una función "absorbida" ligera: el
**compose-gate es una acción de primer plano** del hilo principal. Cuando la
A.SPEC es de integración (§10.1), el hilo principal EJECUTA SIEMPRE los
`composition_checks` en su orden declarado, registra resultados, valida
`composition.owner` y las `systemic_invariants`, y exige el presence-check del
approver antes de liberar. No se dispara ningún subagente.

## Presupuesto de toolcalls

| Ciclo completo | Toolcalls Task |
|----------------|----------------|
| Hay implementación delegable (código/schema) | 1 (GENERATOR) |
| Solo docs / config / proofs mecánicas | 0 |

Se declara `toolcalls: 0|1` en el encabezado de la A.SPEC junto a `mode:`.

## Operating procedure

1. **DEFINE + BOUND + CONTRACT**: el hilo principal escribe la A.SPEC completa
   siguiendo `ADD/ASPEC-TEMPLATE.md`. Chequeo manual de atomicidad, scope vs
   out-of-scope, contract falsable, invariantes evaluables, risk honesto
   (§4.1) y owner/approver (§10.2) — contra la plantilla, sin subagente.
2. **IMPLEMENT**: si hay implementación delegable, lanzar la ÚNICA toolcall
   Task con el contenido de `ADD/task-tools/GENERATOR.md` como prompt y la
   A.SPEC como input. Si solo hay docs/config/verificación mecánica, pasar
   directo a VERIFY.
3. **VERIFY**: el hilo principal ejecuta los comandos deterministas de
   `VERIFICATION` (grep/wc/diff/tsc/pytest/ruff o equivalentes) y registra
   resultados. **Verificación dirigida**: correr solo los tests/checks que
   tocan la `change_surface`; registrar la proof y reusarla; no re-correr
   suites ya verdes en el mismo SHA. **Recorte de output**: `tail -N`, `-q`,
   redirigir a archivo y leer solo el resumen; el ruido no entra al contexto.
   Con señales hard §4.1, elevar rigor propio: invariante con proof explícita
   ejecutada, nunca asumida.
4. **COMPOSE (acción de primer plano, si la A.SPEC es de integración)**: el
   agente principal actúa como COMPOSER cargando la skill
   `ADD/skills/composer-gate-add/Composer-Gate-ADD.md`: recorre los
   `composition_checks` en su orden declarado, ejecuta cada uno y registra
   resultado; valida `composition.owner` y las `systemic_invariants`; exige el
   presence-check del approver. Sin esto no se libera el release (§10.1/§10.2).
   Esta acción NO consume toolcall.
5. **INTEGRATE**: TRACE minimal en hilo principal (sha_anchor + surface check)
   y commit trazable que referencia el ID de la A.SPEC.

## Riesgo alto (§4.1)

`high` y cambios core/composed no usan extreme poverty como camino normal.
Ahí la ceremonia completa y las task tools necesarias se activan para sostener
las garantías obligatorias (approver humano en `high`, proofs ejecutadas,
gates). **Ceremonia ≠ subagent calls**: el modo cambia la ejecución, no las
garantías. Compensación obligatoria del hilo principal cuando extreme poverty
sí aplica:

- invariantes evaluables con proof explícita (nunca "debería estar cubierto")
- verificación redundante si la señal lo amerita (auth/stock/dinero/lg_*/migración)
- ROLLBACK honesto según §9 (compensación/contención/no-repetición/auditoría)
- TRACE minimal ineludible antes de integrar

## Rules

1. Máximo 1 toolcall Task por ciclo; solo GENERATOR. El compose-gate (acción
   de COMPOSER) no consume toolcall: es acción de primer plano.
2. No lanzar SPEC-REVIEWER, VERIFIER, TRACE ni COMPOSER como
   subagentes. COMPOSER se ejecuta como acción de primer plano del hilo
   principal (nunca como task tool automática ni como subagente). Atomizer se
   usa como skill de primer plano cuando corresponde.
3. La calidad del contrato se garantiza en el hilo principal contra la
   plantilla y el canon; un defecto detectado se corrige en la propia A.SPEC
   antes de IMPLEMENT (equivalente a resolver un REVISE mecánico).
4. Ninguna señal de trigger de SPEC-REVIEWER abre un subagente: se resuelve en
   el hilo principal o se escala al approver.
5. La A.SPEC declara `mode: extreme-poverty` y `toolcalls: N` en su encabezado.
6. No opportunistic refactoring; un hallazgo = nueva A.SPEC.

## Completion Checklist

- [ ] A.SPEC con `mode: extreme-poverty` y `toolcalls:` en el encabezado
- [ ] ≤1 toolcall Task ejecutada (solo GENERATOR)
- [ ] VERIFICATION ejecutada con resultados registrados en el hilo principal
- [ ] invariantes con proof explícita (rigor elevado si señal hard)
- [ ] TRACE minimal (sha_anchor + surface) hecho en el hilo principal
- [ ] compose-gate ejecutado como acción de primer plano (owner + checks en orden + presence-check) si la A.SPEC es de integración
- [ ] commit trazable al ID de la A.SPEC
- [ ] sin toolcalls de SPEC-REVIEWER/VERIFIER/TRACE/COMPOSER
