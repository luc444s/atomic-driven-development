# Calendario de Planificación se veía deforme en carga inicial

**Fecha**: 2026-07-24
**Tags**: bugfix, frontend, font, layout

## Problema

Al iniciar el sistema por primera vez (cold start), el calendario de Planificación se mostraba deforme. Al refrescar la página se corregía.

## Causa

La fuente Geist Variable (`@fontsource-variable/geist`) usa `font-display: swap`. El navegador renderiza con la fuente de respaldo (~Roboto en Android) y luego intercambia a Geist cuando termina de descargar el `.woff2` (~29KB). El cambio de métricas de fuente causaba un layout shift visible en el grid CSS de 7 columnas del calendario mensual.

En cold start la descarga tarda y el shift es visible. Al refrescar, la fuente ya está cacheada y no hay shift.

## Solución

1. **`apps/web/src/index.css`** — `@font-face` con `font-display: optional` sobrescribe el `swap` de fontsource. El navegador usa la fuente de respaldo en la primera visita (sin shift) y Geist cacheada en visitas siguientes.

2. **`apps/web/src/shared/ui/resource-calendar/resource-calendar-month-view.tsx`** — `min-w-0 overflow-hidden` en celdas del grid mensual como protección contra overflow que deforme columnas.

## Archivos

| Archivo | Cambio |
|---|---|
| `apps/web/src/index.css` | +4 líneas, `@font-face` override |
| `apps/web/src/shared/ui/resource-calendar/resource-calendar-month-view.tsx` | +2 clases en className de celda |
