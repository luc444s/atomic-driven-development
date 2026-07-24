# ADR 0023 — Patrones seguros para comandos DSL en la consola operativa

## Estado

Aceptado

## Contexto

La consola operativa basada en Monaco Editor (ADR 0022) permite que los plugins registren lenguajes de dominio (DSL) para ejecutar operaciones rápidas. El primer DSL implementado fue el de cotización (`plugins/ventas/cotizacion`). Durante su implementación surgieron errores sistémicos causados por la falta de un contrato claro entre las capas que intervienen:

- **Frontend** (autocompletado + parser visual) y **backend** (parser de ejecución) interpretaban ligeramente distinto el mismo comando.
- Las comillas dobles (`""`) usadas para nombres con espacios no se normalizaban en ambos lados.
- El case-sensitivity no era uniforme: el autocompletado aceptaba minúsculas, pero el backend no reconocía `COTIZAR` en mayúsculas.
- Los comandos especiales (`--help`, `history`, `clear`) no tenían un lugar definido y llegaban accidentalmente al backend.

Estos problemas no son específicos de cotización: cualquier plugin futuro que agregue comandos a la consola los reproducirá si no hay un patrón establecido.

## Decisión

Se establecen **patrones obligatorios** para todo comando DSL que se agregue a la consola operativa, presentes o futuros.

### 1. Simetría estricta entre frontend y backend

Todo comando reconocido por el autocompletado/parser frontend debe ser interpretable de forma equivalente por el parser backend. No puede existir un comando que el frontend sugiera pero el backend rechace por diferencia de tokenización.

- Frontend: `plugins/<plugin>/frontend/dsl/parser.ts`
- Backend: `plugins/<plugin>/backend/services/<dominio>.py` (u equivalente)
- Regla: si se modifica uno, se modifica el otro.

### 2. Tokenización unificada

Ambos parsers deben compartir las mismas reglas de tokenización:

- Palabras separadas por espacios.
- Secuencias entre comillas dobles (`"..."`) son **un solo token**, aunque contengan espacios o keywords.
- Comillas como delimitadores, no como parte del valor.

Ejemplo:

```text
cotizar cliente "Gas del Norte" 400 "Bombona 10kg" mañana 14h
```

Debe producir:

```
["cotizar", "cliente", "Gas del Norte", "400", "Bombona 10kg", "mañana", "14h"]
```

### 3. Normalización de entidades

Cualquier valor que represente una entidad (cliente, producto, vehículo, dirección, etc.) debe ser normalizado:

- Quitar comillas iniciales y finales.
- No aplicar trim interno que altere el significado.
- No asumir que el usuario escribió comillas correctamente: si falta la comilla de cierre, el parser debe fallar o tomar el texto restante como valor crudo, pero nunca ejecutar con un valor truncado sin avisar.

Backend: función helper `_strip_quotes(value)` aplicada a todos los valores de entidad.

### 4. Case-insensitivity en el comando y keywords

El comando y sus keywords deben ser case-insensitive:

- Acciones: `cotizar`, `COTIZAR`, `Cotizar` son equivalentes.
- Keywords: `cliente`, `CLIENTE`, `vehiculo`, `VEHICULO`, `mañana`, `MAÑANA`.
- Patrones de hora: `14h`, `14H`, `14:00`, `14H00` deben reconocerse igual.

Excepción: los valores de entidad mismos (nombres de cliente, SKU, patentes) se buscan case-insensitivamente en la base de datos, pero se preservan tal cual al mostrarlos.

### 5. Autocompletado normalizado

El proveedor de autocompletado debe:

- Normalizar el query antes de enviarlo al backend (quitar comillas).
- Usar `filterText` en minúsculas para que Monaco muestre sugerencias independientemente de cómo escriba el usuario.
- Insertar entidades con espacios entre comillas (`"Gas del Norte" `).
- No enviar requests por cada tecla: debounce + `AbortController` + cache local.

