# ADR 0008 - Testing y Calidad

## Estado

Aceptado

## Contexto

SYSTUTOR OSS necesita disciplina técnica uniforme para sostener modularidad, migración progresiva y colaboración entre varios desarrolladores o agentes de IA.

Sin reglas comunes de calidad, el core, los plugins, migradores y herramientas internas se degradarán rápidamente.

El proyecto debe evitar que la velocidad inicial produzca deuda técnica difícil de corregir después.

## Decisión

Las herramientas oficiales de calidad serán:

* Ruff para lint y format;
* Pyright para typing;
* Pytest para testing backend.

## Reglas base

* Toda lógica nueva relevante debe incluir pruebas.
* El dominio debe cubrirse con pruebas unitarias.
* APIs y servicios críticos deben tener pruebas de integración.
* Migraciones legacy deben probar casos válidos y casos de rechazo.
* El frontend deberá evolucionar con pruebas según riesgo y criticidad del flujo.
* CI debe ejecutar validaciones automáticas antes de merge.
* Ningún PR relevante debe aprobarse si rompe lint, typing o pruebas obligatorias.
* No se debe reducir calidad para acelerar una entrega sin dejar deuda documentada.

## Calidad backend

El backend deberá validar:

```text
ruff check
ruff format --check
pyright
pytest
```

El código Python debe mantener:

* tipado claro;
* funciones pequeñas cuando sea razonable;
* servicios explícitos;
* errores controlados;
* lógica de dominio testeable;
* separación entre API, servicios, dominio e infraestructura.

## Testing backend

Se usarán pruebas en estos niveles:

### Unit tests

Para:

* entidades de dominio;
* reglas de negocio;
* validadores;
* mappers;
* servicios puros;
* permisos;
* eventos;
* helpers críticos.

### Integration tests

Para:

* APIs;
* base de datos;
* servicios que usan PostgreSQL;
* eventos persistentes;
* auditoría;
* jobs;
* plugins;
* migradores.

### Migration tests

Para:

* CSV válidos;
* CSV inválidos;
* manifest válido;
* manifest inválido;
* checksums incorrectos;
* columnas faltantes;
* duplicados;
* referencias inexistentes;
* registros rechazados;
* importaciones idempotentes.

## Cobertura mínima esperada

La primera etapa debe cubrir especialmente:

* dominio;
* permisos;
* auditoría;
* eventos;
* migrador;
* plugin runtime;
* flujos críticos del módulo piloto;
* validaciones de tenancy;
* errores esperados.

No se define inicialmente un porcentaje rígido de cobertura, porque puede generar pruebas superficiales. La prioridad será cubrir riesgo real.

## Frontend

El frontend deberá priorizar pruebas donde exista riesgo operativo.

Especialmente:

* formularios críticos;
* flujos de autorización;
* pantallas de migración;
* pantallas de logística;
* rutas protegidas;
* componentes reutilizables importantes.

La estrategia exacta de testing frontend podrá definirse en un ADR posterior si el proyecto lo requiere.

## CI/CD

El pipeline de CI deberá ejecutar como mínimo:

```text
ruff check
ruff format --check
pyright
pytest
frontend build
```

Cuando existan pruebas frontend, también deberán ejecutarse en CI.

El merge debe bloquearse si fallan validaciones obligatorias.

## Pull Requests

Todo PR relevante debe indicar:

* qué cambia;
* por qué cambia;
* cómo se probó;
* qué riesgos tiene;
* qué módulos toca;
* si modifica permisos;
* si emite eventos;
* si agrega migraciones;
* si afecta migración legacy;
* si actualiza documentación.

## Agentes de IA

Los agentes de IA deben respetar estas reglas:

* no eliminar pruebas para hacer pasar CI;
* no relajar typing sin justificación;
* no introducir dependencias de testing no aprobadas;
* no crear mocks que oculten errores reales;
* no modificar arquitectura para facilitar una prueba;
* crear pruebas junto con lógica nueva relevante;
* actualizar pruebas cuando cambie comportamiento esperado.

## Migraciones Alembic

Toda migración debe ser:

* pequeña;
* revisable;
* asociada a una feature o plugin;
* coherente con el modelo de tenancy;
* probada cuando afecte datos críticos.

No se permiten migraciones que mezclen múltiples dominios sin justificación.

## Datos de prueba

No se deben usar datos reales de clientes en pruebas.

Para fixtures se deben usar:

* datos falsos;
* datos anonimizados;
* muestras mínimas;
* casos representativos del legacy sin exponer información sensible.

## Consecuencias

* El scaffold del proyecto deberá incluir comandos estándar de calidad.
* Los PRs deberán fallar si rompen lint, typing o pruebas obligatorias.
* La velocidad inicial de desarrollo será algo menor, pero el costo de cambio será más controlable.
* El core y los plugins serán más seguros de modificar.
* El migrador legacy será más confiable y auditable.
* Los agentes de IA tendrán límites claros para generar código sin degradar la arquitectura.
