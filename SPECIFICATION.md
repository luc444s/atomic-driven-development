# ADD — Specification

Definición normativa de qué significa cumplir ADD.

## 1. Unidad fundamental: A.SPEC

Una Atomic Specification (A.SPEC) es la unidad canónica de ADD.

Ejemplo:

```
A.SPEC HOST-0001
Docker WordPress Discovery
```

Una A.SPEC responde obligatoriamente:

| Sección      | Pregunta que responde                                    |
|--------------|----------------------------------------------------------|
| WHY          | ¿Qué problema concreto existe?                           |
| WHAT         | ¿Qué comportamiento observable cambia?                   |
| SCOPE        | ¿Qué entra?                                              |
| OUT OF SCOPE | ¿Qué explícitamente NO entra?                            |
| CONTRACT     | ¿Qué debe cumplirse?                                     |
| INVARIANTS   | ¿Qué comportamiento existente no puede romperse?         |
| VERIFICATION | ¿Cómo demostramos que funciona?                          |
| ROLLBACK     | ¿Cómo deshacemos el cambio?                              |

Una SPEC no es documentación: es un contrato de cambio.

## 2. Definición de atomicidad

"Atómico" **no** significa "pocas líneas de código".

Una modificación de 300 líneas puede representar un solo cambio conceptual,
mientras que una de 15 líneas puede mezclar tres comportamientos.

**Una A.SPEC es atómica cuando representa una sola transición observable
del sistema.**

Contraejemplo — NO atómica:

```
HOST-0001 "Implementar administración de WordPress"
  incluye: discovery, restart, logs, backup, creación, SSL
```

Correcto:

```
HOST-0001 → Discover existing WordPress
HOST-0002 → Assign discovered site to tenant
HOST-0003 → Restart site
HOST-0004 → Read container logs
HOST-0005 → Create database backup
HOST-0006 → Restore database backup
HOST-0007 → Provision WordPress
HOST-0008 → Attach domain
HOST-0009 → Provision SSL
```

Cada una produce un cambio observable.

### 2.1 Límite contra fragmentación artificial

ADD permite A.SPECs estructurales y A.SPECs con `ROLLBACK` por compensación,
pero eso NO autoriza dividir una misma promesa en fragmentos preparatorios.

Una A.SPEC solo cuenta como atómica si, al cerrarse, introduce una verdad
nueva, independiente y falsable en el sistema actual.

Puede ser:

- una transición observable nueva
- una propiedad estructural nueva
- una garantía operacional nueva

No basta con:

- "preparar para luego"
- "dejar base lista"
- "agregar plumbing"
- "habilitar fase siguiente"

si la misma promesa todavía depende de trabajo futuro para volverse verdadera.

Test normativo:

> Si la A.SPEC necesita futuras A.SPEC para que su promesa actual sea honesta,
> NO es atómica.

## 3. Las 5 propiedades de un Atomic Change

- **A — Atomic**: una responsabilidad observable.
- **B — Bounded**: scope y non-scope explícitos.
- **C — Contractual**: precondiciones, postcondiciones e invariantes.
- **D — Verifiable**: existe una forma objetiva de demostrar que funciona.
- **E — Traceable**: debe poder seguirse la cadena

```
Requirement → A.SPEC → Code → Migration → Test → Commit → Deployment
```

La trazabilidad es esencial para que agentes programen usando ADD.

## 4. El ciclo ADD

```
DEFINE → BOUND → CONTRACT → IMPLEMENT → VERIFY → INTEGRATE
```

- **DEFINE**: describe una sola modificación observable.
- **BOUND**: establece qué puede y qué no puede tocar.
- **CONTRACT**: define comportamiento esperado e invariantes.
- **IMPLEMENT**: realiza únicamente lo necesario.
- **VERIFY**: comprueba contrato + invariantes.
- **INTEGRATE**: commit/deployment asociado a la A.SPEC.

**Regla fuerte en IMPLEMENT: no opportunistic refactoring.**

