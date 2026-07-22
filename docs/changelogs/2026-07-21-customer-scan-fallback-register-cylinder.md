# Changelog 2026-07-21 - Fallback de registrar envase desde scanner

## Qué se implementó

Se agregó un fallback operativo al flujo de escaneo en `Envases`:

- si el scanner no encuentra el serial/barcode de la bombona;
- la UI ya no queda solo en error muerto;
- ahora ofrece la acción `Registrar envase`.

## Comportamiento

1. el usuario procesa el escaneo;
2. si el backend responde que el envase no existe, se habilita el CTA `Registrar envase`;
3. al pulsarlo, se abre el flujo de alta de envase que ya vive en `Envases`;
4. el alta se abre en modo compacto/minimal;
5. se precargan:
   - `serial`
   - `barcode`
   - `product_id` inferido cuando el sistema puede deducirlo desde el `movement_id` y sus items
   - `entry_mode`, `warehouse_id` y `customer_id/customer_name` cuando el movimiento permite inferirlos
6. tras guardar el envase, el sistema vuelve al flujo de escaneo para continuar la operación.

### Ajuste posterior de alta minima en ruta

- el alta minima desde `Seriales` ya no exige `content_kg` aunque use la rama `FULL_FROM_SUPPLIER`;
- en ese flujo se mantiene el alta operativa del envase y su estado inicial, pero se omite la validacion de kilos de contenido que corresponde al alta completa.

## Alcance actual

- reutiliza el endpoint existente de creación de envases;
- no crea un flujo paralelo fuera de `Envases`;
- no hace alta silenciosa automática;
- mantiene el fallback como intervención humana controlada.

## Archivos tocados

- `plugins/logistics/frontend/cylinders/dialogs/ScanDialog.tsx`
- `plugins/logistics/frontend/cylinders/dialogs/create-cylinder-dialog.tsx`
- `plugins/logistics/frontend/cylinders/hooks/use-cylinder-mutations.ts`
- `plugins/logistics/frontend/LogisticsPage.tsx`

## Notas

- el fallback es especialmente útil mientras el sistema aún se está poblando con bombonas reales en calle;
- si no se puede inferir el producto desde el movimiento, el alta sigue siendo mínima pero el usuario deberá completar luego la ficha desde `Envases`.
