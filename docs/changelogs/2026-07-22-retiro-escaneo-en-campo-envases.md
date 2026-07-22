# Changelog 2026-07-22 - Retiro visible de escaneo en campo desde Envases

## Qué se implementó

Se retiró del runtime visible de la ficha de `Envases` la acción `Escanear` / `Escaneo en campo`.

## Motivo

- en el estado actual del producto ya no conviene presentarlo como acción principal desde la ficha individual del envase;
- el flujo operativo normal debe apoyarse en rutas, carga y otros contextos más específicos.

## Alcance

- `plugins/logistics/frontend/cylinders/dialogs/DetailMenuDialog.tsx`
- `plugins/logistics/frontend/LogisticsPage.tsx`

## Nota

- este cambio retira la acción del runtime visible de `Envases`, pero no elimina todavía el backend ni el wiring interno por si se reaprovecha luego en otro flujo más adecuado.
