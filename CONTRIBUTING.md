# CONTRIBUTING.md

## Objetivo

Esta guia define como contribuir a SYSTUTOR OSS sin romper decisiones base del proyecto.

## Antes de programar

Leer primero:

- `AGENTS.md`
- `docs/adr/`

Si el cambio es una feature importante, tambien debe existir una spec antes de implementar.

## Reglas base

- no introducir logica de negocio en stored procedures o triggers;
- no acoplar modulos innecesariamente;
- no cambiar arquitectura base sin ADR;
- no mezclar cambios grandes sin justificacion;
- agregar pruebas cuando se introduce logica relevante;
- actualizar documentacion si cambia comportamiento.

## Flujo recomendado

```text
1. Crear o revisar spec
2. Revisar ADRs aplicables
3. Implementar en rama propia
4. Agregar pruebas
5. Validar calidad
6. Abrir PR
```

## Convencion de ramas

```text
main
develop
feature/nombre-corto
fix/nombre-corto
refactor/nombre-corto
docs/nombre-corto
```

## Convencion de commits

Usar mensajes claros y cortos:

```text
feat: agregar runtime base de plugins
fix: corregir validacion de tenant_id
refactor: separar repositorio de auditoria
docs: agregar ADR de migracion legacy
test: cubrir importacion CSV invalida
chore: preparar compose local
```

## Pull Requests

Todo PR debe explicar:

- que cambia;
- por que cambia;
- como se probo;
- que riesgos tiene;
- si toca permisos, eventos o migraciones.

## Calidad minima

Antes de merge, el cambio debe pasar al menos:

- lint;
- typing;
- pruebas relevantes al alcance del cambio.

## Regla final

Si un cambio parece rapido pero compromete modularidad, trazabilidad o migracion controlada, no debe entrar como atajo permanente.
