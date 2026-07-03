# SPEC 0023AL — Combobox compartido en core frontend

## Estado

Propuesta

## Contexto

El frontend actual ya tiene dos piezas reutilizables relacionadas, pero ninguna cubre bien el caso intermedio:

- `Select` en `apps/web/src/shared/ui/select.tsx`
- `SearchDialog` en `apps/web/src/shared/ui/search-dialog.tsx`

Hoy:

- `Select` sirve para listas pequenas, cerradas y obvias;
- `SearchDialog` sirve para busqueda modal, remota y multi-columna.

Falta una pieza para el caso mas comun en formularios de negocio:

- seleccion inline;
- filtro textual rapido;
- experiencia mas ligera que un dialogo;
- mas util que un select plano cuando la lista ya no es tan pequena.

Si no se define esta pieza ahora, es muy probable que cada modulo empiece a construir su propia variante de:

- select con buscador;
- dropdown filtrable;
- pseudo-combobox local.

Eso haria que la IA y futuros agentes empiecen a improvisar soluciones distintas segun contexto.

Esta mini spec existe precisamente para evitar esa alucinacion estructural.

## Objetivo

Definir un `Combobox` compartido del core frontend para reutilizarlo en modulos como:

- clientes;
- productos;
- logistics;
- ventas futuras;
- formularios administrativos con listas medianas.

## No objetivos

- no reemplazar `SearchDialog`;
- no reemplazar `Select` en listas pequenas;
- no crear un selector remoto complejo con paginacion infinita;
- no mover aun `shared/ui` a `packages/ui`;
- no reescribir todos los formularios actuales de una vez.

## Decision funcional

La regla de uso queda asi:

1. `Select`
   - listas pequenas
   - catalogos cerrados
   - pocas opciones

2. `Combobox`
   - seleccion inline
   - filtro textual
   - listas medianas o suficientemente grandes para que un select plano ya moleste

3. `SearchDialog`
   - busqueda modal
   - datos remotos
   - datasets ricos o multi-columna
   - seleccion donde ya importa ver mas contexto antes de elegir

## Ubicacion

El componente debe vivir en:

`apps/web/src/shared/ui/combobox.tsx`

Motivo:

- es una pieza reusable del shell/frontend core;
- no es especifica de `crm` ni de `logistics`;
- evita duplicacion entre plugins.

## Alcance minimo

### Incluye

1. componente visual base reutilizable;
2. lista de opciones local por props;
3. input interno para filtrar opciones por texto;
4. seleccion por click;
5. mostrar opcion seleccionada;
6. estado vacio;
7. cierre al seleccionar o click fuera;
8. clases semanticas compatibles con tema claro/oscuro.

### No incluye en esta mini spec

1. fetch remoto integrado;
2. debounce remoto;
3. paginacion;
4. resaltado de coincidencias;
5. multiselect;
6. creatable options.

## Contrato minimo

```typescript
type ComboboxOption = {
  value: string;
  label: string;
  keywords?: string[];
};

type ComboboxProps = {
  value: string;
  onChange: (value: string) => void;
  options: ComboboxOption[];
  placeholder?: string;
  searchPlaceholder?: string;
  emptyMessage?: string;
  className?: string;
  required?: boolean;
  disabled?: boolean;
};
```

## Comportamiento requerido

1. muestra la opcion seleccionada o placeholder;
2. al abrir, permite escribir para filtrar;
3. filtra por `label` y por `keywords` si existen;
4. al seleccionar una opcion, llama `onChange(value)` y cierra;
5. si no hay coincidencias, muestra `emptyMessage`;
6. si se hace click fuera, cierra;
7. no debe usar colores hardcodeados.

## Comportamiento deseable

1. soporte basico de teclado:
   - abrir con Enter o click
   - cerrar con Escape
2. resetear filtro al cerrar

Si esto complica demasiado el primer corte, puede entrar en una iteracion posterior, pero la API no debe impedirlo.

## Integracion esperada

### CRM

Debe usarse donde hoy un `Select` ya se queda corto, pero un `CustomerSearchDialog` seria excesivo.

Ejemplos:

- seleccion de pais;
- seleccion de tipo de documento si el catalogo crece;
- seleccion de localidad o geografia acotada;
- seleccion de establecimiento cuando ya esta precargado en contexto.

### Logistics

Debe usarse en formularios con listas operativas medianas.

Ejemplos:

- zonas;
- rutas acotadas;
- vehiculos por sucursal;
- tipos de tarea.

### Productos / ventas futuras

Debe permitir una experiencia mejor para catalogos medianos locales, sin abrir dialogos pesados.

## Relacion con specs existentes

- complementa `SPEC 0017` y `SPEC 0017.1`
- no reemplaza `SearchDialog`
- es dependiente de `SPEC 0023D` y futuras sub-specs de clientes

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| convertirlo en un SearchDialog disfrazado | medio | limitarlo a lista local filtrable |
| dejarlo demasiado pobre y que vuelvan los pseudo-selects | alto | definir claramente cuando debe usarse |
| meter fetch remoto prematuro | medio | sacarlo de alcance |
| crear otra pieza duplicada por modulo | alto | ubicarlo en `shared/ui` y referenciar esta spec |

## Criterios de aceptacion

1. existe `Combobox` compartido en `apps/web/src/shared/ui/`;
2. resuelve el caso de seleccion inline filtrable;
3. no duplica `SearchDialog`;
4. no intenta resolver casos remotos complejos;
5. queda documentado cuando usar `Select`, `Combobox` y `SearchDialog`.

## Resultado esperado

Despues de esta mini spec, futuros agentes no deberian improvisar:

- ni un select con input ad hoc dentro de un modulo;
- ni un dialogo de busqueda para casos demasiado simples;
- ni una tercera familia de selector.

La convencion compartida debe quedar clara y estable.
