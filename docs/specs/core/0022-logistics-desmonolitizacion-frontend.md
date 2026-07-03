# SPEC 0022 — Logistics: Desmonolitizacion del frontend de envases

## Estado

Propuesta

## Contexto

`plugins/logistics/frontend/LogisticsPage.tsx` concentra hoy demasiadas responsabilidades del submodulo de envases en un solo archivo:

- listado principal;
- resumen por estado;
- filtros de busqueda;
- alta de envase;
- edicion de ficha;
- menu operativo;
- vistas de trazabilidad, PH, retimbrados, custodia, servicios, impresion y escaneo;
- estado local de multiples dialogs;
- queries y mutations del flujo.

La pagina ya reutiliza componentes base del core (`Dialog`, `DataTable`, `Select`, `Alert`, `Button`, buscadores compartidos), por lo que el problema principal no es duplicacion de UI base sino concentracion excesiva de flujos y estado en un solo componente.

Esto vuelve mas costoso:

1. revisar cambios;
2. extender nuevas features como `SPEC 0021`;
3. testear flujos de alta/edicion;
4. aislar regresiones;
5. mantener fronteras claras dentro del submodulo `envases`.

## Objetivo

Desmonolitizar el frontend de envases dentro del plugin `logistics` para que `LogisticsPage.tsx` quede como shell/orquestador, extrayendo dialogs, secciones, helpers y bloques visuales a archivos propios del mismo submodulo, sin crear plugins nuevos ni cambiar comportamiento funcional.

## No objetivos

- no crear un plugin nuevo;
- no separar `envases` de `logistics` como modulo de negocio independiente;
- no reescribir APIs backend;
- no cambiar reglas de negocio de `SPEC 0021` ni del state machine;
- no introducir Zustand, Context adicional o estado global nuevo solo para esta refactorizacion;
- no mover componentes de dominio a `shared/ui` salvo que realmente sean genericos;
- no rediseñar visualmente la pantalla;
- no simplificar aun el formulario de envase por alcance funcional; eso queda en specs propias.

## Alcance

### 1. `LogisticsPage.tsx` como shell

`LogisticsPage.tsx` debe quedar responsable solo de:

1. queries y mutations compartidas del workspace de envases;
2. seleccion del cilindro actual;
3. apertura/cierre de dialogs y secciones;
4. composicion de bloques principales de pantalla;
5. coordinacion de handlers de alto nivel.

No debe seguir creciendo como archivo dueño de todo el JSX de cada flujo.

### 2. Extraccion de dialogs

Se deben extraer como componentes propios, dentro del mismo submodulo frontend de envases:

1. `CreateCylinderDialog`
2. `EditCylinderDialog`
3. `CylinderDetailMenuDialog`
4. `CylinderViewSectionDialog`
5. `HydrotestDialog`
6. `WarrantyDialog`
7. `RetimbradoDialog`
8. `ServiceDialog`
9. `PrintLabelDialog`
10. `ScanDialog`

Cada dialog debe recibir props explicitas y no asumir ownership global de datos fuera de su flujo.

### 3. Extraccion de formulario y helpers

Se deben mover a archivos propios:

1. `CylinderFormFields`
2. tipos de estado del formulario
3. defaults vacios de formularios
4. helpers de conversion y payload (`toNullable`, `toNumberOrNull`, `buildCylinderPayload`, equivalentes)
5. helpers de formato (`formatDate`, `formatDateTime`, etc.)

La meta es que el comportamiento quede igual, pero la logica pura salga del archivo principal.

### 4. Extraccion de bloques visuales

Se deben extraer bloques visuales que hoy no necesitan vivir en el mismo archivo:

1. resumen de estados del envase;
2. filtros de busqueda;
3. tabla principal de envases;
4. card de datos generales del envase;
5. bloques de accion operativa;
6. bloques de vista.

### 5. Extraccion de secciones de vista

Las vistas especializadas deben quedar separadas por concern:

1. trazabilidad;
2. PH y garantias;
3. retimbrados;
4. custodia e impresion;
5. servicios y escaneos;
6. etiqueta operativa.

## Estructura objetivo sugerida

Sin volverlo un nuevo modulo, la organizacion objetivo puede seguir un arbol como este:

```text
plugins/logistics/frontend/
├── LogisticsPage.tsx
├── api.ts
├── CylinderStateBadge.tsx
├── cylinders/
│   ├── components/
│   │   ├── cylinder-general-card.tsx
│   │   ├── cylinder-search-filters.tsx
│   │   ├── cylinder-summary-cards.tsx
│   │   └── cylinder-table.tsx
│   ├── dialogs/
│   │   ├── create-cylinder-dialog.tsx
│   │   ├── edit-cylinder-dialog.tsx
│   │   ├── cylinder-detail-menu-dialog.tsx
│   │   ├── cylinder-view-section-dialog.tsx
│   │   ├── hydrotest-dialog.tsx
│   │   ├── warranty-dialog.tsx
│   │   ├── retimbrado-dialog.tsx
│   │   ├── service-dialog.tsx
│   │   ├── print-label-dialog.tsx
│   │   └── scan-dialog.tsx
│   ├── forms/
│   │   ├── cylinder-form-fields.tsx
│   │   ├── cylinder-form-state.ts
│   │   └── cylinder-payload.ts
│   ├── sections/
│   │   ├── cylinder-custody-section.tsx
│   │   ├── cylinder-label-section.tsx
│   │   ├── cylinder-ph-section.tsx
│   │   ├── cylinder-retimbrados-section.tsx
│   │   ├── cylinder-services-section.tsx
│   │   └── cylinder-trace-section.tsx
│   └── utils/
│       └── formatters.ts
```

La ruta exacta puede ajustarse, pero la idea base no debe perderse: separar por flujo y responsabilidad, no por inventar subdominios nuevos.

## Reglas de diseño

1. Mantener el ownership del flujo dentro de `plugins/logistics/frontend/`.
2. No mover a `shared/ui` componentes que sigan siendo 100% especificos de envases.
3. Solo promover a compartido si el componente deja de ser de dominio y se vuelve reusable de verdad.
4. Preferir props explicitas antes que estado global nuevo.
5. Mantener queries/mutations en el shell mientras no haya una razon fuerte para extraer hooks dedicados.
6. Si se extraen hooks, deben ser hooks del submodulo y no abstracciones genericas vacias.
7. La refactorizacion debe ser incremental; no big-bang.

## Plan de ejecucion sugerido

### Etapa 1 — Bajo riesgo

1. extraer `CylinderFormFields`;
2. extraer helpers puros y tipos de formulario;
3. extraer `CreateCylinderDialog`;
4. extraer `EditCylinderDialog`;
5. extraer `CylinderViewSectionDialog`.

### Etapa 2 — Mediano riesgo

1. extraer `CylinderTable`;
2. extraer `CylinderSearchFilters`;
3. extraer `CylinderSummaryCards`;
4. extraer `CylinderDetailMenuDialog`;
5. extraer `CylinderGeneralCard`.

### Etapa 3 — Limpieza final

1. extraer dialogs secundarios restantes;
2. ordenar imports y helpers;
3. reducir `LogisticsPage.tsx` a shell legible;
4. agregar pruebas frontend o snapshots segun riesgo.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| Romper wiring entre dialogs y estado local | medio | hacer extracciones mecanicas sin cambiar contratos primero |
| Introducir props drilling incomodo | bajo | aceptar props explicitas al inicio; optimizar despues si hace falta |
| Mezclar refactor con cambio funcional | alto | no tocar reglas de negocio en esta spec |
| Promover demasiado pronto componentes a shared/ui | medio | mantener primero todo dentro de `logistics/frontend/cylinders/` |
| Reescribir la pagina de una sola vez | alto | ejecutar por etapas y validar entre cada una |

## Permisos

No se crean permisos nuevos.

## Eventos

No se agregan eventos nuevos.

## Migraciones

No requiere migraciones de base de datos.

## Criterios de aceptacion

### Estructurales

1. `LogisticsPage.tsx` deja de contener el JSX completo de todos los dialogs principales.
2. El formulario de envase vive en archivo propio.
3. Las secciones de vista viven en componentes separados.
4. Los helpers de payload/formato salen del archivo principal.

### Funcionales

1. Alta, edicion, transiciones, PH, garantia, retimbrado, servicios, impresion y escaneo siguen funcionando igual.
2. `SPEC 0021` no se rompe durante la refactorizacion.
3. No cambian contratos API ni payloads por el solo hecho de desmonolitizar el frontend.

### De calidad

1. `ruff check` y `pyright` siguen verdes para el backend tocado si la refactorizacion se mezcla con wiring de datos.
2. `build:web` sigue pasando.
3. Las pruebas backend relevantes de `logistics` siguen pasando.

## Dependencias

- `docs/avances/logistics.md`
- `docs/specs/core/0021-cylinder-create-with-initial-movement.md`
- `plugins/logistics/frontend/LogisticsPage.tsx`
- `apps/web/src/shared/ui/`
