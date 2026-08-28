# ADD — Specification

Definición normativa de qué significa cumplir ADD.

## 1. A.SPEC

Una A.SPEC es la unidad canónica de cambio.
No es documentación: es un contrato de cambio.
Debe ser atómica, acotada, contractual, verificable y trazable.

## 2. Atomicidad

Una A.SPEC representa una sola transición observable del sistema.
Debe producir una verdad nueva, independiente y falsable ahora.
No valen promesas que dependan de futuras A.SPECs.
Si la promesa no es honesta al cerrar, no es atómica.

## 3. Ciclo

Ciclo: DEFINE → BOUND → CONTRACT → IMPLEMENT → VERIFY → INTEGRATE.
La estrategia de ejecución puede variar, pero no puede reducir las garantías ni la Definition of Done.

## 4. Risk (§4.1)

`low`: reversible, sin señales.
`normal`: default.
`high`: irreversible, o toca stock/finanzas/auth/tenancy/seguridad/lg_*, o migración destructiva, o blast radius amplio.
`high` exige `approver:` humano en Traceability.
Subvaluar riesgo es REVISE.

### 4.2 Ejecución

La ceremonia de ejecución es externa a la norma.
Puede variar por tooling o runner.
No puede reducir garantías, verificabilidad ni la Definition of Done.

## 5. Change Surface y Blast Radius

Change Surface: qué se puede tocar y qué está prohibido.
Blast Radius: qué comportamiento podría verse afectado.
Toda superficie en `must_not_affect` debe tener invariante correlativo verificable.
Toda exclusión debe ser comprobable por proof.

## 6. Contract

Toda A.SPEC debe declarar precondiciones y postcondiciones.
Debe indicar qué verdad nueva queda establecida.
Debe decir qué queda fuera de alcance.
Si no puede formularse como contrato, la A.SPEC está incompleta.

## 7. Invariants

Los invariantes protegen comportamiento existente que no puede romperse.
Si un invariante falla, la A.SPEC falla.
Cada invariante debe ser evaluable en VERIFICATION.
No se aceptan invariantes vagos ni no observables.

### 7.1 Completeness map

Toda superficie listada en `blast_radius.must_not_affect` debe tener un invariante correlativo y proof explícita.
Una superficie sin protección es GAP.

## 8. Verification

La verificación debe ser objetiva y ejecutable.
Debe incluir comandos, tests o checks concretos.
No vale delegar en CI sin proof explícita.
Si hay rollback físico o downgrade, debe ejecutarse y registrarse.
La verificación debe cubrir la surface declarada.

## 9. Rollback

Si el cambio es reversible, describir cómo revertirlo.
Si es irreversible, describir compensación, contención y auditoría.
Rollback por migración se demuestra ejecutándolo.
La ausencia de rollback honesto bloquea cierre.

### 9.1 Reversibility proof

Si el scope incluye migración o cambio de esquema y el rollback depende de downgrade físico, la proof debe incluir el comando ejecutado y su resultado.
La presencia de `def downgrade(` no sustituye la ejecución.

## 10. Composition

Si una A.SPEC depende de otras A.SPECs o participa en una capability compuesta, debe declarar sus dependencias y checks de composición.
La integración debe demostrar que las verdades individuales siguen siendo ciertas en conjunto.

### 10.1 Composition checks

Una A.SPEC hoja demuestra sus checks por VERIFICATION.
Una A.SPEC de integración demuestra que la composición completa preserva las verdades declaradas.

### 10.2 Governance

Toda A.SPEC debe declarar `owner` y `approver`.
`high` exige `approver:` humano.
Ausencia de owner/approver es GAP.

## 11. Traceability

La cadena debe poder seguirse:

`Requirement → A.SPEC → Code → Migration → Test → Commit → Deployment`

`Commit` debe llevar el SHA literal.
La trazabilidad conecta la A.SPEC con sus hechos verificables.

## 12. Structural Integrity

El cambio debe preservar cohesión y responsabilidades claras.
Los entrypoints deben limitarse a coordinación cuando exista una capa apropiada para la lógica.
Una A.SPEC no debe introducir cambios estructurales no necesarios para satisfacer su contrato.

## 13. Definition of Done

- Objective satisfied
- Scope respected
- Contract satisfied
- Independent falsable truth exists now
- Invariants preserved
- Verification passed
- Rollback / compensation is honest
- Composition checks passed when applicable
- No unrelated changes
- Structural integrity respected
- Traceability established
