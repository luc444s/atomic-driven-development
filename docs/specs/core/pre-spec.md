aths:

PRE SPEC — Editor de Consola Operativa (Mónaco)
Estado

Borrador

Contexto

El sistema está evolucionando hacia un modelo donde la operación puede ejecutarse no solo mediante UI tradicional (formularios, modales), sino también mediante una consola de comandos tipados con autocompletado.

Para soportar esta interacción, se requiere un componente que:

permita entrada estructurada;
soporte autocompletado contextual;
habilite validación en tiempo real;
permita una experiencia tipo IDE (no tipo textarea simple).

El uso de una pseudo-terminal basada en inputs simples no es suficiente para cumplir estos objetivos.

Decisión

A partir de esta etapa:

Se adopta Monaco Editor como componente oficial para la entrada de comandos del sistema.
Rol dentro del sistema

Monaco no es un componente visual accesorio.

Se define como:

Un componente base del core para interacción estructurada del usuario con el sistema.
Naturaleza del componente

Monaco será utilizado como:

Editor estructurado para comandos del dominio

No como editor de código genérico.

Responsabilidad

El componente Monaco dentro del core será responsable de:

Entrada de comandos del usuario
Posicionamiento y control del cursor
Integración con autocompletado
Renderizado de tokens (keywords, entidades, valores)
Soporte para validación visual en tiempo real
No responsabilidades

Monaco no es responsable de lógica de negocio.

No debe:

ejecutar comandos;
validar reglas del dominio;
resolver entidades;
tomar decisiones operativas.
Relación con el sistema

Monaco se integra conceptualmente con:

Autocomplete Engine
Parser DSL
Command Handlers

Pero no contiene esa lógica.

Modelo de interacción

El flujo esperado es:

Usuario escribe en Monaco
→ sistema sugiere (autocomplete)
→ usuario completa comando
→ comando es interpretado fuera del editor
→ se ejecuta en backend
Experiencia de usuario

El editor debe:

priorizar velocidad de escritura;
minimizar fricción cognitiva;
guiar mediante autocompletado;
evitar ambigüedad mediante sugerencias controladas.
Estilo visual

Aunque puede adoptar estética de terminal (oscuro, fuente monoespaciada), se define que:

La apariencia no define el comportamiento.

La experiencia debe sentirse como:

un IDE simplificado para operar el negocio

No como una terminal real del sistema operativo.

Invariantes
Monaco es la base para interacción avanzada del usuario.
No se permite usar inputs simples para flujos que requieran autocompletado estructurado.
Toda lógica de negocio permanece fuera del editor.
El editor nunca ejecuta directamente acciones del sistema.
La experiencia debe ser guiada, no libre.

Motivación
Se prioriza control, velocidad y precisión en la entrada de datos operativos,
evitando la complejidad y limitaciones de inputs tradicionales.
Riesgos
usar Monaco como editor genérico en lugar de consola guiada;
introducir lógica de negocio dentro del editor;
sobrecargar la UI con comportamiento innecesario;
perder enfoque en velocidad por exceso de features.
Resultado esperado
Un punto único de entrada estructurada para operaciones rápidas,
capaz de escalar hacia una consola completa del sistema.
🧠 Cierre

Esta versión ya está bien alineada con tu filosofía:
