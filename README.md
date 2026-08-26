# ADD — Atomic Development Discipline

> **Atomicity Applies to Change, not Ambition.**
>
> ADD no limita el tamaño del sistema. ADD limita el tamaño de cada cambio
> realizado al sistema.

ADD es una disciplina de desarrollo de software en la que cada cambio se
diseña, implementa y valida como una **unidad mínima, independiente, trazable
y reversible** — sin limitar la ambición o escala del sistema.

No hacemos pequeño el producto. Hacemos pequeño el cambio.

## ¿Por qué ADD?

Los sistemas grandes son difíciles de cambiar con seguridad, sobre todo
cuando participan múltiples equipos o agentes de IA. ADD organiza cada cambio
como una **A.SPEC** (Atomic Specification): un contrato de cambio que delimita
alcance, contrato, invariantes y verificación **antes** de tocar el código.

| Proyecto | Unidad de trabajo |
|----------|-------------------|
| TDD      | Test              |
| SDD      | Especificación    |
| **ADD**  | **A.SPEC**        |

## Contenido

```
ADD/
├── MANIFESTO.md              → Principios y valores de ADD (AAA) — CANÓNICO
├── SPECIFICATION.md          → Definición normativa de cumplir ADD — CANÓNICO
├── ASPEC-TEMPLATE.md         → Plantilla canónica de una A.SPEC
├── skills/                   → Habilidades de aplicación
│   ├── verify-binding-add/   → Binding explícito de comandos/proofs por proyecto
│   ├── ci-wrapper-add/       → Wrapper fino para ejecutar ADD en CI
│   ├── gitflow-lite-add/      → GitFlow liviano: main + add/* (1 A.SPEC = 1 commit)
│   └── gitflow-full-add/      → GitFlow estricto: main + develop + add/* + release/* + hotfix/*
└── task-tools/               → Prompts auto-suficientes para subagent (contexto limpio)
    ├── SPECCER.md            → DEFINE: petición suelta → A.SPEC honesta o split
    ├── SPEC-REVIEWER.md      → calidad de A.SPEC escrito (pre-implementación)
    ├── GENERATOR.md          → BUILD: A.SPEC finalizada → código en change_surface
    ├── VERIFIER.md            → PROVE: contrato declarado vs prueba explícita
    ├── ATOMIZER.md           → cohesión de archivos Python (split)
    └── README.md             → índice + protocolo de lanzamiento vía Task
```

> **MANIFESTO es canónico.** Este README es un resumen de entrada; ante
> contradicción, gana MANIFESTO/SPECIFICATION.

## Task Tools (ejecución con contexto limpio)

Los pasos del ciclo ADD se operacionalizan como task tools: subagents lanzados
con `Task` (`subagent_type=general`) y contexto fresco, para juzgar sin ruido
del hilo principal.

| Paso ADD     | Task tool            | Rol                                        |
|-------------|----------------------|--------------------------------------------|
| DEFINE       | `task-tools/SPECCER.md`  | petición suelta → A.SPEC honesta o split       |
| (quality)    | `task-tools/SPEC-REVIEWER.md`| A.SPEC escrito → calidad pre-implementación    |
| IMPLEMENT    | `task-tools/GENERATOR.md`| A.SPEC finalizada → código en change_surface    |
| VERIFY       | `task-tools/VERIFIER.md`  | contrato declarado vs prueba explícita         |
| (estructural)| `task-tools/ATOMIZER.md` | cohesión de archivos Python (split)            |

Los jueces del ciclo (SPECCER, SPEC-REVIEWER, GENERATOR, VERIFIER, ATOMIZER)
viven en `task-tools/` (fuente única de verdad, contexto limpio vía `Task`).

## Principio central: AAA

**Atomicity Applies to Change, not Ambition.**

Un ERP gigantesco se construye perfectamente: la arquitectura es enorme, los
cambios siguen siendo pequeños.

```
ERP
 │
 ├── Logistics    → 80 A.SPEC
 ├── Commerce     → 120 A.SPEC
 └── Hosting      → 40 A.SPEC
```

## El ciclo ADD

```
DEFINE → BOUND → CONTRACT → IMPLEMENT → VERIFY → INTEGRATE
```

1. **DEFINE** — describe una sola modificación observable.
2. **BOUND** — establece qué puede y qué no puede tocar.
3. **CONTRACT** — define comportamiento esperado e invariantes.
4. **IMPLEMENT** — realiza únicamente lo necesario (sin *opportunistic
   refactoring*).
5. **VERIFY** — comprueba contrato + invariantes.
6. **INTEGRATE** — commit/deployment asociado a la A.SPEC.

## Una A.SPEC responde obligatoriamente

| Sección      | Pregunta                                |
|--------------|-----------------------------------------|
| WHY          | ¿Qué problema concreto existe?          |
| WHAT         | ¿Qué comportamiento observable cambia?  |
| SCOPE        | ¿Qué entra?                             |
| OUT OF SCOPE | ¿Qué explícitamente NO entra?           |
| CONTRACT     | ¿Qué debe cumplirse?                    |
| INVARIANTS   | ¿Qué comportamiento no puede romperse?  |
| VERIFICATION | ¿Cómo demostramos que funciona?         |
| ROLLBACK     | ¿Cómo deshacemos el cambio?             |

Una SPEC no es documentación: es un **contrato de cambio**.

## Atomicidad: una sola transición observable

Atómico **no** significa "pocas líneas". Una A.SPEC es atómica cuando
representa una **sola transición observable** del sistema.

Contraejemplo (NO atómico):

```
HOST-0001 "Implementar administración de WordPress"
  incluye: discovery, restart, logs, backup, creación, SSL
```

Correcto:

```
HOST-0001 → Discover existing WordPress
HOST-0002 → Assign discovered site to tenant
HOST-0003 → Restart site
...
HOST-0009 → Provision SSL
```

## Invariantes y verificación

Si cualquier invariante deja de cumplirse → **A.SPEC = FAILED**, aunque la
funcionalidad nueva aparentemente funcione.

```
invariants:
  - Existing Docker containers MUST NOT be modified.
  - Discovery MUST be read-only.
  - Tenant isolation MUST remain enforced.
```

## ADD y agentes de IA

Un humano entrega una A.SPEC y un agente recibe únicamente:

1. SPEC
2. Contexto relevante del repositorio
3. Change surface permitida
4. Invariantes
5. Comandos de verificación

El agente ejecuta `inspect → implement → test → verify diff → report`. No
necesita entender todo el sistema para modificarlo con seguridad.

## Ley estructural

> Un archivo debe preservar una superficie de responsabilidad coherente y una
> razón principal de cambio.

El tamaño es una señal heurística, no la regla primaria: primero se evalúa
cohesión, luego acoplamiento, recién después tamaño.

## Licencia

[MIT](LICENSE)
