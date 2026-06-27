# ADR 0011 - Superficie Estable para Plugins In-Tree

## Estado

Aceptado

## Contexto

ADR 0002 establece que `plugins/` no debe depender de internals no publicos del core.

Sin embargo, el SDK backend actual aun no expone toda la superficie necesaria para que un plugin de negocio real opere de punta a punta:

- dependencias HTTP de auth/tenant;
- acceso a `Base` para modelos ORM;
- servicios de auditoria y emision de eventos transaccionales;
- componentes UI compartidos formalizados en `packages/ui`.

Bloquear la implementacion de `logistics` hasta expandir todo el SDK agregaria una fase intermedia que hoy no aporta valor de negocio.

## Decisión

Mientras `packages/sdk` y `packages/ui` maduran, los plugins in-tree del monorepo pueden consumir una superficie estable y acotada del core.

Se permite:

- backend de plugin importando infraestructura estable de `apps/api/app/`:
  - `core.database.Base`;
  - dependencias auth/tenant;
  - modelos core necesarios para foreign keys;
  - servicios de auditoria y eventos;
- frontend de plugin importando componentes compartidos de `apps/web/src/shared/ui/` cuando no exista aun equivalente publico en `packages/ui`.

No se permite:

- importar logica de negocio de otros modulos;
- modificar internals del core desde el plugin;
- acoplar el plugin a archivos privados cambiantes sin justificacion;
- crear una segunda jerarquia de componentes base duplicada dentro del plugin.

## Consecuencias

- `logistics` puede implementarse ahora sin rediseñar primero todo el SDK;
- el proyecto reconoce explicitamente una superficie temporal pero estable para plugins in-tree;
- cuando `packages/sdk` o `packages/ui` expongan reemplazos publicos suficientes, los plugins deberan migrar a esas APIs;
- esta excepcion aplica a plugins del monorepo y no implica un contrato estable para plugins externos de terceros.