### 6. Comandos especiales resueltos en frontend

Los comandos que no mutan estado ni requieren backend deben resolverse en el frontend:

| Comando | Responsable | Acción |
|---|---|---|
| `<comando> --help` | Frontend | Mostrar documentación del DSL |
| `history` | Frontend | Mostrar historial local de comandos |
| `clear` | Frontend | Limpiar salida de la terminal |

Nunca deben llegar al backend como comando a ejecutar.

### 7. Validación y ambigüedad en backend

El backend debe ser la última línea de validación:

- Rechazar si falta un campo obligatorio con mensaje descriptivo.
- Rechazar si una entidad no existe, ofreciendo sugerencias cuando sea posible.
- Rechazar si una entidad resuelve a múltiples matches (`AmbiguityError`); nunca adivinar.

### 8. Tests duales por comando

Cada nuevo comando o keyword debe tener:

- Tests de parser frontend (`parser.test.ts`).
- Tests de autocompletado frontend (`autocomplete.test.ts`).
- Tests de parser backend (`apps/api/tests/test_<plugin>_<dominio>_dsl.py` o equivalente).

Casos mínimos a cubrir:

- con y sin comillas;
- mayúsculas y minúsculas;
- nombres con espacios;
- campos opcionales omitidos;
- errores esperados (entidad inexistente, ambigüedad, campo faltante).

### 9. Documentación viva

Todo cambio en el DSL debe reflejarse en:

- `docs/specs/core/0026-cotizacion-consola-dsl-draft-first.md` (para cotización) o spec correspondiente.
- Texto de ayuda en terminal (`help.ts`).
- Opciones del autocompletado (`TOP_LEVEL_COMMANDS`).

## Invariantes

1. Frontend y backend nunca divergen en la interpretación de un comando.
2. Las comillas son delimitadores, nunca parte del valor de búsqueda.
3. Todo el DSL es case-insensitive en comandos y keywords.
4. Los comandos especiales (`--help`, `history`, `clear`) no llegan al backend.
5. El backend nunca ejecuta con entidades no resueltas.
6. Cada nuevo comando lleva tests de ambos lados.
7. La ayuda en terminal y la spec se actualizan junto con el código.

## Consecuencias

### Positivas

- Menor riesgo de errores de integración frontend/backend al agregar comandos.
- Experiencia predecible para el usuario: puede escribir en mayúsculas/minúsculas, con o sin comillas, y obtener el mismo resultado.
- Documentación y tests como parte obligatoria del ciclo de desarrollo.
- Reutilización del patrón en futuros plugins con consola (logística, agenda, etc.).

### Negativas

- Mayor costo inicial: cada comando requiere cambios coordinados en múltiples archivos.
- Duplicación aparente del parser (frontend en TypeScript, backend en Python). Esto es aceptado porque las capas tienen responsabilidades distintas y no comparten runtime.

### Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Olvidar actualizar backend al cambiar frontend | alto | Checklist de este ADR + code review |
| Inconsistencia en manejo de comillas | medio | Helper `_strip_quotes` y tokenizador compartido de reglas |
| Case-sensitivity inadvertida | medio | Comparar siempre con `.lower()` / `re.IGNORECASE` |
| Comandos especiales llegan al backend | medio | Resolverlos explícitamente en `CotizacionPage`/`ConsoleShell` |
| Falta de tests de regresión | alto | Tests duales obligatorios por comando |

## Referencias

- ADR 0022: Adopción de Monaco Editor como consola operativa
- Spec 0026: Cotización vía Consola DSL, Draft-First
- `plugins/ventas/cotizacion/frontend/dsl/parser.ts`
- `plugins/ventas/cotizacion/frontend/dsl/autocomplete.ts`
- `plugins/ventas/cotizacion/backend/services/cotizacion.py`
- `plugins/ventas/cotizacion/frontend/dsl/help.ts`
