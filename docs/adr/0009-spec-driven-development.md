# ADR 0009 - Spec Driven Development

## Estado

Aceptado

## Contexto

SYSTUTOR OSS se construirá con participación de varios programadores y agentes de IA.

Para evitar cambios grandes guiados solo por intuición, contexto implícito o decisiones no documentadas, se necesita una disciplina previa a la implementación.

El proyecto debe proteger:

* arquitectura;
* modularidad;
* trazabilidad;
* migración controlada;
* coherencia entre core y plugins;
* colaboración entre humanos e IA.

Sin specs, cada programador o agente podría interpretar el proyecto de forma distinta.

## Decisión

Toda característica importante deberá empezar con una spec escrita y versionada antes de implementarse.

La spec será el contrato funcional y técnico mínimo de una feature.

## Flujo oficial

```text
idea
-> spec
-> revisión
-> diseño técnico
-> contrato API/datos
-> implementación
-> pruebas
-> PR
-> merge
```

## Reglas base

* No se implementan features importantes sin spec.
* Cambios arquitectónicos relevantes requieren ADR.
* Los agentes deben leer la spec antes de tocar código.
* Toda feature debe declarar alcance, riesgos, permisos, eventos y criterios de aceptación.
* La documentación se actualiza junto con el cambio cuando el comportamiento cambia.
* La spec debe indicar qué módulos, plugins o herramientas serán afectados.
* La spec debe indicar si el cambio afecta migración legacy.
* La spec debe indicar si se requieren migraciones de base de datos.
* La spec debe indicar si se agregan eventos o permisos nuevos.

## Cuándo una spec es obligatoria

Una spec será obligatoria cuando el cambio:

* agregue una feature nueva;
* modifique comportamiento de negocio;
* cree o modifique APIs;
* cree o modifique eventos;
* agregue permisos;
* afecte tenancy;
* afecte auditoría;
* modifique migraciones legacy;
* agregue un plugin;
* cambie estructura del frontend;
* introduzca jobs async;
* afecte datos persistidos;
* altere contratos compartidos.

Cambios menores como typos, ajustes visuales pequeños o refactors internos simples podrán no requerir spec, siempre que no cambien comportamiento.

## Diferencia entre Spec, ADR y PR

### Spec

Define qué se va a construir y cómo debe comportarse.

Responde:

* qué problema resuelve;
* qué alcance tiene;
* qué datos usa;
* qué permisos requiere;
* qué eventos emite;
* cómo se acepta como terminado.

### ADR

Define una decisión arquitectónica duradera.

Responde:

* qué decisión se tomó;
* por qué se tomó;
* qué alternativas se descartaron;
* qué consecuencias tiene.

### PR

Implementa un cambio concreto.

Responde:

* qué archivos cambian;
* cómo se probó;
* qué riesgos tiene;
* qué evidencia existe de que funciona.

## Ubicación

Las specs deberán vivir en:

```text
docs/specs/
```

Para specs por módulo o plugin, se recomienda:

```text
docs/specs/core/
docs/specs/plugins/logistics/
docs/specs/tools/migrator/
docs/specs/tools/legacy-analyzer/
```

Ejemplo:

```text
docs/specs/plugins/logistics/0001-logistics-pilot.md
```

## Estructura mínima de una spec

Cada spec importante deberá incluir:

```md
# SPEC XXXX - Nombre de la feature

## Estado

Borrador | En revisión | Aprobada | Implementada | Obsoleta

## Contexto

Explicación del problema o necesidad.

## Objetivo

Qué se busca lograr.

## No objetivos

Qué queda explícitamente fuera.

## Alcance

Qué módulos, plugins, APIs o pantallas toca.

## Reglas de negocio

Reglas funcionales conocidas.

## Permisos

Permisos requeridos o nuevos permisos a crear.

## Eventos

Eventos emitidos o consumidos.

## Datos

Tablas, entidades, contratos, CSVs o payloads involucrados.

## Migraciones

Si requiere o no migración de base de datos.

## Auditoría y observabilidad

Qué debe quedar registrado.

## Riesgos

Riesgos técnicos, operativos o de migración.

## Criterios de aceptación

Condiciones verificables para considerar terminada la feature.

## Pruebas requeridas

Unitarias, integración, migrador, frontend o manuales.

## Notas para agentes

Instrucciones específicas para IA o colaboradores.
```

## Criterios de aceptación

Toda spec debe tener criterios de aceptación claros.

Ejemplo:

```text
- Un usuario con permiso logistics.delivery.create puede crear una entrega.
- Un usuario sin permiso recibe 403.
- La acción genera auditoría.
- La acción emite logistics.delivery.created.
- La entrega queda asociada al tenant correcto.
- Las pruebas unitarias e integración pasan.
```

No se debe aceptar una spec con criterios ambiguos como:

```text
- debe funcionar correctamente
- debe verse bien
- debe ser rápido
```

sin definir cómo se verifica.

## Reglas para agentes de IA

Todo agente debe:

* leer `AGENTS.md`;
* leer los ADRs relacionados;
* leer la spec antes de implementar;
* respetar el alcance;
* no inventar requisitos;
* no ampliar la feature sin autorización;
* no cambiar contratos sin actualizar spec;
* no modificar arquitectura sin ADR;
* crear pruebas acordes al riesgo;
* actualizar documentación si cambia comportamiento.

Si una instrucción contradice la spec, el agente debe detenerse y pedir resolución o proponer actualización explícita.

## Contratos antes que implementación

Antes de implementar APIs, eventos, migradores o plugins, debe existir contrato explícito.

Ejemplos:

* contrato de API;
* contrato de evento;
* contrato de CSV;
* contrato de plugin;
* contrato de permisos;
* contrato de migración.

La implementación debe seguir el contrato, no inventarlo durante el desarrollo.

## Relación con migración legacy

Cuando una feature toque datos provenientes de SYSTUTOR Legacy, la spec debe indicar:

* dominio afectado;
* origen de datos;
* si requiere CSV + manifest;
* si usa `legacy_id`;
* reglas de validación;
* reglas de rechazo;
* riesgos conocidos;
* si afecta ownership del dominio.

No se deben convertir suposiciones sobre legacy en reglas definitivas sin evidencia.

## Consecuencias

* El core y los módulos crecerán con mayor trazabilidad.
* La colaboración con IA será más segura porque habrá contexto explícito.
* El costo inicial de documentación sube, pero baja la ambigüedad operativa y técnica.
* Las features importantes serán más fáciles de revisar, probar y mantener.
* Los PRs tendrán una base clara para validación.
* La arquitectura será menos vulnerable a cambios improvisados.
