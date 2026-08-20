# A.SPEC API-REST-CON-0009 — Endpoint GET /api/productos/{id} (detalle + transporte)

## WHY
TMS necesita datos físicos de transporte por producto: peso y volumen (M3)
para planificar cargas y rutas.

## WHAT
`GET /api/productos/{id}` retorna el producto con campos de catálogo +
campos físicos de transporte: `m3, peso_kg, unidad_medida`.

## SCOPE
- Lectura de `Producto` por `cod_producto`.
- Exposición de `M3`, `ADR_PesoKg` (peso), `ADR_UnidadMedida` ya presentes
  en el legacy.

## OUT OF SCOPE
- **Campos `ADR_*` (clasificación regulatoria)**: ADR es norma europea;
  en Perú rige otro marco de mercancías peligrosas, por lo que los campos
  `ADR_*` son **candidatos a desaparecer en esta rama** y NO forman parte
  del contrato TMS.
- Stock operativo (derivar de `Movimiento`, NO de `Producto.stock`).
- Creación/enlace en OSS (A.SPEC 0010 → plugin `productos`).

## CONTRACT
- `200` con objeto; `404` si no existe.
- `m3`, `peso_kg` numéricos; `unidad_medida` texto.
- Campos `ADR_*` NO se exponen en esta rama (ver OUT OF SCOPE).
- Stock NO se sirve en este endpoint (o se marca explícitamente como no
  confiable).

## INVARIANTS
- Solo lectura.
- No expone `Producto.stock` como fuente de verdad.
- No expone `ADR_*` (fuera de alcance en Perú).

## VERIFICATION
- Producto conocido (ej. `cod_producto=1` OXIGENO 6M3) → `200` con `m3`,
  `peso_kg`, `unidad_medida`.
- El response NO incluye campos `ADR_*`.
- id inexistente → `404`.

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
  - logistics (cargas/rutas ADR)
must_not_affect:
  - escritura legacy
  - ERP app
```
