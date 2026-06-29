# Vistas SQL Completas — Módulo Stock/Inventario

---

Para extraer las vistas completas, ejecutar en BD:

```sql
-- Vista: CRstockCySMilton
SELECT OBJECT_DEFINITION(OBJECT_ID('CRstockCySMilton'));

-- Vista: kardex_final
SELECT OBJECT_DEFINITION(OBJECT_ID('kardex_final'));

-- Vista: kardex_final1
SELECT OBJECT_DEFINITION(OBJECT_ID('kardex_final1'));

-- Vista: vkardex
SELECT OBJECT_DEFINITION(OBJECT_ID('vkardex'));
```

**Nota:** Las vistas no se incluyen inline porque pueden ser extensas. La extracción debe hacerse directamente desde la BD.

---

## Propósito de cada vista

| Vista | Descripción estimada |
|-------|---------------------|
| `CRstockCySMilton` | Vista para reporte Crystal "Stock por Almacén" (usada por CRalmacengen*) |
| `kardex_final` | Vista resumen del kardex con joins a Producto (si aplica) |
| `kardex_final1` | Variante de kardex_final con diferentes filtros |
| `vkardex` | Vista general del kardex |
