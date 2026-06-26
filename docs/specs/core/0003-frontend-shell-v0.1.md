# SPEC 0003 - Frontend Shell v0.1

## Estado

Aprobada

## Contexto

El backend ya dispone de un core usable con auth JWT, tenancy base, RBAC minimo, health checks, estado del sistema y runtime inicial de plugins.

Todavia falta un frontend shell oficial que permita iniciar sesion, navegar de forma protegida, consultar el estado del sistema y preparar la carga futura de plugins sin inventar modulos de negocio.

## Objetivo

Implementar `Frontend Shell v0.1` con:

- login funcional contra el backend actual;
- sesion persistida de forma simple;
- rutas protegidas para `/app/*`;
- layout principal con sidebar, header y usuario actual;
- dashboard base de sistema;
- navegacion preparada para plugins;
- pantalla inicial de runtime de plugins;
- documentacion de arranque y validacion.

## No objetivos

Queda fuera de alcance en esta iteracion:

- modulos de negocio reales;
- logistica funcional;
- migracion legacy;
- frontend de migrador;
- facturacion, inventario, clientes u otros modulos no implementados;
- reglas de permisos locales como autoridad final;
- administracion completa de plugins.

## Alcance

Toca:

- `apps/web`
- `docs/specs/core`
- `README.md`
- `package.json`

No deberia requerir cambios backend salvo un endpoint minimo coherente si la lectura de plugins no existiera.

## Reglas de negocio

- el frontend shell no implementa negocio, solo acceso y navegacion base;
- el backend sigue siendo la fuente de verdad para auth, permisos y estado del sistema;
- el frontend no debe depender de tablas internas ni reconstruir RBAC como autoridad;
- el token JWT se almacena de forma simple para esta fase inicial;
- al perder sesion o recibir `401`, el shell debe poder forzar reautenticacion;
- la navegacion de plugins debe quedar preparada para crecimiento modular sin inventar pantallas falsas.

## Permisos

Permisos implicados por backend existente:

- `core.auth.me`
- `core.plugin.read`

El frontend no crea permisos nuevos en esta iteracion.

## Eventos

No se agregan eventos nuevos del sistema en esta iteracion.

Se consume el flujo ya existente de login y lectura de plugins del core.

## Datos

Contratos y endpoints involucrados:

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/system/health`
- `GET /api/v1/system/ready`
- `GET /api/v1/system/plugins`
- `VITE_API_BASE_URL`

## Migraciones

No requiere migraciones de base de datos.

## Auditoria y observabilidad

Debe quedar trazable como minimo:

- login exitoso y fallido via backend existente;
- requests HTTP con `request_id` y `correlation_id` cuando el backend los emita;
- errores visibles de autenticacion y carga de sistema;
- estado de sesion del usuario en el shell sin exponer secretos.

## Riesgos

- sobrecargar el shell con modulos de negocio prematuros;
- acoplar el frontend a detalles internos del plugin runtime;
- duplicar validaciones de permisos que pertenecen al backend;
- dejar rutas sin proteccion o rehidratacion inconsistente de sesion;
- introducir tooling frontend fuera del stack aprobado.

## Criterios de aceptacion

- existe spec versionada para frontend shell;
- `apps/web` compila con Vite + TypeScript;
- `/login` permite iniciar sesion con credenciales demo validas;
- el token queda persistido de forma simple y la sesion puede rehidratarse;
- `/app/*` esta protegido por `RequireAuth`;
- el layout principal muestra sidebar, header, usuario actual y logout;
- `/app/system` consume `health` y `ready` y muestra el estado del sistema;
- `/app/plugins` muestra la lista de plugins desde backend si el endpoint existe;
- no se crean pantallas falsas de negocio;
- `pnpm build` pasa;
- `pyright`, `pytest` y `ruff check` del backend siguen pasando.

## Pruebas requeridas

- validacion manual de login correcto;
- validacion manual de login incorrecto;
- validacion manual de redireccion de rutas protegidas;
- validacion manual de logout;
- validacion manual de dashboard de sistema;
- validacion manual de pantalla de plugins;
- build frontend exitoso;
- pruebas backend existentes sin regresion.

## Notas para agentes

- no inventar modulos de negocio;
- mantener el frontend simple y extensible;
- usar el stack aprobado: React, Vite, TypeScript, React Router, TanStack Query, Zustand, Tailwind, pnpm;
- usar componentes de `shadcn/ui` sobre Tailwind; si un componente no existe en shadcn, construirlo con Tailwind utility classes;
- documentar variables de entorno y flujo demo de login.
