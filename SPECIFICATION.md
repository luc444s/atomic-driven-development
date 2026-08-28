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
| risk (§4.1)  | ¿Qué nivel de riesgo declara y qué ceremonia exige?      |
| WHY          | ¿Qué problema concreto existe?                           |
| WHAT         | ¿Qué comportamiento observable cambia?                   |
| SCOPE        | ¿Qué entra?                                              |
| OUT OF SCOPE | ¿Qué explícitamente NO entra?                            |
| CONTRACT     | ¿Qué debe cumplirse?                                     |
| INVARIANTS   | ¿Qué comportamiento existente no puede romperse?         |
| VERIFICATION | ¿Cómo demostramos que funciona?                          |
| ROLLBACK     | ¿Cómo deshacemos el cambio?                              |
| Change Surface (§5) | ¿Qué superficie puede tocar y cuál queda prohibida? |
| Blast Radius (§6) | ¿Qué comportamiento podría verse afectado?           |
| Composition (§10.1) | ¿De qué capability mayor depende y con qué checks? |
| Structural Constraints (§12) | ¿Qué reglas estructurales respeta?        |
| Traceability (§10.2) | ¿Quién es owner/approver y cómo se trazará?       |
| DoD (§8)     | ¿Qué checklist debe quedar verde al cerrar?              |
| Modo (§4.2)  | ¿Qué ceremonia de ciclo le corresponde? (mechanical /    |
|              | judges-lite / completo por defecto)                      |

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

### 4.1 Risk-tiering: ceremonia proporcional al riesgo

El ciclo ADD declara un nivel de riesgo por A.SPEC; la ceremonia mínima
obligatoria es proporcional a ese nivel.

| Nivel | Cuándo (señales del A.SPEC) | Ceremonia mínima |
|-------|------------------------------|------------------|
| `low` | Reversible; sin dinero, stock, auth/seguridad, `lg_*` ni migraciones destructivas; blast radius acotado a la feature | SPECCER → GENERATOR → VERIFIER → TRACE. SPEC-REVIEWER opcional |
| `normal` | Default por defecto | Ciclo estándar; SPEC-REVIEWER regido por su Trigger contract (condicional) |
| `high` | Irreversible (§9), dinero, stock físico, auth/seguridad, migración destructiva, blast radius amplio | SPEC-REVIEWER SIEMPRE (incondicional), aprobación humana (`approver`), VERIFIER y TRACE obligatorios |

Derivación del nivel — solo señales del A.SPEC, sin inferencia externa:

- ROLLBACK sin reversión física posible (§9) → `high`.
- Scope/invariantes tocan `stock`, `finanzas`, `auth`, `tenancy`,
  `seguridad`, `lg_*` → `high`.
- Migración destructiva (`drop`) o reescritura de datos existentes → `high`.
- Blast radius con `must_not_affect` amplio o superficies críticas → `high`.
- Fuera de eso → `normal`; trivias internas reversibles sin señales → `low`.

Honestidad: un nivel declarado **menor** al sugerido por las señales es
subvaloración → SPEC-REVIEWER emite `REVISE`. Un nivel conservador mayor
no llama a `REVISE`.

**Matiz al Trigger contract de SPEC-REVIEWER:** para `high`, SPEC-REVIEWER
corre siempre (no condicional); para `low/normal` mantiene su trigger
condicional. La semántica de veredictos (REVISE/SPLIT/REJECT) no cambia.

Un `high` con ROLLBACK irreversible exige compensación/contención (§9) y
`approver` humano documentado en el A.SPEC; no se integra sin esa aprobación.

### 4.2 Verificación proporcional: modos de ejecución del ciclo

La ceremonia es función de (señales §4.1 × naturaleza de las proofs ×
superficie), **no del tamaño ni del tipo de archivo**. Dos líneas en código
transaccional pueden exigir jueces; cien líneas de prosa o de tema verificables
con build no ganan nada con contexto limpio. El host declara el modo en el
encabezado de la A.SPEC (`mode:`) ANTES de IMPLEMENT; lo que cambia por modo es
QUIÉN/QUÉ ejecuta cada fase, nunca qué debe probarse (la Definition of Done es
idéntica en todos los modos).

#### Modo A — Vía mecánica (main-thread, sin jueces)

Aplica cuando TODAS estas condiciones son verdaderas y quedan declaradas
explícitamente en la A.SPEC:

1. `risk: low` derivado honestamente per §4.1 (reversible, sin señales).
2. Todas las cláusulas de VERIFICATION son comandos deterministas ejecutables
   localmente (grep/wc/diff-stat/tsc/pytest/ruff o equivalentes) con resultado
   binario.
3. Ninguna cláusula requiere juicio semántico ("¿esta prosa es coherente?",
   "¿esta UX es correcta?", "¿este dominio está bien modelado?").
4. Superficie ≤ 3 archivos modificados y blast radius acotado con invariants
   demostrables por diff directo.
5. La A.SPEC declara `mode: mechanical` y lista las condiciones cumplidas
   (1–4) una a una [o invoca una exención automática].

Exenciones automáticas del Modo A (sin necesidad de listar condiciones):

- **Presentación pura** (themes, tokens, colores, estilos, copy, labels,
  layout): aunque la superficie exceda 3 archivos. Proof requerida: build
  (tsc) + diff visual; cero task tools; TRACE opcional — sin migraciones ni
  contratos que anclar, normalmente NO aporta.
- **Frontend consumidor** (comportamiento observable de UI que consume
  endpoints ya probados por tests backend): la verdad dura ya fue verificada
  atrás; aquí basta build + smoke. Máximo TRACE; jueces full sobran.

Regla **backend-decide**: cuando una A.SPEC toca backend y frontend juntos,
la ceremonia la fija el lado backend (donde vive la verdad dura: dominio,
persistencia, transacciones); el frontend hereda el trato y nunca lo agrava.
El trabajo pesado se verifica donde el riesgo vive; la presentación no
re-ceremoniza lo ya probado.

Bajo modo A: DEFINE+IMPLEMENT+VERIFY corren en hilo principal; los jueces vía
Task son OPCIONALES (el host puede lanzarlos si duda); TRACE minimal
(sha_anchor + surface check) sigue OBLIGATORIO para integrar cuando haya
contratos/migraciones que anclar. La desviación no se narra: queda declarada
por el propio `mode:`.

#### Modo B — Jueces-lite

Aplica cuando hay juicio genuino pero el blast radius no toca runtime/producto
(docs/canon/prosa): SPECCER + SPEC-REVIEWER sí corren (la calidad del contrato
importa); GENERATOR corre solo si superficie > 3 archivos o parche no-trivial;
VERIFIER full NO corre — verificación mecánica de proofs + inspección visual
del diff documentada como evidence sustitutiva; TRACE mínimo obligatorio.

Modo C (retro-compatibilidad): ausencia de `mode:` = ciclo completo como
siempre.

#### Modo D — Pobreza extrema (extreme-poverty)

Modo formal del canon (integración CORE-012, decisión approver 2026-08-28).
Colapsa la ceremonia en el hilo principal con presupuesto mínimo de agentes:

- **Ejecución**: ciclo completo (DEFINE → BOUND → CONTRACT → VERIFY →
  INTEGRATE) en el hilo principal con proofs mecánicas.
- **Presupuesto de Task calls**: 0–1 por ciclo; la ÚNICA toolcall permitida es
  GENERATOR (IMPLEMENT). SPECCER, SPEC-REVIEWER, VERIFIER, ATOMIZER y TRACE
  NO se lanzan como subagentes: sus funciones se absorben en el hilo principal
  (rigor contra la plantilla y el canon).
- **SPEC-REVIEWER nunca** como subagente (ni `risk: high`): sus señales se
  resuelven en el hilo principal (REVISE mecánico) o se escalan al approver.
- **COMPOSER no es task tool**: el compose-gate es **acción de primer plano**
  del hilo principal (skill `composer-gate-add`) para A.SPEC de integración;
  no consume toolcall.
- **Mantiene TODAS las checks/proofs**: la DoD es idéntica a los demás modos;
  ningún proof o gate exigido por el risk se omite. `high` sigue exigiendo
  `approver:` humano documentado y no se integra sin esa aprobación.
- La A.SPEC declara `mode: extreme-poverty` y `toolcalls: 0|1`.
- Aplica incluso con señales hard §4.1 (garantías completas obligatorias, ver
  contra-guardias), salvo pedido explícito del approver de ciclo full.

#### Contra-guardias (aplican a Modo A, B y D)

- Señal hard §4.1 impone **garantías completas obligatorias**: el modo de
  ejecución puede ser `full` o `extreme-poverty`, pero NINGUNA proof ni gate
  exigido por el riesgo puede omitirse (approver humano en `high`, proofs de
  invariantes ejecutadas, TRACE minimal, compose-gate cuando aplique).
  **Ceremonia ≠ subagent calls**: conservar las garantías no exige lanzar 5
  subagentes; el modo solo decide QUIÉN/QUÉ ejecuta, nunca qué se prueba.
