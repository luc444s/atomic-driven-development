# ADR 0022 — Adopción de Monaco Editor como consola operativa

## Estado

Aceptado

## Contexto

El sistema está evolucionando hacia un modelo donde la operación puede ejecutarse no solo mediante UI tradicional (formularios, modales), sino también mediante una consola de comandos tipados con autocompletado.

Para soportar esta interacción, se requiere un componente que:

- permita entrada estructurada;
- soporte autocompletado contextual;
- habilite validación en tiempo real;
- permita una experiencia tipo IDE (no tipo textarea simple).

El uso de una pseudo-terminal basada en inputs simples no es suficiente para cumplir estos objetivos.

## Decisión

Se adopta **Monaco Editor** como componente oficial para la entrada de comandos del sistema.

### Rol dentro del sistema

Monaco no es un componente visual accesorio. Se define como:

**Un componente base del core para interacción estructurada del usuario con el sistema.**

### Naturaleza del componente

Monaco será utilizado como **editor estructurado para comandos del dominio**, no como editor de código genérico.

### Responsabilidad

El componente Monaco dentro del core será responsable de:

- Entrada de comandos del usuario
- Posicionamiento y control del cursor
- Integración con autocompletado
- Renderizado de tokens (keywords, entidades, valores)
- Soporte para validación visual en tiempo real

### No responsabilidades

Monaco no es responsable de lógica de negocio. No debe:

- ejecutar comandos;
- validar reglas del dominio;
- resolver entidades;
- tomar decisiones operativas.

### Relación con el sistema

Monaco se integra conceptualmente con:

- **Autocomplete Engine** — proveedor de sugerencias contextuales
- **Parser DSL** — intérprete del lenguaje de dominio
- **Command Handlers** — ejecutores de comandos interpretados

Pero no contiene esa lógica. El editor es solo la superficie de entrada.

### Modelo de interacción

El flujo esperado es:

1. Usuario escribe en Monaco
2. Sistema sugiere (autocomplete)
3. Usuario completa comando
4. Comando es interpretado fuera del editor (parser DSL)
5. Se ejecuta en backend (command handlers)

### Experiencia de usuario

El editor debe:

- priorizar velocidad de escritura;
- minimizar fricción cognitiva;
- guiar mediante autocompletado;
- evitar ambigüedad mediante sugerencias controladas.

### Estilo visual

Aunque puede adoptar estética de terminal (oscuro, fuente monoespaciada), se define que:

**La apariencia no define el comportamiento.**

La experiencia debe sentirse como **un IDE simplificado para operar el negocio**, no como una terminal real del sistema operativo.

## Invariantes

1. Monaco es la base para interacción avanzada del usuario.
2. No se permite usar inputs simples para flujos que requieran autocompletado estructurado.
3. Toda lógica de negocio permanece fuera del editor.
4. El editor nunca ejecuta directamente acciones del sistema.
5. La experiencia debe ser guiada, no libre.
6. El editor no debe aceptar lenguaje libre; toda entrada debe ser interpretable por el DSL definido. Esto protege contra "modo ChatGPT" — el usuario no puede escribir texto arbitrario sin estructura.
7. El editor debe soportar estados intermedios inválidos sin bloquear la interacción. El usuario puede tener comandos incompletos o sintácticamente incorrectos mientras escribe; el editor muestra feedback visual pero nunca impide seguir escribiendo.

### Extensibilidad

Los plugins **no modifican el editor directamente**. Extienden comportamiento exclusivamente mediante providers registrados:

- `CompletionProvider` — sugerencias contextuales
- `TokenProvider` — reglas de resaltado
- `ValidationProvider` — reglas de decoración visual

El editor expone una API de registro (`registerProvider`) que los plugins consumen en su inicialización. Ningún plugin importa, extiende o modifica el componente `ConsoleEditor`.

## Consecuencias

### Positivas

- Un punto único de entrada estructurada para operaciones rápidas, capaz de escalar hacia una consola completa del sistema.
- Separación clara entre superficie de entrada (editor) y lógica de dominio (parser, handlers).
- Cualquier plugin futuro (ventas, logística, agenda) puede consumir la misma consola sin reimplementar.
- Autocompletado contextual como primitiva del core, reutilizable por todos los plugins.
- Velocidad y precisión en entrada de datos operativos, evitando complejidad de formularios multi-paso.

### Negativas

- Monaco es un componente pesado (~5MB bundle, aunque se puede reducir con carga lazy y tree-shaking).
- Requiere curva de aprendizaje para los desarrolladores del equipo en APIs de Monaco (tokens, decorators, completion providers).
- La integración con autocompletado contextual desde múltiples plugins requiere un contrato claro de providers.

### Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Usar Monaco como editor genérico en lugar de consola guiada | alto | Wrapper `ConsoleEditor` con API restringida y modo guiado por defecto |
| Introducir lógica de negocio dentro del editor | alto | El editor expone solo `onCommand(cmd: string)`, sin conocimiento del dominio |
| Sobrecargar la UI con comportamiento innecesario | medio | Feature flags para capacidades (tokens, validación, autocomplete) activables por plugin |
| Perder enfoque en velocidad por exceso de features | medio | La consola arranca en modo mínimo; features se activan por demanda del plugin |
| Bundle size excesivo en carga inicial | medio | Lazy load de Monaco + workers; la consola se carga solo al entrar a plugins que la requieran |
| Complejidad de empaquetado con Vite | bajo | `@monaco-editor/react` maneja la carga de workers en Vite; configurar `vite.config.ts` |

## Arquitectura del componente

```
apps/web/src/shared/ui/console-editor/
├── ConsoleEditor.tsx          # Wrapper de Monaco con API restringida
├── ConsoleEditor.types.ts     # Tipos: CompletionProvider, TokenProvider, ConsoleConfig
├── ConsoleEditor.theme.ts     # Tema visual (oscuro, tokens coloreados)
├── ConsoleEditor.completion.ts # Integración base de autocompletado
├── ConsoleEditor.tokens.ts    # Proveedor base de tokenización
└── ConsoleEditor.validation.ts # Decoradores de validación visual
```

### API pública esperada

```ts
interface ConsoleEditorProps {
  /** Lenguaje del dominio (ej: "cotizacion", "logistica") */
  language: string;
  /** Proveedor de autocompletado contextual */
  completionProvider: CompletionProvider;
  /** Proveedor de tokens para resaltado */
  tokenProvider: TokenProvider;
  /** Handler de comando completo (se dispara al ejecutar).
   *  En esta iteración recibe texto crudo. Evolución prevista:
   *  comando estructurado (AST o DTO) cuando el parser DSL madure. */
  onExecute: (command: string) => void;
  /** Handler de cambio (validación en tiempo real) */
  onChange?: (value: string) => void;
  /** Configuración visual */
  config?: ConsoleConfig;
}
```

## Dependencias

- `@monaco-editor/react` — wrapper React para Monaco
- `monaco-editor` — editor base (cargado lazy)
- Vite — requiere configuración para workers de Monaco
- Plugin runtime — los plugins registran sus completion/token providers

## Referencias

- ADR 0004: Runtime de Plugins
- ADR 0009: Spec-Driven Development
- ADR 0012: CRM Plugin de Clientes
- Spec 0023S: Gestión Comercial (referencia a cotización como dominio futuro)
- Spec 0023XA: Condiciones Comerciales (referencia a presupuesto/cotización)
- Monaco Editor: https://microsoft.github.io/monaco-editor/
- `@monaco-editor/react`: https://github.com/suren-atoyan/monaco-react
