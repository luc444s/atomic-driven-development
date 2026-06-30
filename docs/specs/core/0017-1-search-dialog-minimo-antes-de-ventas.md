# SPEC 0017.1 — SearchDialog Minimo Antes de Ventas

## Estado

Propuesta

## Contexto

La `SPEC 0017` define un `SearchDialog<T>` generico para unificar los dialogos de busqueda reutilizables del frontend.

Sin embargo, la prioridad funcional inmediata del proyecto no es una limpieza amplia de frontend sino avanzar sobre nuevos modulos de negocio, en particular:

- ventas;
- compras;
- caja.

Si se empieza `ventas` sin un bloque generico minimo, el resultado mas probable es replicar por tercera o cuarta vez la misma deuda de UI:

- modal de busqueda;
- input con debounce;
- tabla de resultados;
- estados `loading`, `empty`, `error`;
- `onSelect`;
- cierre del dialogo al seleccionar.

Por otro lado, ejecutar toda la `SPEC 0017` como iniciativa amplia antes de tocar negocio retrasa innecesariamente la entrega funcional.

Esta spec reduce el alcance: construir solo la pieza minima necesaria para evitar nueva duplicacion antes de iniciar `ventas`.

## Objetivo

Implementar un `SearchDialog<T>` minimo, estable y reusable que cubra el patron actual de productos y clientes, para que `ventas` reutilice esa base desde el inicio sin seguir propagando deuda.

## No objetivos

- mover `shared/ui` a `packages/ui`;
- rediseñar el sistema de tablas;
- soportar filtros compuestos avanzados;
- agregar paginacion infinita;
- agregar cache global sofisticado;
- rehacer todos los buscadores del sistema;
- resolver de forma definitiva la deuda estructural `plugins -> apps/web`.

## Alcance

### Incluye

1. crear `apps/web/src/shared/ui/search-dialog.tsx`;
2. implementar contrato generico minimo basado en `ColumnDef<T>`;
3. encapsular debounce de `300ms`;
4. soportar carga inicial al abrir;
5. soportar estados `loading`, `empty`, `error`;
6. soportar seleccion de fila con `onSelect`;
7. migrar `ProductSearchDialog` a esta base;
8. migrar `CustomerSearchDialog` a esta base;
9. dejar el patron listo para `ventas`.

### No incluye

1. migrar todos los buscadores futuros por adelantado;
2. introducir un buscador de proveedores si el modulo `compras` aun no existe;
3. crear wrappers para dominios que todavia no tienen uso real;
4. agregar APIs backend nuevas si los endpoints actuales ya cubren la necesidad.

## Decisiones de implementacion

### 1. Alcance minimo deliberado

`SearchDialog<T>` debe resolver solo este flujo:

1. abrir dialogo;
2. escribir busqueda;
3. esperar debounce;
4. mostrar resultados en tabla;
5. seleccionar item;
6. devolver item al padre.

Todo comportamiento fuera de ese flujo queda fuera de esta spec.

### 2. Ubicacion

El componente vive en:

`apps/web/src/shared/ui/search-dialog.tsx`

Se acepta como compromiso temporal, consistente con ADR 0017.

### 3. Reutilizacion por wrappers delgados

`ProductSearchDialog` y `CustomerSearchDialog` no deben seguir conteniendo su propia logica de estado, debounce y tabla.

Si permanecen, solo pueden existir como wrappers delgados para inyectar:

- `title`;
- `placeholder`;
- `columns`;
- `fetchFn`;
- transformaciones minimas de tipos si fueran necesarias.

### 4. Sin abstraccion prematura extra

No se deben crear en esta spec:

- hooks genericos adicionales;
- factories de columnas;
- sistemas de filtros configurables;
- versiones inline y modal del mismo buscador.

## Contrato minimo

```typescript
interface SearchDialogProps<T> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  placeholder?: string;
  columns: ColumnDef<T>[];
  fetchFn: (query: string) => Promise<T[]>;
  onSelect: (item: T) => void;
  getRowId?: (item: T) => string;
  emptyMessage?: string;
}
```

## Comportamiento requerido

1. cuando `open` pasa a `true`, ejecuta `fetchFn("")`;
2. al cambiar el input, espera `300ms` antes de consultar;
3. si entra una nueva consulta, el estado visible solo debe reflejar la ultima respuesta vigente;
4. si la consulta falla, debe mostrarse `Alert` sin romper la pantalla padre;
5. al hacer clic en una fila, llama `onSelect(item)` y cierra el dialogo;
6. si no hay resultados, muestra un mensaje vacio claro.

## Integraciones objetivo inmediatas

### Productos

El buscador de productos debe quedar listo para:

- stock;
- productos;
- ventas futura.

### Clientes

El buscador de clientes debe quedar listo para:

- logistics;
- ventas futura;
- caja futura si requiere seleccion de cliente.

## Criterios de aceptacion

### Funcionales

1. stock puede seleccionar un producto usando la nueva base generica;
2. logistics puede seleccionar un cliente usando la nueva base generica;
3. el dialogo muestra loading, empty y error correctamente;
4. el debounce evita disparar una consulta por cada pulsacion inmediata;
5. al seleccionar una fila, el item correcto llega al componente padre.

### De deuda tecnica

1. no queda una tercera implementacion de buscador duplicado;
2. `ProductSearchDialog` y `CustomerSearchDialog`, si sobreviven, son wrappers delgados;
3. `ventas` puede reutilizar directamente `SearchDialog<T>` o uno de esos wrappers sin copiar la implementacion.

### De calidad

1. `tsc --noEmit` pasa;
2. `vitest` pasa en lo afectado;
3. no se introducen `any` nuevos en la API publica del componente;
4. no se introducen colores hardcodeados.

## Orden recomendado

1. implementar `SearchDialog<T>` minimo;
2. migrar producto;
3. migrar cliente;
4. validar con tests;
5. continuar con `SPEC` de `ventas`.

## Riesgos

| Riesgo | Impacto | Mitigacion |
|---|---|---|
| El componente se infla antes de tener 3 casos reales | complejidad innecesaria | mantener alcance minimo |
| Los wrappers siguen reteniendo demasiada logica | beneficio parcial | limitar wrappers a defaults de dominio |
| `ventas` requiere un caso no cubierto | ajuste puntual posterior | extender solo contra necesidad real |

## Dependencias

- ADR 0017 — SearchDialog generico en shared/ui;
- SPEC 0017 — SearchDialog Generico Compartido;
- `apps/web/src/shared/ui/data-table.tsx`;
- `apps/web/src/shared/ui/dialog.tsx`;
- `apps/web/src/shared/ui/input.tsx`;
- `apps/web/src/shared/ui/alert.tsx`.