- Un modo que elimine una garantía exigida por su risk (p.ej. `high` sin
  `approver:` humano, o una proof declarada y no ejecutada) = subvaloración →
  REVISE retroactivo del cambio integrado.
- Si tras integrar un defecto aparece que el ciclo completo habría atrapado,
  próximas A.SPECs del mismo tema vuelven al ciclo completo; reincidencia
  obliga a SPEC-REVIEWER retroactivo.
- Auto-declaración falsa de condiciones = subvaloración → REVISE retroactivo
  del cambio integrado.
- El approver puede exigir el ciclo completo en cualquier momento, sin
  justificación; su mención en Traceability cierra la discusión.

Nota estructural del canon: §12.2 aplica sus umbrales como HEURÍSTICA de
cohesión también a este documento. Un monolito coherente que hace bien una
única función normativa puede excederlos: el trigger real de división es que
el documento ya no mantenga una sola razón de cambio, no una cifra.

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

Convención normativa: el `.md` de la propia A.SPEC entra en su propia change_surface.allowed cuando su contrato viaja en el mismo commit. El check
de superficie del executor TRACE (check 2) evalúa esa presencia bajo esta
misma regla.

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

Contraste obligatorio: la cobertura de proof NO termina en coincidencia nominal
de nombres. El verifier MUST contrastar cada proof nombrada contra el artefacto
real (leer el test declarado, ejecutar el comando registrado); una proof
inflada o no corroborada por su artefacto no cierra `PASS` → veredicto `GAP`.

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

### 9.1 Reversibilidad probada

La reversibilidad de un cambio de schema NO es una promesa: es una prueba.

Si el `ROLLBACK` de la A.SPEC es por migración/downgrade físico (reversión
reversible de schema), el `VERIFICATION` DEBE incluir el comando que ejecuta el
downgrade (p.ej. `alembic downgrade <base>`) con su resultado registrado.

La mera presencia de `def downgrade(` en el tree **no alcanza**: TRACE
(CORE-002) verifica que existe; la **ejecución** la prueba el `VERIFICATION`.

Veredicto:

> Downgrade declarado sin ejecución probada → A.SPEC = GAP (reversibilidad no
> verificable), nunca `PASS`.

Esta norma aplica solo a A.SPECs nuevas o re-abiertas; las integradas quedan
grandfathered. No modifica §9 (irreversibles siguen por compensación/contención).

## 10. Correctitud local vs global

Una A.SPEC puede ser localmente correcta y, aun así, una secuencia de A.SPEC
ser globalmente incorrecta.

Corolario normativo:

- pasar contrato + invariantes de cada A.SPEC NO implica que la composición total pase
- una release o capability compuesta MAY requerir checks propios de integración, orden o sistema
- invariantes sistémicas y propiedades emergentes MUST validarse cuando el cambio dependa de varias A.SPEC

ADD verifica cambios pequeños de forma aislada, pero no asume que la suma de
cambios correctos sea automáticamente correcta.

### 10.1 Composition gate: A.SPEC de integración con dueño

Una release/capability compuesta exige una **A.SPEC de integración** que declara
`composition` con:

- `owner`: persona o rol humano responsable del conjunto.
- `composition_checks`: lista ordenada de comandos/procedimientos ejecutables.
- `systemic_invariants`: propiedades del conjunto, no de una hoja.

Sin A.SPEC de integración o sin `owner`, la integración del conjunto queda
`GAP`, nunca `PASS`.

El compose-gate (`compose-gate`) ejecuta los checks en orden y emite el
veredicto. Se materializa como **acción de primer plano del agente principal**
vía la skill `ADD/skills/composer-gate-add/Composer-Gate-ADD.md` (decisión
approver 2026-08-28: la task tool `COMPOSER` fue retirada; el gate nunca corre
como subagente automático):

- `PASS` — owner presente, todos los checks verdes, invariantes sistémicas
  evaluables.
- `FAIL` — un check declarado corrió y falló.
- `GAP` — owner ausente, check faltante/vago/inejecutable, invariante
  sistémica no evaluable, o el conjunto no tiene A.SPEC de integración.

**División de trabajo:** los `composition_checks` de una A.SPEC hoja los juzga
VERIFIER (`verify-composition`); los de la A.SPEC de integración (nivel set) los
juzga COMPOSER (`compose-gate`). No se corren dos jueces sobre el mismo check.