Si mientras implementas encuentras otra mejora ("ya que estoy aquí podría
refactorizar..."), eso es una **nueva A.SPEC**.

## 5. Change Surface

Cada A.SPEC declara su Change Surface:

```yaml
change_surface:
  allowed:
    - plugins/hosting/backend/discovery.py
    - plugins/hosting/backend/models.py
    - tests/hosting/test_discovery.py
  prohibited:
    - kernel/auth/**
    - kernel/tenancy/**
    - plugins/logistics/**
```

La implementación declara de antemano qué superficie del sistema está
autorizada a modificar. Potentísimo para agentes de IA.

## 6. Blast Radius

Change Surface ≠ Blast Radius.

- **Change Surface**: qué código modificamos.
- **Blast Radius**: qué comportamiento podría verse afectado.

```yaml
blast_radius:
  direct:
    - hosting.docker.discovery
  indirect:
    - hosting.site.list
  must_not_affect:
    - auth
    - tenants
    - logistics
    - existing_containers
```

ADD obliga a pensar no solo "¿qué archivo cambio?" sino "¿qué podría
romper?".

## 7. Invariantes

Uno de los pilares más fuertes.

```yaml
invariants:
  - Existing Docker containers MUST NOT be modified.
  - Discovery MUST be read-only.
  - Containers MUST continue running if Systutor is unavailable.
  - Tenant isolation MUST remain enforced.
```

Si cualquier invariante deja de cumplirse:

> **A.SPEC = FAILED**

aunque la funcionalidad nueva aparentemente funcione.

### 7.1 Completitud normativa de invariantes

Los invariantes protegen el Blast Radius. Toda superficie declarada en
`blast_radius.must_not_affect` MUST tener un invariante explícito, evaluable y
con proof explícita en `VERIFICATION`. La superficie `blast_radius.indirect` se
informa como nota, no como puerta de verificación.

Una A.SPEC con `must_not_affect` cuyo invariante correlativo no exista o no sea
evaluable:

> **A.SPEC = FAILED / veredicto VERIFIER = GAP**

El verifier nunca puede emitir `PASS` con superficies `must_not_affect` sin
cubrir. El Blast Radius declara la intención; el invariante la hace verificable;
la proof la vuelve prueba. Vanidad sin solo intención no es una garantía.

Rule for new/re-opened A.SPECs only: surfaces new or re-opened are subject to
this norm. Already-integrated A.SPECs are grandfathered — when re-opened, a
`GAP` completeness note is informative, not an invalidation of prior work.

## 8. Definition of Done

Una A.SPEC solo puede cerrarse cuando:

- [x] Objective satisfied
- [x] Scope respected
- [x] Contract satisfied
- [x] Invariants preserved
- [x] Verification passed
- [x] No unrelated changes
- [x] Traceability established

Esto elimina el ambiguo "parece que ya funciona".

## 9. Rollback en transiciones irreversibles

ADD prefiere cambios reversibles, pero no exige que todo efecto del mundo pueda
deshacerse físicamente.

Hay A.SPEC válidas con efectos irreversibles:

- enviar un email
- cobrar un pago
- emitir una factura fiscal
- accionar hardware o sistemas externos

En estos casos, `ROLLBACK` NO significa "borrar lo ocurrido". Significa definir
cómo el sistema controla el daño y evita repetición incorrecta.

`ROLLBACK` debe tomar una o más de estas formas:

- **compensación**: refund, nota de crédito, email correctivo, evento opuesto
- **contención**: stop, safe-state, lock, aislamiento, operator handoff
- **no-repetición segura**: idempotencia, deduplicación, consumo único, replay guard
- **trazabilidad forense**: auditoría, correlation ID, registro inmutable de qué ocurrió

Una A.SPEC irreversible sigue siendo atómica solo si:

- la transición observable está claramente definida
- las precondiciones son estrictas antes de ejecutar efecto irreversible
- la verificación demuestra que ocurrió correctamente una sola vez
- existe compensación, contención o replay protection explícita
- invariantes siguen siendo evaluables aunque el efecto no pueda deshacerse

Ejemplo honesto:

```text
ROLLBACK:
- no aplica reversión física del email enviado
- compensación: enviar email correctivo
- no-repetición: idempotency key por evento
- auditoría: guardar message_id y correlation_id
```

Ejemplo deshonesto:

```text
ROLLBACK: deshacer envío de email
```

Si una A.SPEC irreversible no define control posterior al efecto, falla como
contrato ADD aunque la operación "funcione".

## 10. Correctitud local vs global

Una A.SPEC puede ser localmente correcta y, aun así, una secuencia de A.SPEC
ser globalmente incorrecta.

Corolario normativo:

- pasar contrato + invariantes de cada A.SPEC NO implica que la composición total pase
- una release o capability compuesta MAY requerir checks propios de integración, orden o sistema
- invariantes sistémicas y propiedades emergentes MUST validarse cuando el cambio dependa de varias A.SPEC

ADD verifica cambios pequeños de forma aislada, pero no asume que la suma de
cambios correctos sea automáticamente correcta.

## 11. Estructura de documentos

```
ADD/
├── MANIFESTO.md
├── SPECIFICATION.md
└── ASPEC-TEMPLATE.md
```

## 12. Ley estructural

Además de atomicidad observable, ADD exige coherencia estructural.

### 12.1 Regla primaria

Un archivo MUST preservar:

- una superficie de responsabilidad coherente
- una razón principal de cambio

La pregunta correcta no es "¿cuántas líneas tiene?" sino:

> "¿Este archivo sigue haciendo una sola cosa coherente?"

### 12.2 Tamaño como heurística

El tamaño del archivo NO es la regla primaria. Es una señal de alerta.

- `0-200` líneas: cómodo
- `200-400` líneas: tolerable
- `>400` líneas: revisar cohesión
- `>600` líneas: extracción fuertemente recomendada

Estas cifras no fallan una A.SPEC por sí mismas. Solo elevan exigencia de
justificación estructural.

### 12.3 Archivos de entrypoint

Archivos como `plugin.py`, `register.py`, `main.py`, `router.py` o equivalentes
MUST actuar principalmente como entrypoint o composition root.

Pueden:

- registrar routers
- cablear dependencias
- exponer entrypoints públicos

No deben convertirse en contenedores de toda la lógica del feature si esa
lógica puede vivir en módulos vecinos más cohesivos.

### 12.4 Trigger de extracción

Si una A.SPEC agrega una nueva responsabilidad observable a un archivo ya bajo
presión estructural (`>400` líneas o múltiples motivos de cambio), la
implementación MUST hacer una de estas dos cosas:

1. extraer la nueva responsabilidad a un módulo nuevo
2. abrir una A.SPEC estructural previa o pareada para separar el archivo

### 12.5 Falla estructural

Una A.SPEC falla aunque el comportamiento nuevo funcione si:

- mezcla varias responsabilidades no relacionadas en un mismo archivo
- convierte un entrypoint en un god-file
- aumenta acoplamiento evitable entre rutas, servicios y acceso a datos
- deja el archivo con múltiples razones principales de cambio

## 13. Commit y changelog

ADD exige trazabilidad, no burocracia innecesaria.

### 13.1 Commit obligatorio

Cada A.SPEC integrada MUST quedar trazable a un commit identificable.

Idealmente:

- un commit por A.SPEC
- o una secuencia corta de commits claramente atribuibles a esa A.SPEC

El mensaje de commit SHOULD referenciar el identificador de la A.SPEC cuando
sea posible.

### 13.2 Changelog no obligatorio por defecto

ADD NO exige changelog por cada commit.

Un changelog es opcional salvo que el proceso del proyecto o la release lo
requiera explícitamente.

### 13.3 Cuándo sí exigir changelog

Changelog SHOULD existir cuando:

- hay release pública
- hay cambios operativos o de despliegue relevantes
- múltiples equipos o agentes necesitan historial resumido
- el cambio afecta usuarios o integradores externos

### 13.4 Regla mínima

La regla mínima de ADD es:

- commit trazable: obligatorio
- changelog por commit: opcional
- changelog por release o hito: recomendado

### 13.5 Trazabilidad verificable por hechos del repo

La trazabilidad no es prosa: es verificable por hechos del repo, anclada en el
SHA del commit.

El campo `Traceability.Commit` de una A.SPEC MUST llenarse en INTEGRATE con el
SHA literal del commit (o el SHA inicial de la secuencia). Sin SHA → la
integración queda `GAP`.

El task tool `ADD/task-tools/TRACE.md` verifica la cadena contra hechos del
repo:

- A.SPEC→commit: el SHA existe en `git log` y el mensaje menciona el ID.
- commit→code: los paths del `--stat` quedan bajo `change_surface.allowed`,
  ninguno bajo `prohibited`.
- commit→test: los tests nombrados en VERIFICATION existen en el tree.
- commit→migración: las migraciones del SCOPE existen y tienen `downgrade(`.
- deployment: la migración está aplicada (o `GAP` informativo si el runtime
  no es expuesto).

Veredicto de TRACE:

> Sin hechos que respalden la cadena, la A.SPEC queda `GAP`, nunca `PASS`.

Los gitlinks de submódulos se aceptan: si la integración en el repo padre bumpa
un gitlink `G` y `allowed` tiene paths bajo `G/`, TRACE valida el diff dentro
del submódulo con el mismo SHA.

Opcional:

```
ADD/
├── examples/
│   ├── bugfix.aspec.md
│   ├── feature.aspec.md
│   ├── migration.aspec.md
│   └── agent-task.aspec.md
└── schemas/
    └── aspec.schema.json
```
