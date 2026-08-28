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
│   ├── atomizer-add/         → Split estructural de Python como acción de primer plano
│   ├── extreme-poverty-add/  → Orquestador anidado: 1 toolcall por ciclo (solo GENERATOR)
│   ├── composer-gate-add/    → Compose-gate como acción de primer plano (el agente es COMPOSER)
│   ├── verify-binding-add/   → Binding explícito de comandos/proofs por proyecto
│   ├── ci-wrapper-add/       → Wrapper fino para ejecutar ADD en CI
│   ├── gitflow-lite-add/      → GitFlow liviano: main + add/* (1 A.SPEC = 1 commit)
│   └── gitflow-full-add/      → GitFlow estricto: main + develop + add/* + release/* + hotfix/*
└── task-tools/               → Prompts auto-suficientes para subagent (contexto limpio)
                                 SPEC-REVIEWER lee SPECIFICATION como ley (canon completo)
    ├── SPEC-REVIEWER.md      → calidad de A.SPEC escrito (pre-implementación)
    ├── GENERATOR.md          → BUILD: A.SPEC finalizada → código en change_surface
    ├── VERIFIER.md            → PROVE: contrato declarado vs prueba explícita
    ├── TRACE.md              → trazabilidad vs hechos del repo (ancla SHA)
    └── README.md             → índice + protocolo de lanzamiento vía Task
```

> **MANIFESTO/SPECIFICATION son canónicos.** Este README es un resumen de
> entrada; ante contradicción, gana MANIFESTO/SPECIFICATION.

## Task Tools (ejecución con contexto limpio)

Los pasos del ciclo ADD se operacionalizan como task tools: subagents lanzados
con `Task` (`subagent_type=general`) y contexto fresco, para juzgar sin ruido
del hilo principal.

### Presupuesto de lectura

Cada task tool es **autocontenido**: sus checks y veredictos viven completos en
su propio cuerpo, y solo lee su input de juicio (`ASPEC-TEMPLATE.md` adicional
    en la plantilla, formato de salida). **SPEC-REVIEWER** — el juez cuyo objeto de
juicio es la norma misma — lee `SPECIFICATION.md` como ley por defecto y el
canon completo (MANIFESTO + SPECIFICATION) solo si la A.SPEC es `risk: high`
o hay duda de norma; además solo corre condicionalmente (Trigger contract +
§4.1/§4.2).

### Modos del ciclo (SPECIFICATION §4.2)

La ceremonia se declara con `mode:` antes de IMPLEMENT. En la práctica:

- `low` y `medium` usan `extreme-poverty` como camino normal.
- `high` y cambios core/compuestos usan el ciclo completo y las task tools
  necesarias.

| mode | Quién ejecuta | Cuándo |
|------|---------------|--------|
| `mechanical` | hilo principal, proofs deterministas (grep/wc/build/diff) | trivial reversible ≤3 archivos; presentación pura exenta |
| `extreme-poverty` | hilo principal, 0–1 Task (solo GENERATOR); garantías completas | default para `low`/`medium`, y para cambios no-core |
| `full` | ciclo estándar con task tools | `high`, core, composición, o pedido explícito del approver |

Reglas canónicas: la ceremonia es función de (señales × naturaleza de las
proofs × superficie), **no del tamaño ni del tipo de archivo**; las señales
hard §4.1 imponen **garantías completas obligatorias** (approver humano en
`high`, proofs ejecutadas, gates) — el modo puede ser `full` o
`extreme-poverty`, **ceremonia ≠ subagent calls**; **backend-decide** — el
frontend hereda el trato más liviano del backend y no re-ceremoniza lo ya
probado atrás.

| Paso ADD     | Task tool            | Rol                                        |
|-------------|----------------------|--------------------------------------------|
| (quality)    | `task-tools/SPEC-REVIEWER.md`| A.SPEC escrito → calidad pre-implementación    |
| IMPLEMENT    | `task-tools/GENERATOR.md`| A.SPEC finalizada → código en change_surface    |
| VERIFY       | `task-tools/VERIFIER.md`  | contrato declarado vs prueba explícita         |
| INTEGRATE    | `task-tools/TRACE.md`   | trazabilidad vs hechos del repo (ancla SHA)     |
| COMPOSE      | skill `composer-gate-add/` | gate de integración set/release (owner + checks) — acción de primer plano del agente principal |

Los jueces del ciclo (SPEC-REVIEWER, GENERATOR, VERIFIER, TRACE)
viven en `task-tools/` (contexto limpio vía `Task`). Atomizer vive como skill.

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