En hojas, quien **ejecuta y registra los resultados** de los composition_checks
es VERIFIER (`verify-composition`) durante VERIFY; esos resultados quedan como
proof de composición registrada junto al cierre.

Verificación del `owner`: COMPOSER valida **presencia** (ausencia → `GAP`); la
naturaleza humana del owner es norma de autoría. Para conjuntos con señales de
riesgo alto, la puerta humana la exige el `approver` de CORE-003 (§4.1).

### 10.2 Governance: owner/approver estructurales

Toda A.SPEC declara `owner` y `approver` (persona o rol) en Traceability.

- **owner**: responsable del cambio.
- **approver**: quien libera la integración (commit/release). El approver es el
  destino de escalación de `REVISE` (si no es mecánico), `SPLIT` y `REJECT`. El
  approver es el destino de escalación de los veredictos no mecánicos y
  reemplaza el vago "se devuelve al usuario".
- En conjuntos de nivel `high` (§4.1), el approver debe ser humano documentado
  y aprobar explícitamente.
- owner/approver se verifican por **presence-check** (presencia, no veracidad
  humana del rol).
- El agente no puede auto-asignarse como owner ni approver.
- Alcance mecánico: El presence-check NO verifica la prohibición de
  auto-asignación (no-self-assign); esa regla queda como norma de governance
  de autoría, fuera del chequeo mecánico.
- Aplica a A.SPECs nuevas o re-abiertas; las integradas quedan grandfathered.

Verificación: SPEC-REVIEWER flaggea ausencia → `REVISE`; VERIFIER → `GAP`
(nunca `PASS`).

Disambiguación de campos: `composition.owner` (nivel set, leído por COMPOSER)
y Traceability `owner`/`approver` (nivel spec, leídos por VERIFIER/
SPEC-REVIEWER) son dos campos distintos con el mismo espíritu; COMPOSER no lee
Traceability, y VERIFIER no lee composition.owner.

## 11. Estructura de documentos

```
ADD/
├── MANIFESTO.md
├── SPECIFICATION.md
├── QUICKSTART.md             # canon de cabecera para agentes activos
├── ASPEC-TEMPLATE.md
├── README.md
├── LICENSE
├── task-tools/          # jueces y ejecutores del ciclo
│   ├── README.md
│   ├── SPECCER.md
│   ├── SPEC-REVIEWER.md
│   ├── GENERATOR.md
│   ├── VERIFIER.md
│   ├── TRACE.md
│   └── ATOMIZER.md
└── skills/              # habilidades de aplicación (gitflow, CI, binding)
    └── <skill>/<Capabilidad>-ADD.md
```

Sincronización del monolito: SPECIFICATION.md se mantiene como documento único
mientras conserve una responsabilidad normativa coherente. Los umbrales de
§12.2 son heurísticos y no obligan por sí solos a dividirlo. Las tablas de
secciones obligatorias (§1) y este árbol de estructura (§11) se sincronizan en
TODA enmienda futura al canon. El split del canon en artículos es decisión
futura del owner, reabierta solo ante nueva ronda CORE: explícitamente out of
scope aquí.

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

Quién juzga: ATOMIZER es el **juez estructural ejecutor** de este trigger al
cruzar umbrales (lee el canon fresco en cada corrida; orden de juicio
cohesión → acoplamiento → navegabilidad → tamaño, con red flags propias).
SPEC-REVIEWER mantiene su chequeo del plan pre-implementación (dimensión 8,
sin cambio).

### 12.5 Falla estructural

Una A.SPEC falla aunque el comportamiento nuevo funcione si:

- mezcla varias responsabilidades no relacionadas en un mismo archivo
- convierte un entrypoint en un god-file
- aumenta acoplamiento evitable entre rutas, servicios y acceso a datos
- deja el archivo con múltiples razones principales de cambio

Cruce del trigger §12.4 sin invocación de ATOMIZER y sin A.SPEC estructural
pareada abierta se emite como `GAP` estructural por VERIFIER sobre hechos del
árbol (conteo de líneas / motivos de cambio), nunca `PASS`.

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

Fuente espejada: las reglas de discovery de checks (`commit→test`,
`commit→migración`) viven SOLO en `ADD/task-tools/TRACE.md`, fuente espejada
de este canon; toda enmienda futura a esas reglas MUST sincronizar canon↔tool
en el mismo cambio.

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
