# A.SPEC API-REST-CON-0008 — Endpoint GET /api/productos

## WHY
TMS (y el plugin `productos` de OSS) necesita el catálogo de productos del
legacy. OSS ya posee productos; el API solo los expone.

## WHAT
`GET /api/productos` retorna array JSON de productos legacy (`Producto`,
4671 items) con campos canónicos: `id, nro, nombre, linea, unidad`.

## SCOPE
- Lectura de `Producto`.
- Serialización JSON.

## OUT OF SCOPE
- Stock (derivar de `Movimiento`, ver 0009).
- Detalle/ADR (A.SPEC 0009).
- Autenticación (A.SPEC 0004).

## CONTRACT
- `200 application/json` con array.
- item: `id` (cod_producto), `nro` (Nro_Producto), `nombre` (Desc_Producto),
  `linea` (Cod_Linea), `unidad` (Cod_Unidad).
- Si `nombre` falta → `"Sin asignar"`.

## INVARIANTS
- Solo lectura.
- NO incluye `Producto.stock` (cache no confiable, ver hallazgos legacy).
- No modifica `Producto`.

## VERIFICATION (TEST REAL, NO MOCK)
- Contra `ERP-SYSTUTOR.API` desplegada en Win10 apuntando a `Sys_Gas2_Plus`
  **real**, `GET /api/productos` retorna el array con los **4671 items**
  reales del legacy.
- Cada item con `id` y `nombre` presentes.
- Test nombre nulo → `"Sin asignar"`.
- Prohibido validar este contrato con mocks: el endpoint debe golpear la BD
  legacy real vía `ClsConexion`.

## ROLLBACK
- Quitar handler de la ruta.

## CHANGE SURFACE
```yaml
allowed:
  - ERP-SYSTUTOR.API/Program.vb
prohibited:
  - plugins/**
```

## BLAST RADIUS
```yaml
direct:
  - lectura Producto
indirect:
  - productos plugin (al consumirse)
must_not_affect:
  - escritura legacy
  - ERP app
```
