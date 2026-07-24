# ADR 0028 — Single Use Case, múltiples adaptadores

## Estado

Aceptado

## Contexto

Históricamente, los ERP tienen un problema recurrente: cuando un mismo caso de uso (ej: crear una cotización) se expone a través de múltiples interfaces (consola, formulario, API externa, AI agent), cada interfaz termina implementando su propia lógica de validación, construcción del draft y comunicación con el backend.

Esto produce:

- Divergencia funcional entre interfaces (la consola acepta algo que el formulario rechaza)
- Duplicación de lógica de negocio en el frontend
- Dificultad para agregar nuevas interfaces (cada una requiere reimplementar el caso de uso)

## Decisión

**Un caso de uso, múltiples adaptadores.**

### Definiciones

- **Caso de uso**: una operación de dominio completa y atómica (ej: `createQuote`, `prepareQuote`).
- **Adaptador**: una interfaz específica que consume el caso de uso (Consola, Formulario, API REST futura, AI agent).
- **Capa de dominio**: código que implementa el caso de uso, independiente de cualquier adaptador.

### Reglas

1. Todo caso de uso vive en `shared/application/`. No en `console/`, no en `ui/`.
2. Todo adaptador llama al caso de uso. El caso de uso nunca conoce al adaptador.
3. La validación de negocio ocurre en el caso de uso, no en el adaptador.
4. El adaptador solo se encarga de:
   - Obtener la entrada del usuario (texto o formulario)
   - Llamar al caso de uso
   - Mostrar el resultado
5. No puede existir lógica de dominio en el adaptador.

### Ejemplo concreto

```
console/                    ui/                     future-ai/
   │                          │                         │
   │ parser → QuoteCommand    │ QuoteCommand            │ QuoteCommand
   │                          │                         │
   └──────────┬───────────────┴──────────────┬──────────┘
              │                              │
              ▼                              ▼
    shared/application/prepareQuote()   shared/application/createQuote()
              │                              │
              ▼                              ▼
           api/ (POST)                  api/ (POST)
```

### Consecuencias

**Positivas:**
- Una sola fuente de verdad para cada caso de uso.
- Agregar un nuevo adaptador (AI, REST, CLI) requiere solo construir el input y llamar al caso de uso existente.
- Las pruebas del dominio se escriben contra `shared/application/`, no contra la UI ni la consola.
- La consola y el formulario son funcionalmente idénticos por construcción.

**Negativas:**
- El caso de uso debe diseñarse para ser agnóstico del adaptador, lo que requiere disciplina.
- Puede tentar a poner demasiada lógica en `shared/application/` (resistir: solo caso de uso, no infraestructura).

## Referencias

- ADR 0009: Spec-Driven Development
- ADR 0022: Adopción de Monaco Editor como consola operativa
- ADR 0023: Patrones seguros para comandos DSL en la consola operativa
- Spec 0027: Cotización — Consola y Formulario
- Hexagonal Architecture / Ports & Adapters (inspiración)
