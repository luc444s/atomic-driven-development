# Atomizer ADD

## Purpose

Skill para decidir y ejecutar un split estructural mínimo en archivos Python
cuando la cohesión lo exige. No es un task tool: se ejecuta en el hilo
principal como acción de primer plano.

## Use When

- un archivo Python mezcla responsabilidades claras
- la extracción mejora cohesión sin cambiar semántica ni contrato
- el cambio necesita separar entrypoint, orchestration, helpers o repo logic

## Do Not Use When

- el archivo ya tiene una única responsabilidad razonable
- el cambio requiere rediseñar comportamiento o contrato
- la separación solo agrega capas sin reducir complejidad real

## Core Law

Atomizer preserva semántica, contrato y proofs. Solo cambia la forma del código,
no la verdad del cambio. Si el split altera el contrato o la verificación, no
es Atomizer: es otra A.SPEC.

## Inputs

- path del archivo a evaluar
- A.SPEC o razón de cambio
- límites de superficie permitida, si existen

## Checks

1. Identificar responsabilidades reales y fronteras naturales.
2. Proponer el split mínimo que restaure cohesión.
3. Confirmar que se preservan rutas, contratos, permisos y verificación.
4. Mantener entrypoints delgados y lógica fuera del punto de entrada.

## Rules

1. No cambiar semántica observable.
2. No inventar nueva arquitectura.
3. No dividir por tamaño si no hay ruptura de cohesión.
4. No consumir Task tool: es acción de primer plano del agente principal.

## Completion Checklist

- [ ] responsabilidades separadas con claridad
- [ ] semántica preservada
- [ ] contrato y verificación intactos
- [ ] entrypoints delgados
- [ ] split mínimo aplicado
