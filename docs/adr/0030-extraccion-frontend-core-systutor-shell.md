# ADR 0030 — Extracción del frontend core a `systutor-shell` (repo público MIT)

## Estado

Aceptado — 2026-08-16

## Contexto

`apps/web/src/shared/` concentraba el frontend core del sistema: componentes UI genéricos (`ui/`), la consola operativa (ADR 0022, 0023), el cliente HTTP (`api/client.ts`) y helpers (`confirm`, `neofetch`).

El patrón de consumo era frágil: los plugins y features importaban desde `apps/web/src/shared/` por rutas relativas o el alias `@/shared/*`, mezclando en la misma carpeta componentes genéricos con lógica acoplada al app (`layout/` depende de `features/auth`, `features/plugins/runtime`, `features/shell/navigation`).

ADR 0029 estableció el patrón multirepo: kernel público MIT en `systutor-core`, montado como submodule en `vendor/` y consumido con alias del bundler. El frontend core merece el mismo tratamiento: es infraestructura reutilizable sin lógica de negocio, y su separación permite versionarlo, publicarlo y consumirlo de forma independiente.

## Decision

Extraer el frontend core a un repo público MIT: `github.com/luc444s/systutor-shell`, montado como submodule en `vendor/systutor-shell/` y consumido via alias `@systutor/shell/*`.

### Qué se mueve

- `shared/ui/*` completo: componentes genéricos, mapas (Leaflet), resource-calendar, consola operativa.
- `shared/api/client.ts`: cliente HTTP desacoplado del auth del app via `setTokenProvider()` (registrado por el app en `features/auth/store.ts`).
- `shared/confirm.ts`, `shared/neofetch.ts` + tests.

### Qué se queda en el app

- `shared/layout/*`: depende de `features/auth`, `features/plugins/runtime`, `features/shell/navigation` (logica del app).
- `shared/layout/theme-toggle.tsx`: acoplado a `features/theme/store`.
- Reglas de negocio, payload builders y wrappers de dominio: en los plugins.

### Mecanismo de consumo

- `vite.config.ts`: alias `@systutor/shell` → `vendor/systutor-shell/src`.
- `tsconfig.json`: `paths` para `@systutor/shell/*`.
- Resolucion de tipos: los archivos del shell resuelven `react`/`react-dom` desde `node_modules` de la raiz del workspace (React 19), mientras el app usa React 18 → `paths` desnudos en `tsconfig.json` fijan `react`, `react-dom`, `react/jsx-runtime`, `clsx`, `tailwind-merge`, `lucide-react`, `@tanstack/react-query`, `sonner` a `apps/web/node_modules`.
- Alias con query para el worker de pdf.js: `pdfjs-dist/build/pdf.worker.min.js?url`.

### Regla de gobernanza

Todo componente nuevo generico va al shell (mismo criterio que el Core externo). El shell no acepta lógica de negocio ni acoplamiento a features del app.

## Consecuencias

**Positivas**

- Frontend core versionable y consumible independiente, espejo del patron de ADR 0029.
- Separacion explicita generico/negocio; los plugins ya no dependen de rutas del app.
- `api/client.ts` deja de importar el store del app (inversion de dependencia via `setTokenProvider`).

**Negativas**

- Cambios al shell requieren commit del submodule + pin nuevo en este repo (igual que `systutor-core`).
- `tsconfig.json` acumula `paths` desnudos como workaround de resolucion de tipos en workspace pnpm.

## Alternativas rechazadas

- npm workspaces: `packages/` es Python y los plugins viven dentro del repo; submodule encaja con el patron existente.
- Mantener `shared/` en el app: perpetua la mezcla generico/negocio y bloquea publicacion independiente.
