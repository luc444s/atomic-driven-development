# Changelog 2026-07-22 - Corrección de estado en Envases

## Qué se implementó

Se refinó el copy de la transición manual de estados en `Envases` para dejar explícito que es una acción excepcional y no el flujo operativo principal.

## Cambios

- `Transición operativa` pasa a mostrarse como `Corrección de estado`.
- el modal ahora advierte que debe usarse solo para regularización o corrección de datos.
- el selector pasa de `Selecciona estado destino` a `Selecciona estado corregido`.
- el CTA final pasa a `Aplicar corrección`.

## Archivos

- `plugins/logistics/frontend/cylinders/dialogs/TransitionDialog.tsx`
- `plugins/logistics/frontend/cylinders/dialogs/DetailMenuDialog.tsx`
